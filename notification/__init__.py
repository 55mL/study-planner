# notification\app.py

from flask import Flask, jsonify
from scheduler import start_scheduler

def create_app():
    app = Flask(__name__)

    @app.route("/health")
    def health():
        return jsonify({"status": "ok"})

    return app

app = create_app()

if __name__ == "__main__":
    start_scheduler()
    app.run(host="0.0.0.0", port=8000)