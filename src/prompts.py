
import json

from langchain_core.messages import SystemMessage
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate


# --------------------------------------------------
# ASSESSMENT OUTPUT SCHEMA
# --------------------------------------------------

ASSESSMENT_JSON_SCHEMA = {
    "summary": "string",
    "possible_conditions": [
        {
            "name": "string",
            "reason": "string"
        }
    ],
    "urgency_level": "LOW | MEDIUM | HIGH | EMERGENCY",
    "recommended_next_steps": ["string"],
    "questions_for_doctor": ["string"],
    "warning_signs": ["string"]
}


# --------------------------------------------------
# SYSTEM SAFETY PROMPT
# --------------------------------------------------

SYSTEM_SAFETY_PROMPT = """
You are MediGuide AI, an educational health-information assistant.

You are NOT a doctor, clinician, emergency service, or diagnostic system.

IMPORTANT SAFETY RULES:

1. Never claim or imply a confirmed diagnosis.
2. Never prescribe medication.
3. Never recommend starting, stopping, or changing medication or dosage.
4. Provide cautious general educational information only.
5. Encourage consultation with a qualified healthcare professional.
6. If information suggests an emergency, set urgency_level to EMERGENCY
   and clearly advise immediate emergency care.
7. Do not falsely reassure the user.
8. If information is insufficient, clearly state this.
9. Possible conditions are educational possibilities, not diagnoses.
10. Use the requested response language for all user-facing text.

OUTPUT REQUIREMENTS:

Return ONLY one valid JSON object matching this structure:

{
    "summary": "",
    "possible_conditions": [
        {
            "name": "",
            "reason": ""
        }
    ],
    "urgency_level": "LOW",
    "recommended_next_steps": [],
    "questions_for_doctor": [],
    "warning_signs": []
}

urgency_level must be exactly one of:
LOW, MEDIUM, HIGH, EMERGENCY.

Do not include Markdown fences or text outside the JSON object.
"""


# --------------------------------------------------
# PATIENT ASSESSMENT TEMPLATE
# --------------------------------------------------

ASSESSMENT_TEMPLATE = PromptTemplate(
    input_variables=[
        "age",
        "gender",
        "symptoms",
        "symptom_details",
        "duration",
        "severity",
        "conditions",
        "medications",
        "notes",
        "language",
    ],
    template="""
Patient information:

Age: {age}
Gender: {gender}
Selected symptoms: {symptoms}
Additional symptom details: {symptom_details}
Duration: {duration}
Severity (1-10): {severity}
Existing conditions: {conditions}
Current medications: {medications}
Additional notes: {notes}
Response language: {language}

Provide cautious educational guidance using the required JSON schema.
"""
)


# --------------------------------------------------
# ASSESSMENT CHAT TEMPLATE
# IMPORTANT:
# SystemMessage keeps the JSON braces literal.
# LangChain will NOT parse them as template variables.
# --------------------------------------------------

ASSESSMENT_CHAT_TEMPLATE = ChatPromptTemplate.from_messages([
    SystemMessage(content=SYSTEM_SAFETY_PROMPT),
    ("human", "{patient_information}")
])


# --------------------------------------------------
# NARRATIVE EXPLANATION TEMPLATE
# --------------------------------------------------

NARRATIVE_SYSTEM_PROMPT = """
You are MediGuide AI.

Explain the already-generated educational assessment
in clear, calm and understandable language.

IMPORTANT RULES:

1. Do not add a diagnosis.
2. Do not introduce new medical claims.
3. Do not provide treatment or medication instructions.
4. Reiterate that the user should consult a qualified
   healthcare professional.
5. If urgency is EMERGENCY, advise immediate emergency help.
6. Respond in the requested language.
"""


NARRATIVE_CHAT_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", NARRATIVE_SYSTEM_PROMPT),
    (
        "human",
        """
Requested language: {language}

Patient information:
{patient_information}

Structured assessment:
{assessment_json}

Write a concise, understandable explanation.
"""
    )
])
