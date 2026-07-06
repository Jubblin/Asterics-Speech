import hashlib
import logging
import os

_log_speech_text = False


def configure_log_redaction() -> None:
    global _log_speech_text
    _log_speech_text = os.environ.get("SPEECH_LOG_TEXT", "").lower() in (
        "1",
        "true",
        "yes",
    )


def format_speech_text(text: str, logger: logging.Logger | None = None) -> str:
    if _log_speech_text or (logger is not None and logger.isEnabledFor(logging.DEBUG)):
        return repr(text)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
    return f"hash={digest} len={len(text)}"
