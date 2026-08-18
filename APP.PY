import os
import re
import urllib.parse
import urllib.request
from flask import Flask, jsonify, render_template, request, abort

app = Flask(__name__)


def get_vid(query):
    try:
        url = (
            "https://www.youtube.com/results?search_query="
            + urllib.parse.quote(query)
        )

        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        with urllib.request.urlopen(req, timeout=5) as response:
            data = response.read().decode("utf-8", errors="ignore")

        ids = re.findall(r'"videoId":"([^"]+)"', data)
        return ids[0] if ids else None

    except Exception as e:
        print("YouTube Error:", e)
        return None


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/agent", methods=["POST"])
def agent():

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "success": False,
            "message": "Invalid JSON request"
        }), 400

    command = data.get("command") or data.get("text_command")

    if not command:
        return jsonify({
            "success": False,
            "message": "Command is required"
        }), 400

    command = command.strip().lower()

    target = ""
    message = ""

    
    if "youtube" in command:

        query = command

        remove_words = [
            "open youtube and search",
            "open youtube and play",
            "open youtube",
            "and play",
            "play",
            "on youtube"
        ]

        for word in remove_words:
            query = query.replace(word, "")

        query = query.strip()

        if not query:
            return jsonify({
                "success": False,
                "message": "Please enter a YouTube search query"
            }), 400

        video_id = get_vid(query)

        if not video_id:
            return jsonify({
                "success": False,
                "message": "YouTube video not found",
                "url": ""
            }), 404

        target = (
            f"https://www.youtube.com/embed/"
            f"{video_id}?autoplay=1&mute=1"
        )

        message = f"Playing {query}"

    elif any(word in command for word in [
        "gmail",
        "email",
        "mail",
        "message"
    ]):

        clean = re.sub(
            r"^(please\s+)?(open\s+)?"
            r"(gmail|email|mail|message)\s*",
            "",
            command,
            flags=re.IGNORECASE
        ).strip()

        parts = re.split(
            r"\b(type|write|saying|message|content|with body)\b",
            clean,
            maxsplit=1,
            flags=re.IGNORECASE
        )

        recipient = parts[0].strip()
        body = parts[1].strip() if len(parts) > 1 else ""

        recipient = re.sub(
            r"^(to|send to|update to|and update to)\s*",
            "",
            recipient,
            flags=re.IGNORECASE
        ).strip()

        recipient = recipient.replace(" at ", "@")
        recipient = recipient.replace(" dot ", ".")
        recipient = recipient.replace(" underscore ", "_")
        recipient = recipient.replace(" ", "")

        recipient = re.sub(
            r"[^a-zA-Z0-9@._%+-]",
            "",
            recipient
        )

        if recipient and "@" not in recipient:
            recipient += "@gmail.com"

        gmail_url = (
            "https://mail.google.com/mail/u/0/"
            "?view=cm&fs=1&"
            + urllib.parse.urlencode({
                "to": recipient,
                "body": body
            })
        )

        target = gmail_url
        message = f"Drafting email to {recipient}"
    else:

        return jsonify({
            "success": False,
            "message": "Command not supported",
            "url": ""
        }), 400

    return jsonify({
        "success": True,
        "message": message,
        "url": target
    })


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        debug=True
    )
