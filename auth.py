"""Session-based OpenAI API-key validation for the Streamlit application."""

import streamlit as st
from openai import APIConnectionError, AuthenticationError, OpenAI, OpenAIError, RateLimitError

SESSION_KEY = "mediguide_openai_api_key"


def validate_api_key(api_key: str) -> tuple[bool, str]:
    """Validate a key by making an authenticated, non-generation API request."""
    candidate = api_key.strip()
    if not candidate:
        return False, "Please enter your OpenAI API key."

    try:
        # Listing models verifies authentication without generating a completion.
        client = OpenAI(api_key=candidate, timeout=15.0, max_retries=0)
        client.models.list()
        return True, "API key validated successfully."
    except AuthenticationError:
        return False, "The API key was rejected. Check it and try again."
    except RateLimitError:
        return False, "OpenAI rate-limited the validation request. Please wait and try again."
    except APIConnectionError:
        return False, "Could not connect to OpenAI. Check your internet connection and retry."
    except OpenAIError:
        return False, "OpenAI could not validate this key. Check its permissions and try again."
    except Exception:
        # Do not display exception details; they may contain request metadata.
        return False, "Validation failed unexpectedly. Please try again."


def render_login() -> None:
    """Render the login gate. The key is never written to disk by this app."""
    st.title("🩺 MediGuide AI")
    st.caption("Secure access — validate your OpenAI API key to continue.")
    st.info(
        "Your API key is used only for this Streamlit session. This application "
        "does not save it in a source file or .env file. Do not share your key."
    )

    with st.form("api_key_login", clear_on_submit=False):
        api_key = st.text_input(
            "OpenAI API key",
            type="password",
            key="api_key_input",
            placeholder="Paste your OpenAI API key",
            help="The key is sent to OpenAI for validation and kept in session memory after validation.",
        )
        submitted = st.form_submit_button("Validate key and continue", type="primary", use_container_width=True)

    if submitted:
        with st.spinner("Validating your API key with OpenAI..."):
            valid, message = validate_api_key(api_key)
        if valid:
            st.session_state[SESSION_KEY] = api_key.strip()
            st.success(message)
            st.rerun()
        else:
            st.error(message)

    st.caption("For security, log out when you finish using MediGuide AI.")
