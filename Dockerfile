FROM python:3.12-bookworm

ARG AAC_HELPER_COMMIT=8b04af51bd0d0b99895327000122062e3b9c0276
ARG VERSION=dev
ARG PIPER_MODEL_ONNX_URL
ARG PIPER_MODEL_JSON_URL
ARG PIPER_MODEL_BASENAME

LABEL org.opencontainers.image.title="Asterics Speech" \
    org.opencontainers.image.source="https://github.com/Jubblin/Asterics-Speech" \
    org.opencontainers.image.version="${VERSION}"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        espeak-ng=1.51* \
        git=1:2.39* \
        ca-certificates=20230311* \
        curl=7.88* \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN mkdir -p /app/speech/ /tmp/helper

WORKDIR /tmp/helper

RUN git init . \
    && git remote add origin https://github.com/asterics/Asterics-AAC-Helper.git \
    && git fetch --depth 1 origin "${AAC_HELPER_COMMIT}" \
    && git checkout FETCH_HEAD \
    && cp -r speech/* /app/speech/ \
    && rm -rf /tmp/helper

WORKDIR /app/speech

RUN pip install --no-cache-dir \
    flask==3.1.3 \
    flask-cors==6.0.5 \
    piper-tts==1.4.2 \
    && mkdir -p /models \
    && curl -fsSL "${PIPER_MODEL_ONNX_URL}" -o "/models/${PIPER_MODEL_BASENAME}.onnx" \
    && curl -fsSL "${PIPER_MODEL_JSON_URL}" -o "/models/${PIPER_MODEL_BASENAME}.onnx.json"

COPY VERSION version.py config.py log_redaction.py provider_piper_data.py speech_logging.py start_server.py /app/speech/

ENV ASTERICS_SPEECH_VERSION=${VERSION}

EXPOSE 5555

VOLUME ["/app/speech/temp"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD ["curl", "-fsS", "http://127.0.0.1:5555/voices/"]

CMD ["python", "start_server.py"]
