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

        # System prompt (same behavior as Gemini chat history)
        self.system_prompt = (
            "You are a helpful medical assistant. "
            "If the user speaks in Hindi, respond in Hindi. "
            "If the user speaks in English, respond in English. "
            "Always detect the user's language and match it."
        )

        self.chat_history = [
            {"role": "system", "content": self.system_prompt}
        ]

    # -------------------------
    # PRESCRIPTION IMAGE ANALYSIS
    # -------------------------
    def analyze_prescription(self, image_bytes: bytes) -> str:
        try:
            # Convert image to base64
            image = Image.open(io.BytesIO(image_bytes))
            buffered = io.BytesIO()
            image.save(buffered, format="PNG")
            image_base64 = base64.b64encode(buffered.getvalue()).decode()

            prompt = """
                Analyze this prescription image.

                Provide a clear and concise summary including:
                1. Patient Name (if visible)
                2. Doctor Name (if visible)
                3. Date
                4. Prescribed Medicines and dosage instructions
                5. Special instructions (what to follow, dietary advice, etc.)
                6. What NOT to follow (contraindications if mentioned)

                Format the output in Markdown.
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

        except Exception as e:
            return f"Error analyzing prescription: {str(e)}"

    # -------------------------
    # NORMAL CHAT (TEXT)
    # -------------------------
    def chat_response(self, text: str) -> str:
        try:
            self.chat_history.append(
                {"role": "user", "content": text}
            )

            response = self.client.chat.completions.create(
                model="gpt-4.1",
                messages=self.chat_history,
                max_tokens=500
            )

            assistant_reply = response.choices[0].message.content
            self.chat_history.append(
                {"role": "assistant", "content": assistant_reply}
            )

            return assistant_reply

        except Exception as e:
            return f"Error getting response: {str(e)}"
