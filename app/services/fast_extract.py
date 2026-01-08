import re

SYMPTOM_WORDS = [
    "fever", "cough", "cold", "pain", "headache", "vomit", "nausea",
    "fatigue", "weakness", "breathlessness", "sore throat", "diarrhea"
]
TEST_WORDS = [
    "cbc", "blood test", "x-ray", "mri", "ct", "urine test", "ecg",
    "lipid profile", "lft", "kft", "thyroid", "vitamin d", "rtpcr"
]

MED_MARKERS = [
    r"\bmg\b", r"\bml\b", r"\btablet\b", r"\btabs?\b", r"\bcapsules?\b",
    r"\bonce\b", r"\btwice\b", r"\bthrice\b", r"\bqd\b", r"\bbd\b", r"\btid\b"
]

def quick_extract(text: str, current: dict) -> dict:
    t = text.lower()
    out = {
        "patient_name": current.get("patient_name"),
        "age": current.get("age"),
        "gender": current.get("gender"),
        "symptoms": list(current.get("symptoms") or []),
        "diagnosis": current.get("diagnosis"),
        "medicines": list(current.get("medicines") or []),
        "medical_tests": list(current.get("medical_tests") or [])
    }
    name_match = re.search(r"(name\s*is|patient\s*name)\s*([a-zA-Z ]+)", t)
    if name_match:
        candidate = name_match.group(2).strip().title()
        if len(candidate) <= 40:
            out["patient_name"] = candidate
    age_match = re.search(r"\b(\d{1,3})\s*(years?|yrs?)\b", t)
    if age_match:
        out["age"] = age_match.group(1)
    if "female" in t:
        out["gender"] = "Female"
    elif "male" in t:
        out["gender"] = "Male"
    for w in SYMPTOM_WORDS:
        if w in t and w not in out["symptoms"]:
            out["symptoms"].append(w)
    diag_match = re.search(r"(diagnosis|impression|dx)\s*[:\-]\s*([a-zA-Z \-]+)", t)
    if diag_match:
        out["diagnosis"] = diag_match.group(2).strip().title()
    if any(re.search(m, t) for m in MED_MARKERS):
        med_name = None
        name_match2 = re.search(r"([a-zA-Z][a-zA-Z0-9\- ]{2,})\s*(\d+\s*mg|\d+\s*ml)?", t)
        if name_match2:
            med_name = name_match2.group(1).strip().title()
        dose = None
        dose_match = re.search(r"(\d+\s*mg|\d+\s*ml)", t)
        if dose_match:
            dose = dose_match.group(1)
        freq = None
        if "once" in t or "qd" in t:
            freq = "Once daily"
        elif "twice" in t or "bd" in t:
            freq = "Twice daily"
        elif "thrice" in t or "tid" in t:
            freq = "Thrice daily"
        if med_name:
            exists = False
            for m in out["medicines"]:
                if m.get("name") and m.get("name").lower() == med_name.lower():
                    if dose:
                        m["dose"] = dose
                    if freq:
                        m["frequency"] = freq
                    exists = True
                    break
            if not exists:
                out["medicines"].append({"name": med_name, "dose": dose, "frequency": freq})
    for tw in TEST_WORDS:
        if tw in t and tw not in [x.get("name","") for x in out["medical_tests"]]:
            out["medical_tests"].append({"name": tw.title()})
    return out