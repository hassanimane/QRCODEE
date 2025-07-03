import os
import uuid
import socket
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
from werkzeug.utils import secure_filename
import qrcode

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['EVENT_BG_FOLDER'] = 'static/backgrounds'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
app.secret_key = 'your_secret_key'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi', 'webm'}

# Ensure necessary folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['EVENT_BG_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        event_name = request.form['event_name']
        event_date = request.form['event_date']
        event_message = request.form['event_message']
        bg_file = request.files['event_bg']

        event_id = str(uuid.uuid4())
        event_folder = os.path.join(app.config['UPLOAD_FOLDER'], event_id)
        os.makedirs(event_folder, exist_ok=True)

        # Save background image
        bg_filename = None
        if bg_file and allowed_file(bg_file.filename):
            ext = bg_file.filename.rsplit('.', 1)[1].lower()
            bg_filename = f"{event_id}.{ext}"
            bg_file.save(os.path.join(app.config['EVENT_BG_FOLDER'], bg_filename))

        # Save event info
        with open(os.path.join(event_folder, "event_info.txt"), "w", encoding="utf-8") as f:
            f.write(f"{event_name}\n{event_date}\n{event_message}\n{bg_filename or ''}")

        # Generate upload link and QR code
        base_url = "https://qrcodee-1.onrender.com"
        upload_url = base_url + url_for('upload', event_id=event_id)

        qr = qrcode.make(upload_url)
        qr_path = os.path.join(event_folder, 'qr.png')
        qr.save(qr_path)

        return render_template('link.html', upload_url=upload_url, qr_code=url_for('qr_code', event_id=event_id))
    return render_template('index.html')

@app.route('/uploads/<event_id>/qr.png')
def qr_code(event_id):
    return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], event_id), 'qr.png')

@app.route('/album/<event_id>/upload', methods=['GET', 'POST'])
def upload(event_id):
    event_folder = os.path.join(app.config['UPLOAD_FOLDER'], event_id)
    if not os.path.isdir(event_folder):
        flash("Event not found.", "danger")
        return redirect(url_for('index'))

    # Load event info
    with open(os.path.join(event_folder, "event_info.txt"), encoding="utf-8") as f:
        lines = f.read().splitlines()
        event_name, event_date, event_message, bg_filename = (lines + ["", "", "", ""])[:4]

    bg_url = None
    if bg_filename:
        bg_url = url_for('static', filename=f'backgrounds/{bg_filename}')

    if request.method == 'POST':
        files = request.files.getlist('media')
        success = False
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                save_path = os.path.join(event_folder, filename)
                print(f"[UPLOAD DEBUG] Saving file to: {save_path}")
                file.save(save_path)
                file_exists = os.path.exists(save_path)
                print(f"[UPLOAD DEBUG] File saved? {file_exists}")
                success = file_exists
        if success:
            flash("Your files have been uploaded! Thank you.", "success")
        else:
            flash("Invalid file type or no file selected.", "danger")
        return redirect(url_for('upload', event_id=event_id))

    return render_template('upload.html',
                           event_name=event_name,
                           event_date=event_date,
                           event_message=event_message,
                           bg_url=bg_url)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
