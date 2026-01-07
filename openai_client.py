import os
import io
import base64
import json
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
            model=os.getenv("OPENAI_MODEL"),
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
            model=os.getenv("OPENAI_MODEL"),
            messages=self.chat_history,
            max_tokens=500
        )

        reply = response.choices[0].message.content
        self.chat_history.append({"role": "assistant", "content": reply})

        return reply

    def extract_patient_info(self, text: str, current: dict) -> dict:
        schema = {
            "patient_name": None,
            "age": None,
            "gender": None,
            "doctor_name": None,
            "checkup_date": None,
            "checkup_details": None,
            "symptoms": [],
            "diagnosis": None,
            "medicines": [],
            "notes": []
        }
        base = {**schema, **(current or {})}
        prompt = (
            "Extract structured medical details from the user's input. "
            "Return ONLY valid JSON matching this schema keys: "
            "patient_name, age, gender, doctor_name, checkup_date, checkup_details, symptoms, diagnosis, medicines, notes. "
            "symptoms: array of strings. "
            "medicines: array of objects with keys: name, dose, frequency. "
            "If a field is not mentioned, leave as null or empty array. "
            "User input: "
            + text
        )
        resp = self.client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL"),
            messages=[
                {"role": "system", "content": "You output ONLY JSON without extra text."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400
        )
        content = resp.choices[0].message.content or "{}"
        try:
            data = json.loads(content)
        except Exception:
            try:
                start = content.find("{")
                end = content.rfind("}")
                data = json.loads(content[start:end+1]) if start != -1 and end != -1 else {}
            except Exception:
                data = {}
        merged = base.copy()
        for k in merged.keys():
            if k in data and data[k] is not None and data[k] != "":
                if isinstance(merged[k], list) and isinstance(data[k], list):
                    if k == "medicines":
                        current_meds = merged[k]
                        for new_med in data[k]:
                            exists = False
                            for med in current_meds:
                                if med.get("name") and new_med.get("name") and med.get("name").lower() == new_med.get("name").lower():
                                    med.update(new_med)
                                    exists = True
                                    break
                            if not exists:
                                current_meds.append(new_med)
                        merged[k] = current_meds
                    else:
                        # For symptoms and notes, append unique
                        current_list = merged[k]
                        for item in data[k]:
                            if item not in current_list:
                                current_list.append(item)
                        merged[k] = current_list
                else:
                    merged[k] = data[k]
        return merged
