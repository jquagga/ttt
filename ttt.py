#!/usr/bin/env python

import json
import os
import time
from datetime import datetime
from pathlib import Path

import apprise
import requests
import scrubadub
import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline


def transcribe_call(destinations):
    """Transcribes audio files and sends notifications.

    Args:
        destinations (dict): A dictionary containing destination information.

    Returns:
        None

    Explanation:
        This function searches for JSON files in the "media/transcribe" directory, sorts them by creation time,
        and transcribes the corresponding audio files. The transcription is performed using different methods
        based on the environment variables set. After transcribing, the function sends notifications using the
        transcribed text. Finally, the JSON and audio files are deleted.

    """
    # First lets search the media directory for all json, sorted by creation time
    jsonlist = sorted(
        Path("media/transcribe").rglob("*.[jJ][sS][oO][nN]"), key=os.path.getctime
    )

    # If the queue is empty, pause for 5 seconds and then restart polling
    if not jsonlist:
        print("Empty queue. Sleep 5 seconds and check again.")
        time.sleep(5)
        return ()

    for jsonfile in jsonlist:
        # Ok, let's grab the first json and pull it out and then the matching wav file
        audiofile = Path(jsonfile).with_suffix(".wav")

        print(f"Processing: {audiofile}")

        # Now load the actual json data into calljson
        calljson = jsonfile.read_text()
        calljson = json.loads(calljson)

        # Send the json and audiofile to a function to transcribe
        # If TTT_DEEPGRAM_KEY is set, use deepgram, else
        # if TTT_WHISPER_URL is set, use whisper.cpp else
        # fasterwhisper
        if os.environ.get("TTT_DEEPGRAM_KEY", False):
            calljson = transcribe_deepgram(calljson, audiofile)
        elif os.environ.get("TTT_WHISPERCPP_URL", False):
            calljson = transcribe_whispercpp(calljson, audiofile)
        else:
            calljson = transcribe_transformers(calljson, audiofile)

        # Ok, we have text back, send for notification
        send_notifications(calljson, destinations)

        # And now delete the files from the transcribe directory
        Path.unlink(jsonfile)
        Path.unlink(audiofile)


def transcribe_whispercpp(calljson, audiofile):
    """Transcribes audio file using whisper.cpp.

    Args:
        calljson (dict): A dictionary containing the JSON data.
        audiofile (Path): The path to the audio file.

    Returns:
        dict: The updated calljson dictionary with the transcript.

    Explanation:
        This function sends the audio file to whisper.cpp for transcription. It constructs a multipart/form-data
        request with the audio file and other parameters. The response from whisper.cpp is parsed as JSON and
        merged into the calljson dictionary. The updated calljson dictionary is then returned.
    """
    whisper_url = os.environ.get("TTT_WHISPERCPP_URL", "http://whisper:8080")

    # Now send the files over to whisper for transcribing
    files = {
        "file": (None, audiofile.read_bytes()),
        "temperature": (None, "0.0"),
        "temperature_inc": (None, "0.2"),
        "response_format": (None, "json"),
    }

    try:
        response = requests.post(f"{whisper_url}/inference", files=files)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"A request error occurred while trying to post to whisper.cpp: {e}")
        raise RuntimeError(
            "A request error occurred while trying to post to whisper.cpp."
        ) from e

    calltext = response.json()

    # And now merge that dict into calljson so [text] in calljson is the transcript
    calljson = {**calljson, **calltext}
    return calljson


def transcribe_transformers(calljson, audiofile):
    """Transcribes audio file using transformers library.

    Args:
        calljson (dict): A dictionary containing the JSON data.
        audiofile (str): The path to the audio file.

    Returns:
        dict: The updated calljson dictionary with the transcript.

    Explanation:
        This function transcribes the audio file using the transformers library. It loads a pre-trained model
        and processor, creates a pipeline for automatic speech recognition, and processes the audio file.
        The resulting transcript is added to the calljson dictionary and returned.
    """
    audiofile = str(audiofile)

    device = "cuda:0"
    torch_dtype = torch.float16

    model_id = "distil-whisper/distil-large-v3"

    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        model_id,
        torch_dtype=torch_dtype,
        low_cpu_mem_usage=True,
        use_safetensors=True,
    )
    model.to(device)

    processor = AutoProcessor.from_pretrained(model_id)

    pipe = pipeline(
        "automatic-speech-recognition",
        model=model,
        tokenizer=processor.tokenizer,
        feature_extractor=processor.feature_extractor,
        max_new_tokens=128,
        torch_dtype=torch_dtype,
        device=device,
    )

    result = pipe(audiofile)
    calljson["text"] = result["text"]
    return calljson


def transcribe_deepgram(calljson, audiofile):
    """Transcribes audio file using Deepgram API.

    Args:
        calljson (dict): A dictionary containing the JSON data.
        audiofile (Path): The path to the audio file.

    Returns:
        dict: The updated calljson dictionary with the transcript.

    Explanation:
        This function sends the audio file to the Deepgram API for transcription. It constructs a POST request
        with the audio file and necessary headers. The response from Deepgram is parsed as JSON, and the
        transcript is extracted and added to the calljson dictionary. The updated calljson dictionary is then
        returned.
    """
    deepgram_key = os.environ.get("TTT_DEEPGRAM_KEY")
    headers = {
        "Authorization": f"Token {deepgram_key}",
        "Content-Type": "audio/wav",
    }
    params = {
        "model": "nova-2-phonecall",
        "language": "en-US",
        "smart_format": "true",
    }

    data = audiofile.read_bytes()
    try:
        response = requests.post(
            "https://api.deepgram.com/v1/listen",
            params=params,
            headers=headers,
            data=data,
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"A request error occurred while trying to post to Deepgram: {e}")
        raise RuntimeError(
            "A request error occurred while trying to post to Deepgram."
        ) from e

    json = response.json()

    # We take the json returned from deepgram and pull out the "transcript"
    # then tack it onto the calljson dict as "text" which is what whisper
    # normally uses
    calltext = json["results"]["channels"][0]["alternatives"][0]["transcript"]
    calljson["text"] = calltext
    return calljson


def send_notifications(calljson, destinations):
    """Sends notifications with transcribed text.

    Args:
        calljson (dict): A dictionary containing the call information.
        destinations (dict): A dictionary containing destination URLs.

    Returns:
        None

    Explanation:
        This function cleans the transcribed text using the scrubadub library to remove personally identifiable
        information (PII). It constructs a notification title based on the call information and sends the cleaned
        text as the notification body. The notification is sent to the specified destination URLs using the
        apprise library.
    """
    # Scrubadub redacts PII let's try and clean the text before
    # goes out the door
    scrubber = scrubadub.Scrubber()
    scrubber.remove_detector("email")
    body = scrubber.clean(calljson["text"])
    title = (
        calljson["talkgroup_description"]
        + " @ "
        + str(datetime.fromtimestamp(calljson["start_time"]))
    )

    short_name = str(calljson["short_name"])
    talkgroup = str(calljson["talkgroup"])
    notify_url = destinations[short_name][talkgroup]

    apobj = apprise.Apprise()
    apobj.add(notify_url)
    apobj.notify(
        body=body,
        title=title,
    )


def import_notification_destinations():
    """Imports notification destinations from a CSV file.

    Returns:
        dict: A dictionary containing the notification destinations.

    Explanation:
        This function reads a CSV file containing notification destinations. Each row in the CSV file represents
        a destination, with the first column as the key, the second column as the sub-key, and the third column
        as the value. The function constructs a dictionary where the keys are the values from the first column,
        and the values are nested dictionaries with the sub-keys and values from the second and third columns,
        respectively. The resulting dictionary is returned.
    """
    import csv

    destinations = {}
    with open("destinations.csv", newline="") as inp:
        reader = csv.reader(inp)
        next(reader, None)  # skip the headers
        for row in reader:
            if row[0] in destinations:
                destinations[row[0]][row[1]] = row[2]
            else:
                destinations[row[0]] = {row[1]: row[2]}

    return destinations


def main():
    """Main entry point of the application.

    Returns:
        None

    Explanation:
        This function serves as the main loop of the application. It imports notification destinations using
        the `import_notification_destinations` function and continuously calls the `transcribe_call` function
        with the imported destinations. The loop runs indefinitely until the program is terminated.
    """
    # Import the apprise destinations to send calls
    destinations = import_notification_destinations()

    while 1:
        transcribe_call(destinations)


if __name__ == "__main__":
    main()
