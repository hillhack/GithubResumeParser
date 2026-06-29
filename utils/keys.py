import contextvars

# Thread-safe, context-local storage for API keys.
# This prevents keys from leaking across different users' Streamlit sessions.
api_keys_ctx = contextvars.ContextVar("api_keys", default={})
