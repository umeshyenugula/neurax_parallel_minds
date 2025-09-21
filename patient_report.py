import os
import requests
import re

api_key = os.environ.get("GROQ_API_KEY")
url = "https://api.groq.com/openai/v1/chat/completions"

script_dir = os.path.dirname(os.path.abspath(__file__))

def report_generation(report_text) -> tuple:
    """
    Generates English and Telugu patient reports in separate text files.
    Returns paths to the generated files.
    """
    prompt = f"""
    Summarize this kidney report in very simple, easy-to-understand language for a layperson. 
    Then, provide clear and helpful suggestions for the patient, including:
    - Lifestyle tips
    - Diet advice
    - Follow-up actions (like what to ask the doctor)
    Give two sections : 
    1️⃣ English: Start with 'Summary'
    2️⃣ Telugu: Just translate the English text. Do not include any English text.
    Pronounce 'Kidney Stone' and food items clearly in Telugu.
    Report:
    {report_text}
    """

    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}]
    }

    response = requests.post(url, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, json=data)
    res_json = response.json()
    full_text = res_json["choices"][0]["message"]["content"]

    # Clean markdown or extra symbols
    full_text = re.sub(r"\*\*(.*?)\*\*", r"\1", full_text)
    full_text = re.sub(r"#+\s*", "", full_text)
    full_text = re.sub(r"\n\s*\n", "\n", full_text).strip()

    # Split English and Telugu
    if "Telugu:" in full_text:
        english_text, telugu_text = full_text.split("Telugu:", 1)
    else:
        english_text, telugu_text = full_text, ""

    # Save English
    english_file = os.path.join(script_dir, "patient_Report_english.txt")
    with open(english_file, "w", encoding="utf-8") as f:
        f.write(english_text.strip())

    # Save Telugu
    telugu_file = os.path.join(script_dir, "patient_Report_telugu.txt")
    with open(telugu_file, "w", encoding="utf-8") as f:
        f.write(telugu_text.strip())

    return english_file, telugu_file
