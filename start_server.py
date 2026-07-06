#!/usr/bin/env python3
import os

import speech_logging
import version
from flask import jsonify
from start import app

speech_logging.configure_logging(os.environ.get("SPEECH_LOG_LEVEL", "INFO"))
speech_logging.patch_speech_manager()
speech_logging.install_request_logging(app)


@app.route("/version/")
def speech_version():
    return jsonify({"version": version.get_version()})


if __name__ == "__main__":
    host = os.environ["SPEECH_HOST"]
    port = int(os.environ["SPEECH_PORT"])
    app.run(host=host, port=port, threaded=True)
