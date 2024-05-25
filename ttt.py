#!/usr/bin/env python

import json
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path

import apprise
import requests
import torch
from better_profanity import profanity
from transformers import (
    AutoModelForCausalLM,
    AutoModelForSpeechSeq2Seq,
    AutoProcessor,
    pipeline,
)

# Let's increase our nice value by 5.  We're important but let's not
# impact system functionality overall.
os.nice(5)

# Before we dig in, let's globally set up transformers
# We will load up the model, etc now so we only need to
# use the PIPE constant in the function.

# If we set TTT_TRANSFORMERS_MODEL_ID, let's use that directly
if os.environ.get("TTT_TRANSFORMERS_MODEL_ID", False):
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
    model_id = os.environ.get("TTT_TRANSFORMERS_MODEL_ID", "openai/whisper-large-v3")
    print(f"We are using {torch_dtype} on {device} with {model_id}")
    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        model_id,
        torch_dtype=torch_dtype,
        low_cpu_mem_usage=True,
        use_safetensors=True,
    )
    model.to(device)
    processor = AutoProcessor.from_pretrained(model_id)
    PIPE = pipeline(
        "automatic-speech-recognition",
        model=model,
        tokenizer=processor.tokenizer,
        feature_extractor=processor.feature_extractor,
        max_new_tokens=128,
        torch_dtype=torch_dtype,
        device=device,
    )
# If we don't set a model, let's use the combo of best / fastest.
# Speculative decoding with large-v3 / distil-v3
else:
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
    assistant_model_id = "distil-whisper/distil-large-v3"
    assistant_model = AutoModelForCausalLM.from_pretrained(
        assistant_model_id,
        torch_dtype=torch_dtype,
        low_cpu_mem_usage=True,
        use_safetensors=True,
    )
    assistant_model.to(device)
    model_id = "openai/whisper-large-v3"
    print(
        f"We are using {torch_dtype} on {device} with {model_id} assisted by {assistant_model_id}"
    )
    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        model_id, torch_dtype=torch_dtype, low_cpu_mem_usage=True, use_safetensors=True
    )
    model.to(device)
    processor = AutoProcessor.from_pretrained(model_id)
    PIPE = pipeline(
        "automatic-speech-recognition",
        model=model,
        tokenizer=processor.tokenizer,
        feature_extractor=processor.feature_extractor,
        max_new_tokens=128,
        generate_kwargs={"assistant_model": assistant_model, "language": "english"},
        torch_dtype=torch_dtype,
        device=device,
    )

# If an ambulance is coming for you stroke is still a bad word,
# we don't want to censor it in this case.
profanity.load_censor_words(whitelist_words=["stroke"])


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

    # Set the return argument to english
    # result = PIPE(audiofile, generate_kwargs={"language": "english"})
    result = PIPE(audiofile)
    calljson["text"] = result["text"]
    return calljson


def send_notifications(calljson, audiofile, destinations):
    """
    Sends notifications using the provided calljson, audiofile, and destinations.

    Args:
        calljson (dict): The JSON object containing call information.
        audiofile (str): The path to the audio file.
        destinations (dict): A dictionary mapping short names and talkgroups to notification URLs.

    Raises:
        None

    Returns:
        None

    Examples:
        send_notifications(calljson, audiofile, destinations)
    """

    # Run ai text through profanity filter
    body = profanity.censor(calljson["text"])
    title = (
        calljson["talkgroup_description"]
        + " @ "
        + str(datetime.fromtimestamp(calljson["start_time"]))
    )
    short_name = str(calljson["short_name"])
    talkgroup = str(calljson["talkgroup"])
    notify_url = destinations[short_name][talkgroup]

    # If TTT_ATTACH_AUDIO is set to True, attach it to apprise notification
    attach_audio = os.environ.get("TTT_ATTACH_AUDIO", "False").lower() in (
        "true",
        "1",
        "t",
    )
    apobj = apprise.Apprise()
    apobj.add(notify_url)
    if attach_audio:
        audio_notification(audiofile, apobj, body, title)
    else:
        apobj.notify(
            body=body,
            title=title,
        )


def audio_notification(audiofile, apobj, body, title):
    """
    Encode audio file to AAC format and send a notification with the audio attachment.

    Args:
        audiofile (str): Path to the input audio file.
        apobj: Object used to send notifications.
        body (str): Body of the notification.
        title (str): Title of the notification.

    Returns:
        None

    Raises:
        subprocess.CalledProcessError: If ffmpeg encoding fails.
        subprocess.TimeoutExpired: If ffmpeg encoding exceeds 30 seconds.
    """
    # Try and except to handle ffmpeg encoding failures
    # If it fails, just upload the text and skip the audio attachment
    try:
        aacfile = Path(audiofile).with_suffix(".m4a")
        ffmpeg_cmd = [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            audiofile,
            "-ac",
            "1",
            "-af",
            "highpass=f=200,lowpass=f=3000,anlmdn,loudnorm=i=-14",
            "-b:a",
            "64k",
            "-c:a",
            "aac",
            aacfile,
        ]
        subprocess.run(ffmpeg_cmd, check=True, timeout=30)

        aacfile = str(aacfile)
        apobj.notify(
            body=body,
            title=title,
            attach=aacfile,
        )
        # Remove aacfile; audiofile and json unlinked later
        try:
            Path(aacfile).unlink()
        except FileNotFoundError:
            print(f"File {aacfile} not found.")
        except PermissionError:
            print(f"No permission to delete {aacfile}.")
    except subprocess.CalledProcessError:
        print(
            f"ffmpeg file conversion error with {aacfile}. We will skip audio on this file and post text only."
        )
        apobj.notify(
            body=body,
            title=title,
        )
        try:
            Path(aacfile).unlink()
        except FileNotFoundError:
            print(f"File {aacfile} not found.")
    except subprocess.TimeoutExpired:
        print(
            f"ffmpeg file conversion error exceeded 30 seconds on {aacfile}. We will skip audio on this file and post text only."
        )
        apobj.notify(
            body=body,
            title=title,
        )
        try:
            Path(aacfile).unlink()
        except FileNotFoundError:
            print(f"File {aacfile} not found.")


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
    """Runs the main loop for transcribing audio files and sending notifications.

    Explanation:
        This function imports the notification destinations, searches for JSON files in the "media/transcribe" directory,
        transcribes the corresponding audio files using different methods based on environment variables,
        sends notifications using the transcribed text and the audio files, and deletes the JSON and audio files.

    Args:
        None

    Returns:
        None

    Raises:
        None

    Examples:
        None
    """
    # Import the apprise destinations to send calls
    destinations = import_notification_destinations()

    while 1:
        # First lets search the media directory for all json, sorted by creation time
        jsonlist = sorted(
            Path("media/transcribe").rglob("*.[jJ][sS][oO][nN]"), key=os.path.getctime
        )

        # If the queue is empty, pause for 5 seconds and then restart polling
        if not jsonlist:
            print("Empty queue. Sleep 5 seconds and check again.")
            time.sleep(5)
            continue

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
            # transformers
            if os.environ.get("TTT_DEEPGRAM_KEY", False):
                calljson = transcribe_deepgram(calljson, audiofile)
            elif os.environ.get("TTT_WHISPERCPP_URL", False):
                calljson = transcribe_whispercpp(calljson, audiofile)
            else:
                calljson = transcribe_transformers(calljson, audiofile)

            # When Whisper process a file with no speech, it tends to spit out "you"
            # Just "you" and nothing else.
            # So if the transcript is just "you", don't bother sending the notification,
            # we will just delete the files and keep going to the next call.
            if calljson["text"].strip() != "you":
                send_notifications(calljson, audiofile, destinations)

            # And now delete the files from the transcribe directory
            try:
                Path(jsonfile).unlink()
            except FileNotFoundError:
                print(f"File {jsonfile} not found.")
            except PermissionError:
                print(f"No permission to delete {jsonfile}.")
            try:
                Path(audiofile).unlink()
            except FileNotFoundError:
                print(f"File {audiofile} not found.")
            except PermissionError:
                print(f"No permission to delete {audiofile}.")


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


if __name__ == "__main__":
    main()
