from flask import Flask, request, jsonify, send_file
from flask_cors import CORS 
import os
import subprocess
from pydub import AudioSegment
import whisper
from gtts import gTTS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts.prompt import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app) 
app.config['UPLOAD_FOLDER'] = './uploads'
app.config['OUTPUT_FOLDER'] = './output_videos'


os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

def extract_audio(video_path, audio_output_path):
    command = ['ffmpeg','-y', '-i', video_path, '-q:a', '0', '-map', 'a', audio_output_path]
    subprocess.run(command)

def transcribe_audio(audio_path):
    model = whisper.load_model("base")
    result = model.transcribe(audio_path)
    return result['text']

def translate_text(text, target_language):
    prompt = """ "{sentence}" translate this sentence into {language}. Provide only the translated sentence without additional explanation."""
    prompt_template = PromptTemplate(input_variables=["language", "sentence"], template=prompt)
    llm = ChatGoogleGenerativeAI(model='gemini-1.5-flash')
    chain = prompt_template | llm | StrOutputParser()
    res = chain.invoke({"language": target_language, "sentence": text})
    return res

def text_to_speech(text, output_mp3_path, language='en'):
    tts = gTTS(text=text, lang=language)
    tts.save(output_mp3_path)

def adjust_audio_length(input_audio_path, target_audio_path, output_audio_path):
    input_duration = len(AudioSegment.from_file(input_audio_path)) / 1000.0
    target_duration = len(AudioSegment.from_file(target_audio_path)) / 1000.0
    speed_change_factor = input_duration / target_duration
    if abs(speed_change_factor - 1) < 0.01:
        AudioSegment.from_file(input_audio_path).export(output_audio_path, format="mp3")
        return
    subprocess.run(["ffmpeg", "-y", "-i", input_audio_path, "-filter:a", f"atempo={speed_change_factor:.2f}", "-vn", output_audio_path])

def replace_audio(video_path, audio_path, output_video_path):
    command = ['ffmpeg', '-y', '-i', video_path, '-i', audio_path, '-c:v', 'copy', '-c:a', 'aac', '-map', '0:v:0', '-map', '1:a:0', output_video_path]
    subprocess.run(command)

@app.route('/upload', methods=['POST'])
def process_video():
    file = request.files['video']
    language = request.form['language']
    
    if file:
        video_filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(video_filename)

        audio_path = './uploads/extracted_audio.mp3'
        extract_audio(video_filename, audio_path)

        transcribed_text = transcribe_audio(audio_path)
        translated_text = translate_text(transcribed_text, language)
        
        translated_audio_path = './uploads/translated_audio.mp3'
        text_to_speech(translated_text, translated_audio_path)
        
        adjusted_audio_path = './uploads/adjusted_audio.mp3'
        adjust_audio_length(translated_audio_path, audio_path, adjusted_audio_path)

        output_video_path = os.path.abspath("./output_videos/translated_video.mp4")

        replace_audio(video_filename, adjusted_audio_path, output_video_path)
        
        filename = os.path.basename(output_video_path)
        return jsonify({"output_video": filename})

    return jsonify({"error": "No file uploaded"}), 400

@app.route('/download/<path:filename>', methods=['GET'])
def download_video(filename):
    return send_file(filename, as_attachment=True)

@app.route('/output_videos/<filename>', methods=['GET'])
def serve_video(filename):
    video_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    if os.path.exists(video_path):
        return send_file(video_path)
    return jsonify({"error": "File not found"}), 404


if __name__ == '__main__':
    app.run(debug=True)
