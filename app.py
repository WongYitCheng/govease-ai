from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
from guardian_agent import add_watermark
import os

app = Flask(__name__)
CORS(app)

app.config["UPLOAD_FOLDER"] = "uploads"

# 创建 uploads 文件夹（如果不存在）
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# 临时存储水印文件路径
user_data = {}


@app.route("/")
def index():
    """Serve the chat interface"""
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    """Handle chat messages and file uploads"""
    message = request.form.get("message", "")
    file = request.files.get("file")
    portal = request.form.get("portal", "LHDN")

    # ========== 文件上传路径 ==========
    if file and file.filename:
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(filepath)
        print(f"[DEBUG] File saved: {filepath}")

        try:
            from concierge_agent import extract_document_data, update_user_data
            
            extracted = extract_document_data(filepath)
            print(f"[DEBUG] Extracted data: {extracted}")
            update_user_data(extracted)
            
            watermarked_path = add_watermark(filepath, portal)
            user_data["watermarked_path"] = watermarked_path
            
            reply = f"""✅ Document received and protected!

📛 Name: {extracted.get('full_name', 'Not found')}
🆔 IC Number: {extracted.get('ic_number', 'Not found')}
📍 Address: {extracted.get('address', 'Not found')}
🎂 Date of Birth: {extracted.get('date_of_birth', 'Not found')}

🔒 Watermark applied: FOR {portal} USE ONLY
✅ Your data is saved securely.

✨ Click 'Send Data to Browser Extension' to start auto-filling forms!"""

            return jsonify({
                "reply": reply,
                "extracted": extracted,
                "status": "success"
            })

        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({
                "reply": f"❌ Sorry, I had trouble reading that document. Error: {str(e)}",
                "status": "error"
            })

    # ========== 文本消息路径 ==========
    else:
        try:
            from concierge_agent import extract_from_text, chat_response, update_user_data
            
            extracted = extract_from_text(message)
            if any(extracted.values()):
                update_user_data(extracted)
            
            reply = chat_response(message)
            
            return jsonify({
                "reply": reply,
                "status": "success"
            })

        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({
                "reply": f"❌ Error: {str(e)}",
                "status": "error"
            })


@app.route("/upload-and-watermark", methods=["POST"])
def upload_and_watermark():
    """上传图片并添加水印"""
    file = request.files.get("file")
    portal = request.form.get("portal", "LHDN")
    
    if not file:
        return jsonify({"error": "No file uploaded"}), 400
    
    # 保存原文件
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(filepath)
    print(f"[DEBUG] File saved for watermark: {filepath}")
    
    # 检查文件类型
    file_ext = file.filename.split('.')[-1].lower()
    
    if file_ext in ['jpg', 'jpeg', 'png']:
        from guardian_agent import add_watermark
        watermarked_path = add_watermark(filepath, portal)
    else:
        watermarked_path = filepath
        print(f"[INFO] Non-image file saved: {filepath}")
    
    return jsonify({
        "status": "success",
        "original": filepath,
        "watermarked": watermarked_path,
        "portal": portal,
        "filename": file.filename
    })


@app.route("/get-data", methods=["GET"])
def get_data():
    """Return all collected user data"""
    from concierge_agent import get_user_data
    return jsonify(get_user_data())


@app.route("/download/<filename>", methods=["GET"])
def download_file(filename):
    """下载文件"""
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    return jsonify({"error": "File not found"}), 404


@app.route("/download-watermarked", methods=["GET"])
def download_watermarked():
    """Download the watermarked document"""
    path = user_data.get("watermarked_path")
    if path and os.path.exists(path):
        return send_file(path, as_attachment=True)
    return jsonify({"error": "No watermarked file found"}), 404


@app.route("/clear-data", methods=["POST"])
def clear_data():
    """Clear all stored user data"""
    from concierge_agent import clear_user_data
    clear_user_data()
    user_data.clear()
    return jsonify({"status": "cleared"})


@app.route("/reset", methods=["POST"])
def reset():
    """Reset conversation and clear data"""
    from concierge_agent import clear_user_data, reset_conversation
    clear_user_data()
    reset_conversation()
    user_data.clear()
    return jsonify({"status": "reset"})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"})


if __name__ == "__main__":
    print("\n" + "="*50)
    print("🚀 GovEase AI Server Running")
    print("📍 http://127.0.0.1:5000")
    print("="*50 + "\n")
    app.run(debug=True, host="127.0.0.1", port=5000)