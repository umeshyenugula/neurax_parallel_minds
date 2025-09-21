# sppech.py
import asyncio
import edge_tts
import os

async def generate_telugu_audio(report_path="patient_Report_telugu.txt", output_file="static/audio/patient_telugu_report.mp3"):
    """
    Generate Telugu speech from the report file.
    """
    if not os.path.exists(report_path):
        raise FileNotFoundError(f"Report file not found: {report_path}")

    with open(report_path, "r", encoding="utf-8") as f:
        report_text = f.read()

    telugu_text = report_text
    voice = "te-IN-ShrutiNeural"
    output_path = os.path.join('static', 'audio', 'patient_telugu_report.mp3')


    tts = edge_tts.Communicate(telugu_text, voice)
    await tts.save(output_path)
    return output_path

async def generate_english_audio(report_path="patient_Report_english.txt", output_file="static/audio/patient_english_report.mp3"):
    """
    Generate English speech from the report file.
    """
    if not os.path.exists(report_path):
        raise FileNotFoundError(f"Report file not found: {report_path}")

    with open(report_path, "r", encoding="utf-8") as f:
        report_text = f.read()
    english_text = report_text
    voice = "en-US-AriaNeural"
    output_path = os.path.join('static', 'audio', 'patient_english_report.mp3')


    tts = edge_tts.Communicate(english_text, voice)
    await tts.save(output_path)
    return output_path
