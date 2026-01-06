import os
import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image
import io

load_dotenv()

class GeminiClient:
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        
        genai.configure(api_key=api_key)
        # User requested gemini-2.5-flash specifically
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.chat = self.model.start_chat(history=[
            {
                "role": "user",
                "parts": ["You are a helpful medical assistant. If the user speaks in Hindi, you must respond in Hindi. If the user speaks in English, respond in English. Always detect the language of the user's input and match it."]
            },
            {
                "role": "model",
                "parts": ["Understood. I will act as a helpful medical assistant and respond in the same language as the user (Hindi or English)."]
            }
        ])

    def analyze_prescription(self, image_bytes: bytes) -> str:
        try:
            image = Image.open(io.BytesIO(image_bytes))
            prompt = """
            Analyze this prescription image. 
            Provide a clear and concise summary including:
            1. Patient Name (if visible)
            2. Doctor Name (if visible)
            3. Date
            4. Prescribed Medicines and dosage instructions
            5. Special instructions (What to follow, dietary advice, etc.)
            6. What NOT to follow (if any specific contraindications are mentioned or implied).
            
            Format the output as Markdown.
            """
            response = self.model.generate_content([prompt, image])
            return response.text
        except Exception as e:
            return f"Error analyzing prescription: {str(e)}"

    def chat_response(self, text: str) -> str:
        try:
            response = self.chat.send_message(text)
            return response.text
        except Exception as e:
            return f"Error getting response: {str(e)}"
