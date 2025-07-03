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
