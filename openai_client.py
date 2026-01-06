import os
import io
import base64
from dotenv import load_dotenv
from PIL import Image
from openai import OpenAI

load_dotenv()

class OpenAIClient:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        self.client = OpenAI(api_key=api_key)

        self.system_prompt = (
            "You are a helpful medical assistant. "
            "If the user speaks in Hindi, respond in Hindi. "
            "If the user speaks in English, respond in English. "
            "Always detect the user's language and match it. "
            "This is not a diagnosis. Always consult a qualified doctor."
        )

        self.chat_history = [
            {"role": "system", "content": self.system_prompt}
        ]

    def analyze_prescription(self, image_bytes: bytes) -> str:
        image = Image.open(io.BytesIO(image_bytes))
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        image_base64 = base64.b64encode(buffered.getvalue()).decode()

        prompt = """
            Analyze this prescription image.

            Provide:
            1. Patient Name (if visible)
            2. Doctor Name (if visible)
            3. Date
            4. Medicines & dosage
            5. Instructions
            6. Contraindications

            Format in Markdown.
        """

        response = self.client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": self.system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=800
        )

        return response.choices[0].message.content

    def chat_response(self, text: str) -> str:
        self.chat_history.append({"role": "user", "content": text})

        response = self.client.chat.completions.create(
            model="gpt-4.1",
            messages=self.chat_history,
            max_tokens=500
        )

        reply = response.choices[0].message.content
        self.chat_history.append({"role": "assistant", "content": reply})

        return reply
