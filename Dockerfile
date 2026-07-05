FROM python:3.12-bookworm

ARG PIPER_MODEL_ONNX_URL
ARG PIPER_MODEL_JSON_URL
ARG PIPER_MODEL_BASENAME

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        espeak-ng=1.51* \
        git=1:2.39* \
        ca-certificates=20230311* \
        curl=7.88* \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN mkdir -p /app/speech/ \
    && git clone --depth 1 https://github.com/asterics/Asterics-AAC-Helper.git /tmp/helper \
    && cp -r /tmp/helper/speech/* /app/speech/ \
    && rm -rf /tmp/helper

WORKDIR /app/speech

RUN pip install --no-cache-dir \
    flask==3.1.3 \
    flask-cors==6.0.5 \
    piper-tts==1.4.2 \
    && mkdir -p /models \
    && curl -fsSL "${PIPER_MODEL_ONNX_URL}" -o "/models/${PIPER_MODEL_BASENAME}.onnx" \
    && curl -fsSL "${PIPER_MODEL_JSON_URL}" -o "/models/${PIPER_MODEL_BASENAME}.onnx.json"

COPY config.py provider_piper_data.py speech_logging.py start_server.py /app/speech/

EXPOSE 5555

VOLUME ["/app/speech/temp"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD ["curl", "-fsS", "http://127.0.0.1:5555/voices/"]

CMD ["python", "start_server.py"]
