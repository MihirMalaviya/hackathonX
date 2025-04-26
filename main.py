# this is for env variables
import os

# this is for regex in parsing the AI output
import re

# from pygments import highlight
# from pygments.lexers import PythonLexer
# from pygments.formatters import HtmlFormatter

# this is for STT w/ the deepgram api
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions, Microphone

# this is for generating text with the google gemini api
from google import genai
from google.genai import types

# this is for the html conversion
from utils import md2html

# this is for debugging
from icecream import ic

# config
# sorry for hardcoding this i hope u can forgive me
DEEPGRAM_API_KEY = "7dfa9bdcbc7c93f2a638fd5a2ceacc1d68e1193b"
GEMINI_MODEL = "gemini-2.0-flash"


system_prompt = """You are an assistant for creating live presentation notes in markdown.

Your job is to take a stream of spoken input (as text) and maintain a markdown buffer that reflects key ideas clearly and concisely.

Each response should:
- Modify or append to the current markdown buffer
- Use clear, slide-like formatting

When it's time for a new slide, start a new slide by writing: 'NEXT' at the beginning of the message, followed by the new buffer content. If you find yourself removing something, odds are, it is time for a new slide.
IMPORTANT: When you write 'NEXT', ONLY write it for the first time. For the next updates you don't need NEXT on top unless you are starting yet another slide.
When a question is asked what you think is something the audience needs to think about, make a new slide (NEXT) which is just # <the question>, and once we have moved on from it or have said the answer, you can do NEXT again and either bring back the old slide contents with modifications or start a clean slide based on your discretion.

Capabilities:
- You can use all basic markdown features
- You can use all HTML features when you see fit, by just adding plain HTML with no codeblock. For styles you can use <style> tags, or use tailwind classes.
- You have built-in support for mermaid diagrams! You can use them by writing ```mermaid at the beginning of the codeblock and ``` at the end. You can use this to create flowcharts, sequence diagrams, class diagrams, and more! Just make sure to enclose the text in "quotes" so things are escaped properly.

""".strip()


class PresentationAssistant:
    def __init__(self, system_prompt: str = system_prompt):
        self.system_prompt = system_prompt
        self.transcript = []

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
