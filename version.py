import os
from pathlib import Path

_VERSION_FILE = Path(__file__).with_name("VERSION")


def get_version() -> str:
    if _VERSION_FILE.is_file():
        return _VERSION_FILE.read_text(encoding="utf-8").strip()
    return os.environ.get("ASTERICS_SPEECH_VERSION", "dev")
