# ttt

> [!IMPORTANT]
> And so, this project reaches it's archive period. While it's been fun and a cool tool, trying to keep whisper running on Openvino or other hardware has been a bit of an endless game of whack-a-mole. The domain has been retired and I'll leave the code here in case anyone wants to use it. Good luck out there!

[![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/jquagga/ttt/badge)](https://securityscorecards.dev/viewer/?uri=github.com/jquagga/ttt)
[![Docker](https://github.com/jquagga/ttt/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/jquagga/ttt/actions/workflows/docker-publish.yml)

ttt is small python file which collects json and wav file output from [trunk-recorder](https://github.com/robotastic/trunk-recorder) and uses Whisper.ai to convert speech to text. Essentially it is a "police scanner" which lets you read the conversation instead of just listening (but you can listen too if you like).

Since the text is A.I. generated all of the usual disclaimers apply. It's not perfect but it does a reasonable job if the audio coming from the system you are monitoring is understandable.

Presently, ~~www.pwcscanner.org~~ is running on ttt, serving notifications with ~~opus~~ AAC (to support Safari sadly) attachments to a self-hosted [ntfy](https://github.com/binwiederhier/ntfy). Reception needs to be improved as the audio quality periodically drops and transcription quality suffers but I'm happy with the start.

## Installation

The easiest way is probably to use the docker-compose.yml in this repository and bring up the image. It's a HUGE image - nearly 8GB - since it has the cuda (nvidia GPU) dependencies. If you don't use CUDA, you can certainly build your own image with mamba or conda and remove the cuda dependencies from the environment.yml

## Configuration

Configuration is all done by environmental variables and the destinations.csv(which tells ttt where to send notifications per talkgroup). Take a look at the code in ttt.py and you can see your options. A present there are 3 different speech to text options. The default if nothing is set is to use transformers whisper with openai/large-v3. That's the most accurate version I've found but you can use distil or other models.

If you set the Whisper.cpp variables, ttt will happily forward requests off to a whisper.cpp install. That's a really quick / easy way to get up if you don't have a cuda card as whisper can be built with CLBLAST for Radeon etc.

Finally, for testing and "just work now" you can sign up and use a Deepgram API key and processing can be done by "the cloud". I'd say that's probably not cost-effective over the long term but if you want to see what the system would spit out for you this takes minimal setup.

### destinations.csv

This is a pretty basic, 3 column csv with your system shortname, the talkgroup id in Decimal, and the apprise url to report to. It doesn't have to be ntfy. Any service apprise supports should work (discord, slack, matrix, mastodon, whatever).

```csv
short_name,talkgroup,url
pwcpw25,1003,ntfy://notarealtopic
```
