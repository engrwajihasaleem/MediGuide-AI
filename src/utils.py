import json
import re

REQUIRED_KEYS = {
    "summary", "possible_conditions", "urgency_level",
    "recommended_next_steps", "questions_for_doctor", "warning_signs"
}
VALID_URGENCY = {"LOW", "MEDIUM", "HIGH", "EMERGENCY"}

def build_patient_inputs(**kwargs):
    return {
        "age": kwargs["age"],
        "gender": kwargs["gender"],
        "symptoms": ", ".join(kwargs["symptoms"]) if kwargs["symptoms"] else "Not specified",
        "symptom_details": kwargs["symptom_details"].strip() or "None provided",
        "duration": kwargs["duration"],
        "severity": kwargs["severity"],
        "conditions": kwargs["conditions"].strip() or "None provided",
        "medications": kwargs["medications"].strip() or "None provided",
        "notes": kwargs["notes"].strip() or "None provided",
        "language": kwargs["language"]
    }

def parse_json_safely(raw_text):
    if not isinstance(raw_text, str):
        raw_text = str(raw_text)
    cleaned = re.sub(r"^\s*```(?:json)?\s*|\s*```\s*$", "", raw_text.strip(), flags=re.I)
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start < 0 or end < start:
        return None, "No JSON object found."
    try:
        return json.loads(cleaned[start:end + 1]), None
    except json.JSONDecodeError as exc:
        return None, str(exc)

def validate_assessment(data):
    if not isinstance(data, dict):
        return False, "The response must be a JSON object."
    missing = REQUIRED_KEYS - set(data.keys())
    if missing:
        return False, f"Missing fields: {', '.join(sorted(missing))}"
    if data["urgency_level"] not in VALID_URGENCY:
        return False, "Invalid urgency level."
    if not isinstance(data["summary"], str):
        return False, "summary must be text."
    for key in ("possible_conditions",):
        if not isinstance(data[key], list):
            return False, f"{key} must be a list."
        for item in data[key]:
            if not isinstance(item, dict) or not {"name", "reason"}.issubset(item):
                return False, "Each possible condition needs name and reason."
    for key in ("recommended_next_steps", "questions_for_doctor", "warning_signs"):
        if not isinstance(data[key], list) or not all(isinstance(x, str) for x in data[key]):
            return False, f"{key} must be a list of text."
    return True, "Valid"

# Conservative phrase screen only. It is not a complete emergency detector.
EMERGENCY_PHRASES = [
    "severe chest pain", "crushing chest pain", "can't breathe",
    "cannot breathe", "difficulty breathing", "severe shortness of breath",
    "unconscious", "not waking up", "stroke symptoms", "face drooping",
    "one-sided weakness", "seizure", "heavy bleeding", "suicidal"
]

def detect_emergency_red_flags(patient):
    text = " ".join(str(v) for v in patient.values()).lower()
    return [phrase for phrase in EMERGENCY_PHRASES if phrase in text]

def emergency_override(data):
    """Utility for tests/integrations; emergency override must take precedence."""
    data = dict(data)
    data["urgency_level"] = "EMERGENCY"
    data["recommended_next_steps"] = [
        "Seek emergency medical help immediately. Do not wait for an AI response."
    ] + list(data.get("recommended_next_steps", []))
    return data
