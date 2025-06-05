
# Voice activated/responses with Chat GPT

Python 3 project that wraps ChatGPT with a voice recognition package and a speech package.

The project prompts you for speech input and the ChatGPT response will be read back to you.<br>
You can use a (optional) "keyword" (Default is "Computer") which you will have to prefix your question with in order for it to be sent to ChatGPT.<br>
The sessions are context aware, meaning ChatGPT will remember your previous questions and comments during the session.<br>

NOTE:<br>
The default model is "gpt-3.5-turbo" which is pretty old at this point and should probably be replaced with something newer.<br>


```
Packages used:
openai==1.84.0                  # OpenAI/ChatGPT
pyttsx3==2.98                   # Text to speech output
SpeechRecognition==3.14.3       # Speech recognition, speech to text
PyAudio==0.2.14
dotenv==0.9.9                   # Environment file
```

```
Usage:
 python3 chat.py {params}

Parameters:
  -audio     Turn on full audio support, use both microphone and speakers. (Current=False)
  -mic       Use microphone input. (Current=False)
  -speaker   Use speaker output. (Current=False)
  -usekey    Use keyword. The keyword can be set in config.py (Current=computer)
  -full      Show full json response. (Current=False)
  -test      Test mode does not use ChatGPT and returns a hardcoded response instead. (Current=False)

In chat commands:
  exit       Exit the chat program
  quit       Same as exit
  save       Save chat as a text file into the 'logs' folder

Example:
 python3 chat.py -test -audio
   # Start in test mode (don't connect to ChatGPT) and use both the microphone and speakers

```
