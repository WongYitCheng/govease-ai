from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS 
from guardian_agent import add_watermark
import os
import json

app = Flask(__name__)
CORS(app)

app.config["UPLOAD_FOLDER"] = "uploads"

user_data = {}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    message = request.form.get("message", "")
    file = request.files.get("file")
    portal = request.form.get("portal", "LHDN")

    # ── FILE UPLOAD PATH ──────────────────────────────────────
    if file and file.filename:
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(filepath)

        try:
            from concierge_agent import extract_document_data
            extracted = extract_document_data(filepath)
            user_data.update(extracted)

            # Apply watermark
            watermarked = add_watermark(filepath, portal)
            user_data["watermarked_path"] = watermarked

            reply = f"""Document received and protected! ✅

Name: {extracted.get('full_name', 'Not found')}
IC Number: {extracted.get('ic_number', 'Not found')}
Address: {extracted.get('address', 'Not found')}
Date of Birth: {extracted.get('date_of_birth', 'Not found')}
Confidence: {extracted.get('confidence', 'unknown')}

Watermark applied: FOR {portal} USE ONLY 🔒
Your data is saved securely on your device."""

            return jsonify({
                "reply": reply,
                "extracted": extracted,
                "status": "success"
            })

        except Exception as e:
            return jsonify({
                "reply": f"Sorry, I had trouble reading that document. Error: {str(e)}",
                "status": "error"
            })

    # ── TEXT MESSAGE PATH ─────────────────────────────────────
    else:
        try:
            from concierge_agent import extract_from_text, chat_response

            # Keywords that suggest user is sharing personal info
            keywords = [
                "ic", "name", "address", "nama", "ic number",
                "my name", "i am", "990", "880", "970", "800",
                "jalan", "kl", "kuala lumpur", "selangor",
                "salary", "income", "gaji", "employer"
            ]

            if any(kw in message.lower() for kw in keywords):
                # Extract structured data from typed text
                extracted = extract_from_text(message)
                user_data.update(extracted)

                reply = f"""Got your details! Here is what I extracted: ✅

Name: {extracted.get('full_name', 'Not found')}
IC Number: {extracted.get('ic_number', 'Not found')}
Address: {extracted.get('address', 'Not found')}
Date of Birth: {extracted.get('date_of_birth', 'Not found')}
Monthly Income: {extracted.get('monthly_income', 'Not found')}
Confidence: {extracted.get('confidence', 'unknown')}

Your data is saved and ready for form filling!
Open any government portal and click the GovEase button. 🚀"""

                return jsonify({
                    "reply": reply,
                    "extracted": extracted,
                    "status": "success"
                })

            else:
                # Normal conversation
                reply = chat_response(message)
                return jsonify({
                    "reply": reply,
                    "status": "success"
                })

        except Exception as e:
            return jsonify({
                "reply": f"Error: {str(e)}",
                "status": "error"
            })


@app.route("/get-data")
def get_data():
    return jsonify(user_data)


@app.route("/download-watermarked")
def download_watermarked():
    portal = request.args.get("portal", "LHDN")
    path = user_data.get("watermarked_path")
    if path and os.path.exists(path):
        return send_file(path, as_attachment=True)
    return jsonify({"error": "No watermarked file found"}), 404


@app.route("/clear-data", methods=["POST"])
def clear_data():
    user_data.clear()
    return jsonify({"status": "cleared"})


if __name__ == "__main__":
    app.run(debug=True)