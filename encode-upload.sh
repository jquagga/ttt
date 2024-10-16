#!/bin/dash

echo "Copying $1 to transcribe directory"

mkdir -p ./media/transcribe
filename="$1"
basename="${filename%.*}"
audiofile="${basename}.wav"
json="${basename}.json"

cp "${json}" ./media/transcribe/
cp "${audiofile}" ./media/transcribe/
