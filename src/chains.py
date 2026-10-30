
import json

from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from src.prompts import (
    SYSTEM_SAFETY_PROMPT,
    ASSESSMENT_TEMPLATE,
    ASSESSMENT_CHAT_TEMPLATE,
    NARRATIVE_CHAT_TEMPLATE,
)


# --------------------------------------------------
# OPENAI MODEL INITIALIZATION
# --------------------------------------------------

def get_llm(api_key, model_name="gpt-4o-mini", temperature=0.1):
    """Initialize OpenAI Chat Model."""

    if not api_key or not str(api_key).strip():
        raise ValueError("A validated OpenAI API key is required.")

    return ChatOpenAI(
        model=model_name,
        temperature=temperature,
        api_key=api_key,
        timeout=60,
        max_retries=2,
    )


# --------------------------------------------------
# PATIENT INFORMATION FORMATTER
# --------------------------------------------------

def format_patient_information(inputs):
    """Convert patient information into readable text."""

    lines = []

    for key, value in inputs.items():

        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False)

        lines.append(f"{key}: {value}")

    return "\n".join(lines)


# --------------------------------------------------
# ASSESSMENT CHAIN
# --------------------------------------------------

def build_assessment_chain(
    api_key,
    model_name="gpt-4o-mini",
    temperature=0.1
):
    """
    Build the MediGuide assessment chain using LCEL.

    Returns:
        Runnable producing {"text": model_response}
    """

    llm = get_llm(
        api_key=api_key,
        model_name=model_name,
        temperature=temperature,
    )

    text_chain = (
        ASSESSMENT_CHAT_TEMPLATE
        | llm
        | StrOutputParser()
    )

    return RunnableLambda(
        lambda inputs: {
            "text": text_chain.invoke(inputs)
        }
    )


# --------------------------------------------------
# INVOKE ASSESSMENT
# --------------------------------------------------

def invoke_assessment_with_chain(
    inputs,
    api_key,
    model_name="gpt-4o-mini",
    temperature=0.1
):
    """Generate structured educational health assessment."""

    chain = build_assessment_chain(
        api_key=api_key,
        model_name=model_name,
        temperature=temperature,
    )

    patient_information = ASSESSMENT_TEMPLATE.format(**inputs)

    return chain.invoke({
        "patient_information": patient_information
    })


# --------------------------------------------------
# MESSAGE CLASS DEMONSTRATION
# --------------------------------------------------

def message_class_demo(patient_information):
    """Demonstrate LangChain message classes."""

    return [
        SystemMessage(content=SYSTEM_SAFETY_PROMPT),

        HumanMessage(content=patient_information),

        AIMessage(
            content=(
                "I can provide general educational information, "
                "not a medical diagnosis."
            )
        ),
    ]


# --------------------------------------------------
# STREAMING NARRATIVE EXPLANATION
# --------------------------------------------------

def stream_narrative(
    api_key,
    model_name,
    temperature,
    inputs
):
    """Stream a natural-language explanation of the assessment."""

    llm = get_llm(
        api_key=api_key,
        model_name=model_name,
        temperature=temperature,
    )

    assessment_json = inputs["assessment_json"]

    if isinstance(assessment_json, (dict, list)):
        assessment_json = json.dumps(
            assessment_json,
            ensure_ascii=False,
            indent=2,
        )

    patient_data = {
        key: value
        for key, value in inputs.items()
        if key not in ("assessment_json", "language")
    }

    messages = NARRATIVE_CHAT_TEMPLATE.format_messages(
        language=inputs["language"],
        patient_information=format_patient_information(patient_data),
        assessment_json=assessment_json,
    )

    for chunk in llm.stream(messages):

        content = chunk.content

        if isinstance(content, str):
            if content:
                yield content

        elif isinstance(content, list):

            for part in content:

                if isinstance(part, dict) and part.get("type") == "text":
                    yield part.get("text", "")
