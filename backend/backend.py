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
import pysrt
from pysrt import SubRipFile, SubRipItem, SubRipTime
from datetime import timedelta

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
    return result

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

def create_subtitle_file(transcribed_segments, language, output_srt_path):
    """
    Generate a subtitle file (.srt) with translated captions.
    """
    subs = SubRipFile()

    for idx, segment in enumerate(transcribed_segments):
        # Convert timedelta to SubRipTime
        start_time = timedelta_to_subrip_time(timedelta(seconds=segment['start']))
        end_time = timedelta_to_subrip_time(timedelta(seconds=segment['end']))
        text = segment['text']  # Use original transcribed text

        # If the selected language is not English, translate the text
        text = translate_text(segment['text'], language)

        subtitle = SubRipItem(index=idx + 1, start=start_time, end=end_time, text=text)
        subs.append(subtitle)

    subs.save(output_srt_path, encoding='utf-8')


def timedelta_to_subrip_time(td):
    """
    Convert a timedelta object to a SubRipTime instance.
    """
    total_seconds = int(td.total_seconds())
    milliseconds = int((td.total_seconds() - total_seconds) * 1000)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return SubRipTime(hours=hours, minutes=minutes, seconds=seconds, milliseconds=milliseconds)


def embed_subtitles(video_path, subtitle_path, output_path):
    """
    Embed subtitles (.srt) into the video using FFmpeg.
    """
    command = [
        'ffmpeg', '-y', '-i', video_path, '-vf',
        f"subtitles={subtitle_path}:force_style='FontSize=24,PrimaryColour=&HFFFFFF&'",
        '-c:a', 'copy', output_path
    ]
    subprocess.run(command, check=True)

@app.route('/upload', methods=['POST'])
def process_video():
    file = request.files['video']
    language = request.form['language']  # Language for translation
    caption_option = request.form['caption_option']  # Captions option (none, translated, or language code)

    if file:
        video_filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(video_filename)

        # Step 1: Extract audio
        audio_path = './uploads/extracted_audio.mp3'
        extract_audio(video_filename, audio_path)

        # Step 2: Transcribe audio
        transcribed_data = whisper.load_model("base").transcribe(audio_path)

        # Step 3: Translate text (if needed)
        transcribed_text = transcribed_data['text']
        translated_text = translate_text(transcribed_text, language)  # Translate text to the target language

        # Step 4: Create SRT file based on caption option
        srt_path = './uploads/captions.srt'
        if caption_option == "none":
            # No captions requested, skip subtitle generation
            pass
        elif caption_option == "translated":
            # Generate captions in the translated language (use the translation you already did)
            create_subtitle_file(transcribed_data['segments'], language, srt_path)
        else:
            # Generate captions in the selected language (language code, e.g., "en")
            create_subtitle_file(transcribed_data['segments'], caption_option, srt_path)

        # Step 5: Generate translated audio
        translated_audio_path = './uploads/translated_audio.mp3'
        text_to_speech(translated_text, translated_audio_path, language)

        # Step 6: Adjust audio length
        adjusted_audio_path = './uploads/adjusted_audio.mp3'
        adjust_audio_length(translated_audio_path, audio_path, adjusted_audio_path)

        # Step 7: Replace audio in the video
        temp_video_path = './output_videos/temp_video.mp4'
        replace_audio(video_filename, adjusted_audio_path, temp_video_path)

        # Step 8: Embed subtitles into the video (if captions are selected)
        final_video_path = os.path.abspath("./output_videos/translated_with_captions.mp4")
        if caption_option != "none":
            embed_subtitles(temp_video_path, srt_path, final_video_path)

        # Return the translated video with captions
        filename = os.path.basename(final_video_path)
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


