import os
import requests
import json
import re

# Environment + API setup
api_key = os.environ.get("GROQ_API_KEY")
url = "https://api.groq.com/openai/v1/chat/completions"
script_dir = os.path.dirname(os.path.abspath(__file__))

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

def report_generation(report_text: str, patient_id: str) -> None:
    # Create the structured prompt
    prompt = f"""
    You are an AI assistant for a medical imaging platform. Your task is to generate a concise, professional 'AI Overview' for a doctor's report based on the following structured findings in JSON format. The tone should be clinical and direct.

    Findings:
    {report_text}

    Based on this data, generate:
    - A clear 'AI Overview' section for the report (mention size, shape, location, and complexities)
    - A Conclusion for the findings
    - Suggestions for the Doctor
    """

    # Prepare the request data for the Groq API
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}]
    }

    # Send request to the Groq API
    response = requests.post(url, headers=headers, json=data)
    res_json = response.json()

    # Extract the generated content
    text = res_json["choices"][0]["message"]["content"]

    # Clean up the generated text
    text_clean = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text_clean = re.sub(r"#+\s*", "", text_clean)
    text_clean = re.sub(r"\n\s*\n", "\n", text_clean)

    # Save the result to a patient-specific file
    file_name = f"{patient_id}_doctor_report.txt"
    file_path = os.path.join(script_dir, file_name)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(text_clean)

    return text_clean  # Return the cleaned text for further processing
