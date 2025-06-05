"""
Cyb's ChatGPT Client - (c)2023
"""
import io
import sys
import time
import os
from datetime import datetime
from dotenv import load_dotenv
import speech_recognition as sr
import pyttsx3
import openai
import config as cfg


speech_input = None
speech_output = None


# ---------------------------------------------------------
def main():
    """

    :return:
    """
    global speech_input, speech_output

    try:

        can_start = load_env()
        if not can_start:
            return
        
        parse_args()
        hello_world()
        show_usage()
        do_chat = True
        skip_chat = False
        input_mode = ("Talk" if cfg.gpt["use_microphone"] else "Type")
        output_mode = ("Talk" if cfg.gpt["use_speakers"] else "Text")
        if not cfg.gpt["do_test"]:
            chat_partner = "ChatGPT"
        else:
            chat_partner = "Test"

        openai.organization = cfg.gpt["organization"]
        openai.api_key = cfg.gpt["api_key"]

        if cfg.gpt["use_microphone"]:
            speech_input = sr.Recognizer()

        if cfg.gpt["use_speakers"]:
            speech_output = pyttsx3.init()

        keyword_lower = cfg.gpt["keyword"].lower().strip()
        keyword_len = len(keyword_lower)

        print("-----------------------------------")

        while do_chat:

            if cfg.gpt["use_microphone"]:
                print("\n[You::{}]".format(input_mode))
                question = record_text()
                print("{}".format(question))
            else:
                question = input("\n[You::{}]\n".format(input_mode))

            if not question:
                print("[System]\nFailed to record a question, please try again ...\n")
                continue

            # Convert to lowercase for easier compare
            question_lower = question.lower().strip()

            # Check for in-chat commands

            # Are we done chatting?
            # if question_lower == "exit" or question_lower == "quit":
            if question_lower.startswith("exit") or question_lower.startswith("quit"):
                do_chat = False

            # Save the conversation to a text file
            # Ignore the command and prompt for the next chat input
            if question_lower == "save":
                save_messages_to_file()
                skip_chat = True

            # Add our question to the conversation list
            if do_chat and not skip_chat:

                # Check for keyword
                if cfg.gpt["use_keyword"]:
                    if question_lower.startswith(keyword_lower):
                        question = question[keyword_len:].strip()
                    else:
                        print("[System]\nMissing keyword, skipping ...\n")
                        continue

                cfg.gpt["messages"].append({"role": "user", "content": question})

                # Send the whole conversation to ChatGPT
                if not cfg.gpt["do_test"]:
                    response = send_message()
                else:
                    right_back_at_you = "You said: {}".format(question)
                    response = {
                        "created": int(time.time()),
                        "choices": [{"message": {"role": "assistant", "content": right_back_at_you}}]
                    }

                if not "None" == response:
                    
                    if cfg.gpt["show_full_response"]:
                        print("\n[{}::{}]\n{}".format(chat_partner, output_mode, response))

                    gpt_time = response["created"]
                    gpt_role = response["choices"][0]["message"]["role"]
                    gpt_content = response["choices"][0]["message"]["content"]

                    if 0 == cfg.gpt["start_time"]:
                        cfg.gpt["start_time"] = gpt_time

                    if not cfg.gpt["show_full_response"]:
                        print("\n[{}::{}]\n{}".format(chat_partner, output_mode, gpt_content))

                    if cfg.gpt["use_speakers"]:
                        speak_text(gpt_content)

                    # Add the ChatGPT answer to the conversation list
                    cfg.gpt["messages"].append({"role": gpt_role, "content": gpt_content})

            skip_chat = False

        print(" \n")

    except Exception as ex:
        sys.stderr.write("main(): {}\n".format(ex))


# ---------------------------------------------------------
# noinspection PyUnresolvedReferences
def speak_text(text_to_speak):
    """

    :return:
    """
    global speech_output

    if speech_output and text_to_speak:
        speech_output.say(text_to_speak)
        speech_output.runAndWait()


# ---------------------------------------------------------
# noinspection PyUnresolvedReferences,PyUnusedLocal
def record_text():
    """

    :return:
    """
    global speech_input

    audio_text = None
    do_record = True

    if speech_input:
        while do_record:

            try:

                with sr.Microphone() as audio_source:
                    speech_input.adjust_for_ambient_noise(audio_source, duration=0.2)
                    audio = speech_input.listen(audio_source)

                    # Looks like recognize_google() has a bug in 3.9.0
                    # where it always prints out the full json response to stdout
                    # We use this ugly wrapper trap to get rid of it
                    text_trap = io.StringIO()
                    sys.stdout = text_trap
                    audio_text = speech_input.recognize_google(audio, show_all=False)
                    sys.stdout = sys.__stdout__

                    do_record = False

            except sr.RequestError:
                # sys.stderr.write("ERROR: record_text(e1): {}\n".format(e1))
                pass
            except sr.UnknownValueError as e2:
                # sys.stderr.write("ERROR: record_text(e2): {}\n".format(e2))
                pass
            except Exception as ex:
                sys.stderr.write("ERROR: record_text(ex): {}\n".format(ex))
                audio_text = None
                do_record = False

    return audio_text


# ---------------------------------------------------------
def send_message() -> dict:
    """

    :return:
    """

    response = "None"

    try:
        response = openai.ChatCompletion.create(
            model=cfg.gpt["model"],
            temperature=cfg.gpt["temperature"],
            messages=cfg.gpt["messages"]
        )

    except Exception as ex:
        sys.stderr.write("ERROR: send_message(): {}\n".format(ex))

    return response


# ---------------------------------------------------------
def save_messages_to_file():
    """

    :return:
    """

    try:

        file_name = "gpt_{}.txt".format(
            datetime.fromtimestamp(cfg.gpt["start_time"]).strftime("%Y-%m-%d_%H.%M.%S")
        )

        with open(file_name, "w") as f:
            for msg_dict in cfg.gpt["messages"]:
                f.write("\n[{}]\n{}\n".format(msg_dict["role"], msg_dict["content"]))

    except Exception as ex:
        sys.stderr.write("ERROR: save_messages_to_file(): {}\n".format(ex))


# ---------------------------------------------------------
def load_env():
    """

    :return:
    """

    load_dotenv()  # Load environment variables from .env file

    gpt_org = os.getenv('GPT_ORG')
    api_key = os.getenv('GPT_API_KEY')
    
    if gpt_org:
        cfg.gpt["organization"] = gpt_org
    else:
        sys.stderr.write("ERROR: load_env(): GPT_ORG not found in .env or environment\n")
        return False

    if api_key:
        cfg.gpt["api_key"] = api_key
    else:
        sys.stderr.write("ERROR: load_env(): GPT_API_KEY not found in .env or environment\n")
        return False
        
    return True


# ---------------------------------------------------------
def parse_args():
    """

    :return:
    """

    # Read command line params
    argc = len(sys.argv)
    if argc > 1:

        # Loop through the arguments, ignore argv[0]
        for x in range(1, argc):
            arg_low = sys.argv[x].lower().strip()

            # Do Test?
            if arg_low == "-test":
                cfg.gpt["do_test"] = True

            # Show full response?
            if arg_low == "-full":
                cfg.gpt["show_full_response"] = True

            # Turn on full audio support?
            if arg_low == "-audio":
                cfg.gpt["use_audio"] = True
                cfg.gpt["use_microphone"] = True
                cfg.gpt["use_speakers"] = True

            # Use microphone?
            if arg_low == "-mic":
                cfg.gpt["use_microphone"] = True

            # Use speakers?
            if arg_low == "-speaker":
                cfg.gpt["use_speakers"] = True

            # Use keyword?
            if arg_low == "-usekey":
                cfg.gpt["use_keyword"] = True


# ---------------------------------------------------------
def show_usage():
    """

    :return:
    """

    print(" ")
    print("Usage:")
    print(" python3 chat.py {params}")
    print(" ")
    print("Parameters:")
    print("  -audio     Turn on full audio support, use both microphone and speakers. (Current={})".format(
        cfg.gpt["use_audio"]
    ))
    print("  -mic       Use microphone input. (Current={})".format(
        cfg.gpt["use_microphone"]
    ))
    print("  -speaker   Use speaker output. (Current={})".format(
        cfg.gpt["use_speakers"]
    ))
    print("  -usekey    Use keyword. The keyword can be set in config.py (Current={})".format(
        cfg.gpt["keyword"]
    ))
    print("  -full      Show full json response. (Current={})".format(
        cfg.gpt["show_full_response"]
    ))
    print("  -test      Test mode does not use ChatGPT and returns a hardcoded response instead. (Current={})".format(
        cfg.gpt["do_test"]
    ))
    print(" ")
    print("In chat commands:")
    print("  exit       Exit the chat program")
    print("  quit       Same as exit")
    print("  save       Save chat as a text file into the 'logs' folder")
    print(" ")
    print("Example:")
    print(" python3 chat.py -test -audio")
    print("   # Start in test mode (don't connect to ChatGPT) and use both the microphone and speakers")
    print(" ")


# ---------------------------------------------------------
def hello_world():
    """

    :return:
    """

    print(" ")
    print("         .d88888b.             ")
    print("       .8P'     '9bd888b.      ")
    print("      .8P     .d8P'   `'988.   ")
    print("   .8888   .d8P'    ,     98.  ")
    print(" .8P' 88   8'    .d98b.    88  ")
    print(".8P   88   8 .d8P'   '98b. 88  ")
    print("88    88   8P'  `'8b.    '98.  ")
    print("88.   88   8       8'8b.    88 ")
    print(" 88    '98.8       8   88   '88")
    print("  `8b.    '98.,  .d8   88    88")
    print("  88 '98b.   .d8P' 8   88   d8'")
    print("  88    '98bP'    .8   88 .d8' ")
    print("  '8b     `    .d8P'   8888'   ")
    print("   '88b.,   .d8P'     d8'      ")
    print("     '9888P98b.     .d8'       ")
    print("             '988888P'             Cyb's ChatGPT Client - (c)2023")
    print("                                          {}".format(cfg.gpt["model"]))


# ---------------------------------------------------------
if __name__ == "__main__":
    main()
