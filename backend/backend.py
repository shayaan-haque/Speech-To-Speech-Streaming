from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import subprocess
from pydub import AudioSegment
import whisper
import edge_tts
import asyncio
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

LANGUAGE_TO_VOICE = {
    # Arabic
    "ar": "ar-EG-ShakirNeural",  # Egyptian Arabic
        
    # Chinese
    "zh": {
        "default": "zh-CN-YunxiNeural",  # Male voice
        "alternatives": [
            "zh-CN-XiaoxiaoNeural",      # Female voice
            "zh-CN-YunyangNeural",       # Male voice
            "zh-TW-HsiaoChenNeural"      # Taiwanese Mandarin
        ]
    },
    
    # Dutch
    "nl": "nl-NL-MaartenNeural",
    
    # English
    "en": {
        "default": "en-US-EricNeural",   # Male voice
        "alternatives": [
            "en-US-JennyNeural",         # Female voice
            "en-GB-RyanNeural",          # British Male
            "en-GB-SoniaNeural",         # British Female
            "en-AU-NatashaNeural"        # Australian Female
        ]
    },
    
    # French
    "fr": {
        "default": "fr-FR-HenriNeural",
        "alternatives": [
            "fr-FR-DeniseNeural",
            "fr-CA-SylvieNeural"         # Canadian French
        ]
    },
    
    # German
    "de": {
        "default": "de-DE-ConradNeural",
        "alternatives": [
            "de-DE-KatjaNeural",
            "de-AT-JonasNeural"          # Austrian German
        ]
    },
    
    # Greek
    "el": "el-GR-AthanasiosNeural",
    
    # Gujarati
    "gu": "gu-IN-NiranjanNeural",
    
    # Hindi
    "hi": {
        "default": "hi-IN-MadhurNeural",
        "alternatives": ["hi-IN-SwaraNeural"]
    },
    
    # Italian
    "it": {
        "default": "it-IT-DiegoNeural",
        "alternatives": ["it-IT-ElsaNeural"]
    },
    
    # Japanese
    "ja": {
        "default": "ja-JP-KeitaNeural",
        "alternatives": ["ja-JP-NanamiNeural"]
    },
    
    # Korean
    "ko": {
        "default": "ko-KR-InJoonNeural",
        "alternatives": ["ko-KR-SunHiNeural"]
    },
    
    
    # Marathi
    "mr": "mr-IN-AarohiNeural",
    
    # Polish
    "pl": {
        "default": "pl-PL-MarekNeural",
        "alternatives": ["pl-PL-ZofiaNeural"]
    },
    
    # Portuguese
    "pt": {
        "default": "pt-BR-AntonioNeural",  # Brazilian
        "alternatives": [
            "pt-BR-FranciscaNeural",       # Brazilian
            "pt-PT-DuarteNeural",          # European
            "pt-PT-RaquelNeural"           # European
        ]
    },
        
    # Russian
    "ru": {
        "default": "ru-RU-DmitryNeural",
        "alternatives": ["ru-RU-SvetlanaNeural"]
    },
    
    # Spanish
    "es": {
        "default": "es-ES-AlvaroNeural",   # Spain
        "alternatives": [
            "es-ES-ElviraNeural",          # Spain
            "es-MX-JorgeNeural",           # Mexican
            "es-AR-TomasNeural"            # Argentinian
        ]
    },
    
    # Swedish
    "sv": {
        "default": "sv-SE-MattiasNeural",
        "alternatives": ["sv-SE-SofieNeural"]
    },
    
    # Tamil
    "ta": "ta-IN-ValluvarNeural",
    
    # Telugu
    "te": "te-IN-MohanNeural",
    
    # Thai
    "th": {
        "default": "th-TH-NiwatNeural",
        "alternatives": ["th-TH-PremwadeeNeural"]
    },
    
    # Turkish
    "tr": {
        "default": "tr-TR-AhmetNeural",
        "alternatives": ["tr-TR-EmelNeural"]
    },
    
    # Urdu
    "ur": {
        "default": "ur-PK-AsadNeural",
        "alternatives": ["ur-PK-UzmaNeural"]
    }
}

# Helper function to get voice for a language
def get_voice(language_code, prefer_female=False):
    voice_data = LANGUAGE_TO_VOICE.get(language_code)
    
    if voice_data is None:
        return None
    
    if isinstance(voice_data, str):
        return voice_data
    
    if prefer_female and "alternatives" in voice_data:
        # Try to find a female voice (usually contains "Female" or female names)
        female_voices = [v for v in voice_data["alternatives"] if any(female_indicator in v for female_indicator in ["Female", "Neural", "Elvira", "Jenny", "Sonia", "Natasha"])]
        if female_voices:
            return female_voices[0]
    
    return voice_data["default"]

async def text_to_speech(text, output_mp3_path, language='en'):
    """
    Convert text to speech using Edge TTS
    """
    try:
        # Get voice using the new mapping
        voice_data = LANGUAGE_TO_VOICE.get(language)
        
        # Handle unsupported languages
        if voice_data is None:
            print(f"Language {language} not supported, falling back to English")
            voice = LANGUAGE_TO_VOICE['en']['default']
        # If it's a simple string voice ID
        elif isinstance(voice_data, str):
            voice = voice_data
        # If it's a dictionary with default and alternatives
        else:
            voice = voice_data['default']
        
        # Create communicate object and save
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_mp3_path)
        
    except Exception as e:
        print(f"Error in text_to_speech: {str(e)}")
        raise

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
    subs = SubRipFile()
    for idx, segment in enumerate(transcribed_segments):
        start_time = timedelta_to_subrip_time(timedelta(seconds=segment['start']))
        end_time = timedelta_to_subrip_time(timedelta(seconds=segment['end']))
        text = translate_text(segment['text'], language)
        subtitle = SubRipItem(index=idx + 1, start=start_time, end=end_time, text=text)
        subs.append(subtitle)
    subs.save(output_srt_path, encoding='utf-8')

def timedelta_to_subrip_time(td):
    total_seconds = int(td.total_seconds())
    milliseconds = int((td.total_seconds() - total_seconds) * 1000)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return SubRipTime(hours=hours, minutes=minutes, seconds=seconds, milliseconds=milliseconds)

def embed_subtitles(video_path, subtitle_path, output_path):
    command = [
        'ffmpeg', '-y', '-i', video_path, '-vf',
        f"subtitles={subtitle_path}:force_style='FontSize=24,PrimaryColour=&HFFFFFF&'",
        '-c:a', 'copy', output_path
    ]
    subprocess.run(command, check=True)

def generate_summary(text):
    prompt = """Please summarize the following text: "{text}". Keep the summary concise and clear."""
    prompt_template = PromptTemplate(input_variables=["text"], template=prompt)
    llm = ChatGoogleGenerativeAI(model='gemini-1.5-flash')
    chain = prompt_template | llm | StrOutputParser()
    summary = chain.invoke({"text": text})
    return summary

@app.route('/upload', methods=['POST'])
async def process_video():
    file = request.files['video']
    language = request.form['language']
    caption_option = request.form['caption_option']
    
    if file:
        video_filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(video_filename)
        
        audio_path = './uploads/extracted_audio.mp3'
        extract_audio(video_filename, audio_path)
        
        transcribed_data = whisper.load_model("base").transcribe(audio_path)
        summary = generate_summary(transcribed_data['text'])
        
        transcribed_text = transcribed_data['text']
        translated_text = translate_text(transcribed_text, language)
        
        srt_path = './uploads/captions.srt'
        if caption_option != "none":
            create_subtitle_file(transcribed_data['segments'], language if caption_option == "translated" else caption_option, srt_path)
        
        translated_audio_path = './uploads/translated_audio.mp3'
        await text_to_speech(translated_text, translated_audio_path, language)
        
        adjusted_audio_path = './uploads/adjusted_audio.mp3'
        adjust_audio_length(translated_audio_path, audio_path, adjusted_audio_path)
        
        temp_video_path = './output_videos/temp_video.mp4'
        replace_audio(video_filename, adjusted_audio_path, temp_video_path)
        
        final_video_path = os.path.abspath("./output_videos/translated_with_captions.mp4")
        if caption_option != "none":
            embed_subtitles(temp_video_path, srt_path, final_video_path)
        else:
            os.rename(temp_video_path, final_video_path)
        
        filename = os.path.basename(final_video_path)
        return jsonify({
            "output_video": filename,
            "summary": summary,
            "transcription": translated_text
        })
    
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