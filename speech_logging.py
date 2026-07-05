import logging
import re
import time
from urllib.parse import unquote

import config  # type: ignore[import-not-found]
import speechManager  # type: ignore[import-not-found]
import util  # type: ignore[import-not-found]
from flask import g, request

logger = logging.getLogger("asterics.speech")

_SPEECH_PATH = re.compile(
    r"^/(?P<endpoint>speakdata|speak|cache)/(?P<text>[^/]+)"
    r"(?:/(?P<provider>[^/]+)(?:/(?P<voice>[^/]+))?)?/?$"
)


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


def _parse_speech_path(path: str) -> dict | None:
    match = _SPEECH_PATH.match(path)
    if not match:
        return None
    return {
        "endpoint": match.group("endpoint"),
        "text": unquote(match.group("text")).lower(),
        "provider_id": unquote(match.group("provider") or ""),
        "voice_id": unquote(match.group("voice") or ""),
    }


def patch_speech_manager() -> None:
    def get_speak_data_logged(text, provider_id="", voice_id=None):
        start = time.perf_counter()

        if config.cacheData:
            cached = util.getCacheData(text, provider_id, voice_id)
            if cached:
                elapsed_ms = (time.perf_counter() - start) * 1000
                logger.info(
                    "speak cache=HIT text=%r provider=%r voice=%r bytes=%d elapsed_ms=%.1f",
                    text,
                    provider_id or "(default)",
                    voice_id or "(default)",
                    len(cached),
                    elapsed_ms,
                )
                return cached

        provider = (
            speechManager.speechProviders[provider_id]
            if provider_id in speechManager.speechProviders
            else config.speechProviderList[0]
        )
        if not hasattr(provider, "getSpeakData"):
            logger.error(
                "speak synthesis=FAILED missing getSpeakData provider=%r text=%r",
                provider_id or "(default)",
                text,
            )
            return None

        synth_start = time.perf_counter()
        data = provider.getSpeakData(text, voice_id)
        synth_ms = (time.perf_counter() - synth_start) * 1000
        total_ms = (time.perf_counter() - start) * 1000

        if config.cacheData and data and len(data) > 0:
            util.saveCacheData(text, provider_id, voice_id, data)

        if not data:
            logger.warning(
                "speak cache=%s synthesis=FAILED text=%r provider=%r voice=%r synth_ms=%.1f total_ms=%.1f",
                "MISS" if config.cacheData else "disabled",
                text,
                provider_id or "(default)",
                voice_id or "(default)",
                synth_ms,
                total_ms,
            )
            return data

        logger.info(
            "speak cache=%s synthesis=OK text=%r provider=%r voice=%r bytes=%d synth_ms=%.1f total_ms=%.1f",
            "MISS" if config.cacheData else "disabled",
            text,
            provider_id or "(default)",
            voice_id or "(default)",
            len(data),
            synth_ms,
            total_ms,
        )
        return data

    speechManager.getSpeakData = get_speak_data_logged


def install_request_logging(app) -> None:
    @app.before_request
    def _start_request_timer():
        g.request_started_at = time.perf_counter()

    @app.after_request
    def _log_request(response):
        elapsed_ms = (time.perf_counter() - g.request_started_at) * 1000
        speech = _parse_speech_path(request.path)

        if speech:
            logger.info(
                "request %s %s endpoint=%s text=%r provider=%r voice=%r status=%s elapsed_ms=%.1f",
                request.method,
                request.path,
                speech["endpoint"],
                speech["text"],
                speech["provider_id"] or "(default)",
                speech["voice_id"] or "(default)",
                response.status_code,
                elapsed_ms,
            )
        else:
            logger.info(
                "request %s %s status=%s elapsed_ms=%.1f",
                request.method,
                request.path,
                response.status_code,
                elapsed_ms,
            )

        return response
