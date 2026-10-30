
# Conservative emergency phrase screening.
# This is NOT a validated medical triage system.

EMERGENCY_PHRASES = [

    "severe chest pain",
    "crushing chest pain",
    "cannot breathe",
    "can't breathe",
    "severe shortness of breath",
    "unconscious",
    "not waking up",
    "face drooping",
    "one-sided weakness",
    "heavy bleeding",
    "seizure"

]


def detect_emergency_red_flags(patient):

    symptom_text = " ".join([

        str(patient.get("symptoms", "")),

        str(patient.get("symptom_details", ""))

    ]).lower()

    detected = [

        phrase
        for phrase in EMERGENCY_PHRASES
        if phrase in symptom_text

    ]

    return detected
