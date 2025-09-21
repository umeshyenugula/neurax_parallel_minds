import os
import requests
import re
import json

api_key = os.environ.get("GROQ_API_KEY")
url = "https://api.groq.com/openai/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

script_dir = os.path.dirname(os.path.abspath(__file__))

def report_generation(report_text: str, patient_id: str) -> None:
    prompt = f"""
    Summarize this kidney report in very simple, easy-to-understand language for a layperson. 
    Then, provide clear and helpful suggestions for the patient, including:
    - Lifestyle tips
    - Diet advice
    - Follow-up actions (like what to ask the doctor)

    Give two sections: 
    1. One for English — Start with 'Summary' 
    2. One for Telugu — Translate everything from English, do not change content

    Pronounce 'Kidney Stone', food items clearly in Telugu.
    Do not include any English text in Telugu.

    Generate it as if you're talking directly to the patient.

    Report:
    {report_text}
    """

    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}]
    }

    response = requests.post(url, headers=headers, json=data)
    res_json = response.json()
    text = res_json["choices"][0]["message"]["content"]

    # Clean markdown artifacts
    text_clean = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text_clean = re.sub(r"#+\s*", "", text_clean)
    text_clean = re.sub(r"\n\s*\n", "\n", text_clean)

    # Save to: KD12345_report.txt
    filename = f"{patient_id}_report.txt"
    file_path = os.path.join(script_dir, filename)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(text_clean)
