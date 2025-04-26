# this is for env variables
import os

# this is for regex in parsing the AI output
import re

# for transcript storage
import json

# this is for STT w/ the deepgram api
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions, Microphone

# this is for generating text with the google gemini api
from google import genai
from google.genai import types

# this is for the html conversion
from utils import md2html, text_to_speech

# this is for debugging
from icecream import ic

# config
# sorry for hardcoding this i hope u can forgive me
# ccc559c9ed26db13b0afd075339917e93f0c25f3
DEEPGRAM_API_KEY = "7dfa9bdcbc7c93f2a638fd5a2ceacc1d68e1193b"
GEMINI_MODEL = "gemini-2.0-flash"


# When it's time for a new slide, start a new slide by writing: 'NEXT' at the beginning of the message, followed by the new buffer content. If you find yourself removing something, odds are, it is time for a new slide.
# IMPORTANT: When you write 'NEXT', ONLY write it for the first time. For the next updates you don't need NEXT on top unless you are starting yet another slide.
# When a question is asked what you think is something the audience needs to think about, make a new slide (NEXT) which is just # <the question>, and once we have moved on from it or have said the answer, you can do NEXT again and either bring back the old slide contents with modifications or start a clean slide based on your discretion.


system_prompt = """You are an assistant for creating live presentation notes in markdown.

Your job is to take a stream of spoken input (as text) and maintain a markdown buffer that reflects key ideas clearly and concisely.

Each response should:
- Modify or append to the current markdown buffer
- Use clear, slide-like formatting

Always have SLIDE <number> at the beginning of the message, to indicate the current slide number. The first slide should be SLIDE 1, and each subsequent slide should increment the number by 1.
When it's time for a new slide, start a new slide by writing: SLIDE <next number> at the beginning of the message, followed by the new buffer content. If you find yourself removing something, odds are, it is time for a new slide.
When a question is asked what you think is something the audience needs to think about, make a new slide which is just # <the question>, and once we have moved on from it or have said the answer, you can do a new slide again and either bring back the old slide contents with modifications or start a clean slide based on your discretion.

Capabilities:
- You can use all basic markdown features
- You can use all HTML features when you see fit, by just adding plain HTML with no codeblock. For styles you can use <style> tags, or use tailwind classes.
- You have built-in support for mermaid diagrams! You can use them by writing ```mermaid at the beginning of the codeblock and ``` at the end. You can use this to create flowcharts, sequence diagrams, class diagrams, and more! Just make sure to enclose the text in "quotes" so things are escaped properly.

Style Guide:
- IMPORTANT: If YOU, the AI are adressed directly, you can add the answer, or whatever else the teacher asks for. Whenever you talk like this, make sure to surround your talking with `backticks!` Example: "AI, please say hello for me." `Hello!`.
- Keep bullet points short and presentation-ready
- Use markdown tables for simple grids or truth tables or other stuff
- Make sure it is written like a presentation, this means minimal notes that only work as an aid. Easy on the eyes. Simple and short, usually bullets or grids.
- Try and keep it simple and informal. Use lowercase for bullets and such.
- When you see fit, if there is a hypothetical example, do your best to make a visualization of it in markdown at the top of the slide. No need to overdo it though.
- ALWAYS use tabs for nested bullets. If you don't do this the parser cannot detect the nested bullets.
- NEVER put the full markdown in a codeblock. This is a big no-no. It will not be parsed correctly and it will be a mess. You can put the code in a codeblock if you want to show an example of something, but never the full markdown. This is very important.
- IMPORTANT: You are an AID. This means you should not be hasty and go ahead. You are only showing notes and only doing things when the teacher asks you to do so. No guesswork, assume user intent well and don't rush the teacher by going ahead. Keep it concise.
- IMPORTANT: If YOU, the AI are adressed directly, you can add the answer, or whatever else the teacher asks for. Whenever you talk like this, make sure to surround your talking with `backticks!` Example: "AI, please say hello for me." `Hello!`.
- Not every transcript update means you need to add/modify something. Though, sometimes it is okay to quickly rethink what you did in the buffer to make the notes more readable and useful. Transcript updates come as fast as possible, and are not nessecarily a deliberate set length. DONT TAKE NOTES ON EVERY SINGLE LITTLE THING.

""".strip()

# - You can use Latex like this:
#   When \\(a \\ne 0\\), there are two solutions to \\(ax^2 + bx + c = 0\\) and they are
#   \\[x = {-b \\pm \\sqrt{b^2-4ac} \\over 2a}.\\]


class PresentationAssistant:
    def __init__(self, system_prompt: str = system_prompt):
        self.system_prompt = system_prompt
        self.transcript = []
        self.transcript_id = 0

        self.client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
        self.contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text="""Hi class!\n"""),
                ],
            ),
            types.Content(
                role="model",
                parts=[
                    types.Part.from_text(
                        text="""SLIDE 1
# 👋 Hi class!\n"""
                    ),
                ],
            ),
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text="""...\n"""),
                ],
            ),
            types.Content(
                role="model",
                parts=[
                    types.Part.from_text(
                        text="""SLIDE 1
# 👋 Hi class!\n"""
                    ),
                ],
            ),
        ]

        self.system_prompt = types.Part.from_text(text=system_prompt)

    def process_transcription(self, text: str):
        self.transcript.append(text)

        self.transcript_id += 1
        with open("transcript.json", "w", encoding="utf-8") as f:
            json.dump({"id": self.transcript_id, "text": text}, f)

        # ic(self.contents)

        self.contents.append(
            types.Content(role="user", parts=[types.Part.from_text(text=text)])
        )

        config = types.GenerateContentConfig(
            response_mime_type="text/plain",
            system_instruction=[self.system_prompt],
        )

        response_text = ""
        for chunk in self.client.models.generate_content_stream(
            model=GEMINI_MODEL, contents=self.contents, config=config
        ):
            # print(chunk.text, end="")
            response_text += chunk.text

        self.contents.append(
            types.Content(
                role="model", parts=[types.Part.from_text(text=response_text)]
            )
        )

        self.update_html_buffer(response_text)

        # i wanted it to speak stuff but it was too much of a hassle to make it good

        # will find stuff inside of `<>` and speak it out with function
        # speaking_text = re.findall(r"`(.*?)`", response_text)
        # text_to_speech(speaking_text)

    def update_html_buffer(self, text=""):

        text = text.strip()

        text = re.sub(
            r"```mermaid\n(.*?)```",
            r'<div class="mermaid">\1</div>',
            text,
            flags=re.DOTALL,
        )

        with open("content.html", "w", encoding="utf-8") as f:
            tempHTML = md2html(text)

            # print(tempHTML)
            f.write(tempHTML)


text = """
# Hello class!
""".strip()


if __name__ == "__main__":
    assistant = PresentationAssistant()

    deepgram = DeepgramClient(api_key=DEEPGRAM_API_KEY)

    try:
        dg_connection = deepgram.listen.websocket.v("1")

        def on_message(self, result, **kwargs):
            if sentence := result.channel.alternatives[0].transcript:
                print(f"Transcript: {sentence}")
                assistant.process_transcription(sentence)  # auto-process

        dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
        dg_connection.on(
            LiveTranscriptionEvents.Error, lambda self, e: print(f"ERROR: {e}")
        )

        options = LiveOptions(
            model="nova-3",
            punctuate=True,
            language="en-US",
            encoding="linear16",
            channels=1,
            sample_rate=16000,
            smart_format=True,
            endpointing=1000,
        )

        dg_connection.start(options)
        microphone = Microphone(dg_connection.send)
        microphone.start()

        input("Press Enter to stop recording...\n\n")

        microphone.finish()
        dg_connection.finish()

    except Exception as e:
        print(f"Error: {e}")

    assistant.update_html_buffer(text)
