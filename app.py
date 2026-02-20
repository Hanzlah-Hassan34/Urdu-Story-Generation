"""HTTP REST API for trigram story generation (Render-compatible)"""

import json
import os
import sys
from flask import Flask, request, Response, jsonify

sys.stdout.reconfigure(encoding="utf-8")

# Import generation logic from server
from server import initialize_model, generate_story

app = Flask(__name__)

# Token replacement: EOS->full stop, EOP->newline, EOT->full stop
def format_output(text):
    return (text
        .replace("<EOS>", "۔")   # Urdu full stop
        .replace("<EOP>", "\n")
        .replace("<EOT>", "۔"))

@app.route("/")
def health():
    return jsonify({"status": "ok", "service": "urdu-story-api"}), 200

@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json() or {}
    prefix = data.get("prefix", "")
    max_length = int(data.get("maxLength", 500))

    def stream():
        for chunk in generate_story(prefix=prefix, max_length=max_length):
            formatted = format_output(chunk)
            is_final = chunk.endswith("<EOT>") or len(chunk.split()) >= max_length
            payload = json.dumps({"chunk": formatted, "isFinal": is_final, "numTokens": len(chunk.split())})
            yield f"data: {payload}\n\n"
            if is_final:
                break

    return Response(
        stream(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )

if __name__ == "__main__":
    if not initialize_model():
        sys.exit(1)
    port = int(os.environ.get("PORT", 50051))
    print(f"[✓] HTTP API listening on port {port}")
    app.run(host="0.0.0.0", port=port)
