
from flask import Flask, request, jsonify, send_file, render_template_string
import os
import whisper
from werkzeug.utils import secure_filename
from datetime import timedelta
from docx import Document
from fpdf import FPDF

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

model = whisper.load_model("base")
latest_transcript = ""  # Global metin saklama

@app.route('/')
def index():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.route('/transcribe', methods=['POST'])
def transcribe():
    global latest_transcript

    if 'file' not in request.files:
        return jsonify({'error': 'Dosya bulunamadı'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Dosya seçilmedi'}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    result = model.transcribe(filepath, word_timestamps=True)

    transcript = []
    for segment in result['segments']:
        start_time = str(timedelta(seconds=int(segment['start'])))
        speaker = "Konuşmacı 1"
        text = segment['text'].strip()
        transcript.append(f"[{start_time}] {speaker}: {text}")

    latest_transcript = "\n".join(transcript)
    return jsonify({'transcript': latest_transcript})

@app.route('/download/<format>', methods=['GET'])
def download(format):
    global latest_transcript
    if not latest_transcript:
        return "Henüz metin yok.", 400

    if format == "pdf":
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("Arial", size=12)
        for line in latest_transcript.split("\n"):
            pdf.multi_cell(0, 10, line)
        pdf_path = "transcript.pdf"
        pdf.output(pdf_path)
        return send_file(pdf_path, as_attachment=True)

    elif format == "word":
        doc = Document()
        for line in latest_transcript.split("\n"):
            doc.add_paragraph(line)
        doc_path = "transcript.docx"
        doc.save(doc_path)
        return send_file(doc_path, as_attachment=True)

    return "Desteklenmeyen format", 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
