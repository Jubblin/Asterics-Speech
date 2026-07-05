import logging
import os
import subprocess
import time

import constants  # type: ignore[import-not-found]
import util  # type: ignore[import-not-found]

logger = logging.getLogger("asterics.speech.piper")

providerId = os.environ["PIPER_PROVIDER_ID"]


def get_provider_id():
    return providerId


getProviderId = get_provider_id


def get_voice_type():
    return constants.VOICE_TYPE_EXTERNAL_DATA


getVoiceType = get_voice_type


def get_voices():
    return [
        {
            "id": os.environ["PIPER_VOICE_ID"],
            "name": os.environ["PIPER_VOICE_NAME"],
            "lang": os.environ["PIPER_VOICE_LANG"],
        }
    ]


getVoices = get_voices


def get_speak_data(text, _voice_id=None):
    start = time.perf_counter()
    path = util.getTempFileFullPath(providerId)
    result = subprocess.run(
        ["piper", "--model", os.environ["PIPER_MODEL"], "--output_file", path],
        input=text,
        text=True,
        capture_output=True,
    )
    elapsed_ms = (time.perf_counter() - start) * 1000
    if result.returncode != 0:
        logger.error(
            "piper failed text=%r elapsed_ms=%.1f stderr=%s",
            text,
            elapsed_ms,
            result.stderr.strip(),
        )
        return b""
    data = util.getTempFileData(providerId)
    logger.info(
        "piper synthesized text=%r bytes=%d elapsed_ms=%.1f",
        text,
        len(data),
        elapsed_ms,
    )
    return data


getSpeakData = get_speak_data
