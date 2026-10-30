
import json
import streamlit as st
from src.pdf_service import build_pdf_report


from src.config import (
    APP_NAME, APP_DESCRIPTION, LANGUAGES, GENDERS, SYMPTOM_OPTIONS,
    DURATION_OPTIONS, DEFAULT_MODEL
)
from src.chains import build_assessment_chain, stream_narrative
from src.auth import SESSION_KEY, render_login
from src.prompts import ASSESSMENT_TEMPLATE
from src.cache_manager import configure_cache
from src.utils import (
    parse_json_safely, validate_assessment, build_patient_inputs,
    emergency_override
)
from src.database import (
    init_db, save_assessment, get_history, delete_history
)
from src.safety import detect_emergency_red_flags


# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🩺",
    layout="wide"
)


# ---------------------------------------------------------
# AUTHENTICATION
# ---------------------------------------------------------

if not st.session_state.get(SESSION_KEY):
    render_login()
    st.stop()

api_key = st.session_state[SESSION_KEY]


# ---------------------------------------------------------
# DATABASE INITIALIZATION
# ---------------------------------------------------------

init_db()


# ---------------------------------------------------------
# DISCLAIMER
# ---------------------------------------------------------

DISCLAIMER = (
    "**Educational prototype only.** MediGuide AI is not a doctor and does not "
    "provide a diagnosis, emergency service, or treatment. It cannot replace "
    "a licensed healthcare professional. Consult a qualified clinician for "
    "medical concerns. If symptoms are severe or life-threatening, contact "
    "local emergency services immediately."
)


# ---------------------------------------------------------
# APPLICATION HEADER
# ---------------------------------------------------------

st.title("🩺 MediGuide AI")
st.caption(APP_DESCRIPTION)
st.error(DISCLAIMER)


# ---------------------------------------------------------
# SIDEBAR CONFIGURATION
# ---------------------------------------------------------

with st.sidebar:

    st.header("MediGuide AI")

    if st.button("Log out", use_container_width=True):
        st.session_state.pop(SESSION_KEY, None)
        st.session_state.pop("api_key_input", None)
        st.rerun()

    st.write("A safety-first educational symptom guidance prototype.")

    st.warning(DISCLAIMER)

    st.subheader("Model configuration")

    model_name = st.text_input(
        "OpenAI model",
        value=DEFAULT_MODEL
    )

    temperature = st.slider(
        "Temperature",
        0.0,
        1.0,
        0.1,
        0.1
    )

    language = st.selectbox(
        "Answer language",
        LANGUAGES,
        index=0
    )

    st.subheader("Caching")

    cache_enabled = st.toggle(
        "Enable response cache",
        value=True
    )

    cache_type = st.selectbox(
        "Cache type",
        ["SQLiteCache", "InMemoryCache"]
    )

    if cache_enabled:
        configure_cache(cache_type)
    else:
        configure_cache("Disabled")

    st.caption(
        "InMemoryCache clears when the app process stops. "
        "SQLiteCache persists on disk."
    )


# ---------------------------------------------------------
# PATIENT INFORMATION FORM
# ---------------------------------------------------------

st.subheader("Patient information")

with st.form("patient_form"):

    c1, c2 = st.columns(2)

    with c1:

        age_text = st.text_input(
            "Age",
            placeholder="e.g. 35"
        )

        gender = st.selectbox(
            "Gender",
            GENDERS
        )

        symptoms = st.multiselect(
            "Select symptoms",
            SYMPTOM_OPTIONS
        )

        symptom_details = st.text_area(
            "Other symptoms / details",
            height=90
        )

        duration = st.selectbox(
            "Duration of symptoms",
            DURATION_OPTIONS
        )

    with c2:

        severity = st.slider(
            "Overall symptom severity (1 = mild, 10 = severe)",
            1,
            10,
            3
        )

        conditions = st.text_area(
            "Existing medical conditions",
            height=90
        )

        medications = st.text_area(
            "Current medications",
            height=90
        )

        notes = st.text_area(
            "Additional notes (optional)",
            height=90
        )

    submitted = st.form_submit_button(
        "Assess symptoms",
        type="primary",
        use_container_width=True
    )


# ---------------------------------------------------------
# ASSESSMENT PROCESSING
# ---------------------------------------------------------

if submitted:

    if not age_text.strip().isdigit() or not (0 <= int(age_text) <= 120):
        st.warning("Please enter a valid age between 0 and 120.")
        st.stop()

    if not symptoms and not symptom_details.strip():
        st.warning(
            "Please enter or select at least one symptom. "
            "No API request was made."
        )
        st.stop()

    patient = build_patient_inputs(
        age=int(age_text),
        gender=gender,
        symptoms=symptoms,
        symptom_details=symptom_details,
        duration=duration,
        severity=severity,
        conditions=conditions,
        medications=medications,
        notes=notes,
        language=language
    )

    # -----------------------------------------------------
    # EMERGENCY PHRASE SCREEN
    # -----------------------------------------------------

    red_flags = detect_emergency_red_flags(patient)

    if red_flags:

        st.error("Potential emergency warning detected")

        st.write(
            "Your description includes symptoms that may require immediate "
            "assessment. Do not wait for an AI assessment. Contact local "
            "emergency services or go to the nearest emergency department now."
        )

        st.write("Detected terms:", ", ".join(red_flags))

        st.info(
            "This safety check is limited and cannot identify every emergency."
        )

        st.stop()

    # -----------------------------------------------------
    # AI ASSESSMENT
    # -----------------------------------------------------

    st.info(
        "The following is general educational information, not a diagnosis."
    )

    try:

        with st.spinner("Preparing a safety-focused assessment..."):

            chain = build_assessment_chain(
                api_key=api_key,
                model_name=model_name,
                temperature=temperature
            )

            patient_information = ASSESSMENT_TEMPLATE.format(**patient)

            result = chain.invoke({
                "patient_information": patient_information
            })

            raw_output = (
                result.get("text", "")
                if isinstance(result, dict)
                else str(result)
            )

            parsed, error = parse_json_safely(raw_output)

        # -------------------------------------------------
        # JSON VALIDATION
        # -------------------------------------------------

        if error:

            st.error(
                "The AI response could not be read as valid JSON. "
                "Please try again."
            )

            with st.expander("Technical output for debugging"):
                st.code(raw_output)

            st.stop()

        valid, validation_message = validate_assessment(parsed)

        if not valid:

            st.error(
                f"The AI response did not match the required format: "
                f"{validation_message}"
            )

            with st.expander("Raw model response"):
                st.code(raw_output)

            st.stop()

        # -------------------------------------------------
        # URGENCY DISPLAY
        # -------------------------------------------------

        if parsed["urgency_level"] == "EMERGENCY":

            st.error(
                "The AI has flagged this as potentially urgent. "
                "Seek emergency medical help immediately."
            )

        elif parsed["urgency_level"] == "HIGH":

            st.warning("Prompt medical assessment is recommended.")

        elif parsed["urgency_level"] == "MEDIUM":

            st.warning(
                "Consider contacting a qualified healthcare professional."
            )

        else:

            st.success(
                "The AI has assigned a LOW urgency level. "
                "This does not rule out a medical problem."
            )

        # -------------------------------------------------
        # STREAMING PATIENT GUIDANCE
        # -------------------------------------------------

        st.subheader("Live patient guidance")

        narrative_inputs = {
            **patient,
            "assessment_json": json.dumps(
                parsed,
                ensure_ascii=False
            )
        }

        # Streamlit displays each chunk as it arrives.
        # The returned value contains the completed narrative.
        narrative = st.write_stream(
            stream_narrative(
                api_key,
                model_name,
                temperature,
                narrative_inputs
            )
        )

        # -------------------------------------------------
        # SAVE COMPLETED SESSION
        # -------------------------------------------------

        if not isinstance(narrative, str):
            narrative = str(narrative or "")

        try:

            record_id = save_assessment(
                patient=patient,
                assessment=parsed,
                narrative=narrative
            )

            st.success(
                f"Assessment saved successfully. Session ID: {record_id}"
            )

        except Exception:

            record_id = None

            st.warning(
                "The assessment was generated, but its history could not "
                "be saved. Please check the local database."
            )
        # -------------------------------------------------
        # DOWNLOAD PDF REPORT
        # -------------------------------------------------

        st.subheader("📄 Download Patient Guidance Report")

        try:
            pdf_data = build_pdf_report(
                patient=patient,
                assessment=parsed,
                narrative=narrative,
                record_id=record_id if record_id is not None else "Not saved"
            )

            st.download_button(
                label="Download Patient Guidance PDF",
                data=pdf_data,
                file_name=f"mediguide_report_{record_id or 'latest'}.pdf",
                mime="application/pdf",
                key=f"download_current_pdf_{record_id or 'latest'}"
            )

        except Exception as pdf_error:
            st.warning(
                "The PDF report could not be generated. "
                "Please check the PDF service."
            )
        # -------------------------------------------------
        # ASSESSMENT DASHBOARD
        # -------------------------------------------------

        st.divider()
        st.subheader("Assessment dashboard")

        st.metric(
            "Suggested urgency level",
            parsed["urgency_level"]
        )

        st.write("**Patient symptom summary**")
        st.write(parsed["summary"])

        tab1, tab2, tab3, tab4 = st.tabs([
            "Possible conditions",
            "Next steps",
            "Ask your doctor",
            "Warning signs"
        ])

        with tab1:

            st.caption(
                "Educational possibilities only. These are not diagnoses."
            )

            for item in parsed["possible_conditions"]:

                st.markdown(f"**{item['name']}**")
                st.write(item["reason"])

        with tab2:

            for item in parsed["recommended_next_steps"]:
                st.markdown(f"- {item}")

        with tab3:

            for item in parsed["questions_for_doctor"]:
                st.markdown(f"- {item}")

        with tab4:

            for item in parsed["warning_signs"]:
                st.markdown(f"- {item}")

        st.error(DISCLAIMER)

        # -------------------------------------------------
        # DOWNLOAD JSON
        # -------------------------------------------------

        st.download_button(
            "Download assessment JSON",
            data=json.dumps(
                parsed,
                ensure_ascii=False,
                indent=2
            ),
            file_name="mediguide_assessment.json",
            mime="application/json"
        )

    except Exception:

        st.error(
            "MediGuide could not complete the request. Check your API key, "
            "internet connection and package setup."
        )


# ---------------------------------------------------------
# PATIENT SESSION HISTORY
# ---------------------------------------------------------

st.divider()
st.header("📋 Patient Session History")

st.caption(
    "Review previously completed assessments stored in your local database."
)

try:

    history = get_history(limit=100)

    if not history:

        st.info(
            "No saved sessions yet. Complete your first assessment "
            "to see it here."
        )

    else:

        st.metric(
            "Total saved sessions",
            len(history)
        )

        # Build readable labels for the session selector.
        session_labels = {}

        for item in history:

            session_id = item["id"]
            created_at = item.get("created_at", "Unknown date")
            urgency = item.get("urgency", "Unknown")
            symptoms_text = item.get("symptoms", "No symptoms")

            label = (
                f"Session #{session_id} | {created_at} | "
                f"{urgency} | {str(symptoms_text)[:45]}"
            )

            session_labels[label] = item

        selected_label = st.selectbox(
            "Select a previous patient session",
            list(session_labels.keys()),
            key="history_session_selector"
        )

        selected_session = session_labels[selected_label]

        # -------------------------------------------------
        # DISPLAY SELECTED SESSION
        # -------------------------------------------------

        st.subheader(
            f"Session #{selected_session['id']}"
        )

        st.caption(
            f"Created: {selected_session.get('created_at', 'Unknown')}"
        )

        patient_data = selected_session["patient"]
        assessment_data = selected_session["assessment"]

        h1, h2 = st.columns(2)

        with h1:

            st.write("**Patient information**")
            st.write(f"Age: {patient_data.get('age', 'N/A')}")
            st.write(f"Gender: {patient_data.get('gender', 'N/A')}")
            st.write(
                f"Symptoms: {patient_data.get('symptoms', 'N/A')}"
            )
            st.write(
                f"Duration: {patient_data.get('duration', 'N/A')}"
            )
            st.write(
                f"Severity: {patient_data.get('severity', 'N/A')}/10"
            )

        with h2:

            st.write("**Assessment information**")

            st.metric(
                "Suggested urgency",
                assessment_data.get("urgency_level", "N/A")
            )

            st.write(
                assessment_data.get("summary", "")
            )

        history_tab1, history_tab2, history_tab3 = st.tabs([
            "Saved guidance",
            "Assessment details",
            "Patient details"
        ])

        with history_tab1:

            st.write(
                selected_session.get(
                    "narrative",
                    "No saved narrative."
                )
            )

        with history_tab2:

            st.json(assessment_data)

        with history_tab3:

            st.json(patient_data)

        # -------------------------------------------------
        # DOWNLOAD PREVIOUS SESSION
        # -------------------------------------------------

        st.download_button(
            "Download previous session JSON",
            data=json.dumps(
                {
                    "session_id": selected_session["id"],
                    "created_at": selected_session["created_at"],
                    "patient": patient_data,
                    "assessment": assessment_data,
                    "narrative": selected_session.get("narrative", "")
                },
                ensure_ascii=False,
                indent=2
            ),
            file_name=f"mediguide_session_{selected_session['id']}.json",
            mime="application/json",
            key=f"download_history_{selected_session['id']}"
        )
                # -------------------------------------------------
        # DOWNLOAD PREVIOUS SESSION PDF
        # -------------------------------------------------

        try:
            history_pdf = build_pdf_report(
                patient=patient_data,
                assessment=assessment_data,
                narrative=selected_session.get("narrative", ""),
                record_id=selected_session["id"]
            )

            st.download_button(
                label="Download Previous Session PDF",
                data=history_pdf,
                file_name=(
                    f"mediguide_session_{selected_session['id']}.pdf"
                ),
                mime="application/pdf",
                key=f"history_pdf_{selected_session['id']}"
            )

        except Exception:
            st.warning(
                "Could not generate the PDF for this saved session."
            )

        # -------------------------------------------------
        # DELETE HISTORY WITH CONFIRMATION
        # -------------------------------------------------

        st.divider()
        st.subheader("History management")

        confirm_delete = st.checkbox(
            "I understand that deleting history permanently removes "
            "all locally saved assessment sessions.",
            key="confirm_delete_history"
        )

        if st.button(
            "Delete all patient history",
            type="secondary",
            disabled=not confirm_delete
        ):

            delete_history()

            st.session_state.pop(
                "history_session_selector",
                None
            )

            st.session_state.pop(
                "confirm_delete_history",
                None
            )

            st.success("Local patient history has been cleared.")
            st.rerun()

except Exception:

    st.error(
        "Unable to load patient history. Please check the database "
        "and its file permissions."
    )


# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------

st.divider()

st.caption(
    "MediGuide AI — educational prototype. "
    "Always seek qualified medical advice."
)
