import os
import uuid
from datetime import datetime, timedelta, date
from flask import (
    Flask, request, jsonify, session, url_for, redirect,
    render_template, flash, send_file, send_from_directory
)
from parse import parsing
from pymongo import MongoClient
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from groq import Groq
from doctor import dsupport
from modeldo import detect_stones_report
from doctorreport import create_kidney_report 
import json
app = Flask(__name__)
app.secret_key = os.urandom(24)
MONGO_URI = "mongodb+srv://umeshyenugula2007_db_user:fwmIOPGPWBnzIoce@agritrade.29grdah.mongodb.net/"
client = MongoClient(MONGO_URI)
db = client["Litholens"]
doctor_col = db["doctor"]
patients_col = db["patient"]
import re
def parse_findings(findings_text):
    ai_overview = ""
    conclusion = ""
    suggestions = ""

    # Extract AI Overview
    ai_overview_match = re.search(r"AI Overview\s*(.*?)(?=Conclusion|$)", findings_text, re.DOTALL)
    if ai_overview_match:
        ai_overview = ai_overview_match.group(1).strip()

    # Extract Conclusion
    conclusion_match = re.search(r"Conclusion\s*(.*?)(?=Suggestions for the Doctor|$)", findings_text, re.DOTALL)
    if conclusion_match:
        conclusion = conclusion_match.group(1).strip()

    # Extract Suggestions
    suggestions_match = re.search(r"Suggestions for the Doctor\s*(.*)", findings_text, re.DOTALL)
    if suggestions_match:
        suggestions_text = suggestions_match.group(1).strip()
        # Split the suggestions by the numbering pattern and make them a list
        try:
            suggestions = suggestions_text.split("\n")
        except Exception as e:
            suggestions=0,0,0
    # Clean up suggestions (removing line breaks and unnecessary spaces)



    # Return all the extracted data: ai_overview, conclusion, suggestions, location, size, number_of_stones
    return ai_overview, conclusion, suggestions

# Upload folders & allowed extensions
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['OUTPUT_FOLDER'] = 'static/detected'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
os.makedirs('doctor', exist_ok=True)  # For doctor reports

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def parse_report_file(filepath):
    """
    Parses the AI report text file to extract:
    - AI Overview
    - Conclusion
    - Suggestions (list)
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split content into overview+conclusion and suggestions parts
    parts = content.split("Suggestions for the Doctor")
    overview_conclusion = parts[0].strip()
    suggestions_block = parts[1].strip() if len(parts) > 1 else ""

    ai_overview = ""
    conclusion = ""

    # Extract AI Overview and Conclusion from overview_conclusion part
    if "AI Overview" in overview_conclusion:
        split_parts = overview_conclusion.split("Conclusion")
        ai_overview = split_parts[0].replace("AI Overview", "").strip()
        if len(split_parts) > 1:
            conclusion = split_parts[1].strip()

    # Extract numbered suggestions
    suggestions = []
    for line in suggestions_block.split('\n'):
        line = line.strip()
        if line and line[0].isdigit():
            # Remove numbering prefix (e.g. "1. ", "2. ")
            parts = line.split('.', 1)
            if len(parts) > 1:
                suggestions.append(parts[1].strip())
            else:
                suggestions.append(line)

    return ai_overview, conclusion, suggestions


# Helper to convert URL-like path to absolute filesystem path
def get_abs_path(url_path):
    if not url_path:
        return None
    # Remove leading slash
    if url_path.startswith('/'):
        url_path = url_path[1:]
    # Construct absolute path based on app root directory
    return os.path.abspath(os.path.join(os.path.dirname(__file__), url_path.replace('/', os.sep)))


@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")
@app.route("/punlogin", methods=["GET", "POST"])
def punlogin():
    return render_template("punlogin.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if "username" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = doctor_col.find_one({"username": username})
        if user and check_password_hash(user["password"], password):
            session["username"] = username
            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password.", "error")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect(url_for("login"))

    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    patients_today_count = patients_col.count_documents({
        "submitted_at": {"$gte": today_start, "$lt": today_end}
    })

    return render_template("dashboard.html",
                           name=session["username"],
                           pn=patients_today_count,
                           rg=patients_today_count)
@app.route('/submit-patient', methods=['POST'])
def submit_patient():
    required_fields = ['full_name', 'age', 'gender', 'phone', 'email', 'address']
    for field in required_fields:
        if not request.form.get(field):
            return jsonify(success=False, message=f"Field {field} is required."), 400

    try:
        age_int = int(request.form.get('age'))
    except ValueError:
        return jsonify(success=False, message="Age must be a valid number."), 400

    files = request.files.getlist('medical_images')
    if not files or len(files) == 0:
        return jsonify(success=False, message="Please upload at least one medical image."), 400

    saved_image_urls = []
    detected_image_urls = []
    all_findings = []
    patient_id = "PATIENT_" + uuid.uuid4().hex[:8].upper()

    for idx, file in enumerate(files, start=1):
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)

            try:
                file.save(filepath)
            except Exception as e:
                app.logger.error(f"File saving error: {e}")
                return jsonify(success=False, message="Failed to save uploaded file."), 500

            saved_image_urls.append(f"/static/uploads/{unique_filename}")

            try:
                findings, detected_img_path = detect_stones_report(
                    image_path=filepath,
                    model_path=r"C:\kaggle\working\kidney_stone_ssl\simclr_yolo11n\weights\best.pt",
                    output_dir=app.config['OUTPUT_FOLDER'],
                    patient_id=f"{patient_id}_{idx}"
                )
            except Exception as e:
                app.logger.error(f"Detection error: {e}")
                return jsonify(success=False, message="Error processing image."), 500

            all_findings.append(f"Image {idx}: {findings}")
            detected_image_urls.append(detected_img_path.replace("\\", "/"))
        else:
            return jsonify(success=False, message="Unsupported file type."), 400

    combined_findings = " ".join(all_findings)
    session['patient_id'] = patient_id

    patient_doc = {
        "patient_id": patient_id,
        "full_name": request.form.get('full_name'),
        "age": age_int,
        "gender": request.form.get('gender'),
        "phone": request.form.get('phone'),
        "email": request.form.get('email'),
        "address": request.form.get('address'),
        "insurance": request.form.get('insurance', ''),
        "uploaded_images": saved_image_urls,
        "detected_images": detected_image_urls,
        "findings": combined_findings,
        "submitted_at": datetime.now()
    }

    try:
        patients_col.insert_one(patient_doc)
    except Exception as e:
        app.logger.error(f"MongoDB insertion error: {e}")
        return jsonify(success=False, message="Database error."), 500

    return jsonify(
        success=True,
        patient_code=patient_id,
        uploaded_images=saved_image_urls,
        detected_images=detected_image_urls,
        findings="Can Download Report (Get Report Doctor Copy , Get Patient Copy)"
    )

@app.route('/doctor-report')
def doctor_report():
    patient_id = session.get("patient_id")
    if not patient_id:
        return "Patient ID not found in session", 404

    patient_doc = patients_col.find_one({"patient_id": patient_id})
    if not patient_doc:
        return render_template('404.html'), 404
    
    # Ensure that findings_text is fetched properly from the database
    findings_text = patient_doc.get("findings", "")

    # Check if findings_text exists and handle errors if not
    if not findings_text:
        app.logger.error("Findings text is empty!")
        return "No findings available", 400

    # Ensure the 'doctor' directory exists for report generation
    os.makedirs("doctor", exist_ok=True)

    # Generate the doctor report using the dsupport function
    try:
        text = dsupport.report_generation(findings_text, patient_id)  # Generate report for the doctor
    except Exception as e:
        app.logger.error(f"Error in report generation: {str(e)}")
        return "Error generating the report", 500
    
    # Now parse the generated report
    ai_overview, conclusion, suggestions = parse_findings(text)

    # Extract additional findings from the structured data
    result = str(parsing(findings_text))  
    try:
        location, size, number_of_stones = result.split(",")
    except ValueError:
        location, size, number_of_stones = "0", "0", "0"    

    # Log the extracted details for debugging purposes
    app.logger.info(f"AI Overview: {ai_overview}")
    app.logger.info(f"Conclusion: {conclusion}")
    app.logger.info(f"Suggestions: {suggestions}")
    app.logger.info(f"Location: {location}")
    app.logger.info(f"Size: {size}")
    app.logger.info(f"Stones: {number_of_stones}")

    # Prepare the patient info for PDF generation
    patient_info = {
        "name": patient_doc.get("full_name", ""),
        "id": patient_doc.get("patient_id", ""),
        "gender": patient_doc.get("gender", ""),
        "age": patient_doc.get("age", ""),
        "address": patient_doc.get("address", ""),
        "report_date": patient_doc.get("submitted_at", date.today())
    }

    # Prepare the findings dictionary for the PDF generation
    findings_dict = {
        "detection": "Detected" if "stone" in findings_text.lower() else "Not Detected",
        "location": location,
        "stone_size": size,
        "number_of_stones": number_of_stones,
        "ai_overview": ai_overview,
        "conclusion": conclusion,
        "doctor_suggestions": suggestions,
        "original_image": get_abs_path(patient_doc.get("uploaded_images", [None])[0]),
        "detected_image": get_abs_path(patient_doc.get("detected_images", [None])[0])
    }

    # Prepare the PDF filename and path
    pdf_filename = f"{patient_id}_report.pdf"
    pdf_filepath = os.path.join(app.config['OUTPUT_FOLDER'], pdf_filename)

    try:
        create_kidney_report(
            filename=pdf_filepath,
            patient_info=patient_info,
            findings=findings_dict,
            scanned_image_path=get_abs_path(patient_doc.get("detected_images", [None])[0]),
            show_pdf=True  # This flag might control whether the PDF is shown or not
        )
    except Exception as e:
        app.logger.error(f"PDF generation failed: {e}")
        return f"Failed to generate PDF: {str(e)}", 500

    # Return the generated PDF for download
    return send_file(pdf_filepath, mimetype='application/pdf', as_attachment=True, download_name=pdf_filename)
@app.route('/patient-report')
def patient_report():
    patient_id = session.get("patient_id")
    if not patient_id:
        return "Patient ID not found in session", 404

    patient_doc = patients_col.find_one({"patient_id": patient_id})
    if not patient_doc:
        return  404
    
    # Ensure that findings_text is fetched properly from the database
    findings_text = patient_doc.get("findings", "")

    # Check if findings_text exists and handle errors if not
    if not findings_text:
        app.logger.error("Findings text is empty!")
        return "No findings available", 400

    # Ensure the 'doctor' directory exists for report generation
    os.makedirs("doctor", exist_ok=True)

    # Generate the doctor report using the dsupport function
    try:
        text = dsupport.report_generation(findings_text, patient_id)  # Generate report for the doctor
    except Exception as e:
        app.logger.error(f"Error in report generation: {str(e)}")
        return "Error generating the report", 500
    
    # Now parse the generated report
    ai_overview, conclusion, suggestions = parse_findings(text)

    # Extract additional findings from the structured data
    result = str(parsing(findings_text))  
    try:
        location, size, number_of_stones = result.split(",")
    except ValueError:
        location, size, number_of_stones = "0", "0", "0" 

    # Log the extracted details for debugging purposes
    app.logger.info(f"AI Overview: {ai_overview}")
    app.logger.info(f"Conclusion: {conclusion}")
    app.logger.info(f"Suggestions: {suggestions}")
    app.logger.info(f"Location: {location}")
    app.logger.info(f"Size: {size}")
    app.logger.info(f"Stones: {number_of_stones}")

    # Prepare the patient info for PDF generation
    patient_info = {
        "name": patient_doc.get("full_name", ""),
        "id": patient_doc.get("patient_id", ""),
        "gender": patient_doc.get("gender", ""),
        "age": patient_doc.get("age", ""),
        "address": patient_doc.get("address", ""),
        "report_date": patient_doc.get("submitted_at", date.today())
    }

    # Prepare the findings dictionary for the PDF generation
    findings_dict = {
        "detection": "Detected" if "stone" in findings_text.lower() else "Not Detected",
        "location": location,
        "stone_size": size,
        "number_of_stones": number_of_stones,
        "conclusion": conclusion,
        "ai_overview": ai_overview,
        "original_image": get_abs_path(patient_doc.get("uploaded_images", [None])[0]),
        "detected_image": get_abs_path(patient_doc.get("detected_images", [None])[0])
    }

    # Prepare the PDF filename and path
    pdf_filename = f"{patient_id}_report.pdf"
    pdf_filepath = os.path.join(app.config['OUTPUT_FOLDER'], pdf_filename)

    try:
        from reportpatinet import create_report
        create_report(
            pdf_filepath,
            patient_info,
            findings_dict,
            get_abs_path(patient_doc.get("uploaded_images", [None])[0]),
            get_abs_path(patient_doc.get("detected_images", [None])[0])# This flag might control whether the PDF is shown or not
        )
    except Exception as e:
        app.logger.error(f"PDF generation failed: {e}")
        return f"Failed to generate PDF: {str(e)}", 500

    # Return the generated PDF for download
    return send_file(pdf_filepath, mimetype='application/pdf', as_attachment=True, download_name=pdf_filename)
@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/static/detected/<filename>')
def detected_file(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)


@app.route('/3d-view')
def three_d_view():
    return render_template('3dmodel.html')


@app.route('/patientsview')
def patients_view():
    # Fetch recent patients from the database
    patients = patients_col.find().sort('submitted_at', -1)  # Sort by the most recent submissions

    patient_data = []
    for patient in patients:
        patient_data.append({
            "patient_id": patient.get("patient_id", ""),
            "full_name": patient.get("full_name", ""),
            "age": patient.get("age", ""),
            "gender": patient.get("gender", ""),
            "submitted_at": patient.get("submitted_at", "").strftime('%Y-%m-%d'),
            "phone": patient.get("phone", ""),
            "report_url": f"/static/detected/{patient.get('patient_id')}_detected.jpg"  # Assuming the report is an image
        })

    return render_template('patientsview.html', patients=patient_data)


@app.route('/logout')
def logout():
    session.pop("username", None)
    session.pop("patient_id", None)
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))

@app.route("/chat", methods=["POST"])
def chat():
    from groq import Groq
    user_message = request.json.get("message")
    if not user_message:
        return jsonify({"reply": "Please provide a message."})
    cclient = Groq(
    api_key="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",
)
    chat_completion = cclient.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": (
                   "You are a medical assistant specialized in kidney health and general patient care. "
                   "You should ONLY answer questions related to kidney health, kidney stones, and medical advice related to kidneys. "
                   "Answer in not more than 5 lines. "
                   "For any other topic, politely respond with: 'I am only able to answer questions related to kidney health.' "
                   "Include a disclaimer ONLY when medical advice requires a doctor's confirmation. "
                )
            },
            {"role": "user", "content": user_message}
        ],
        model="llama-3.3-70b-versatile"
    )

    reply = chat_completion.choices[0].message.content
    return jsonify({"reply": reply})
import asyncio
import uuid
import os
from flask import Flask, request, jsonify, session
from werkzeug.utils import secure_filename # your report generator
from sppech import generate_english_audio,generate_telugu_audio  # your existing functions
@app.route('/getimage', methods=['POST'])
def getimage():
    try:
        files = request.files.getlist('medical_images')
        if not files or len(files) == 0:
            return jsonify(success=False, message="Please upload at least one medical image."), 400
        saved_image_urls = []
        detected_image_urls = []
        all_findings = []
        patient_id = "PATIENT_" + uuid.uuid4().hex[:8].upper()
        for idx, file in enumerate(files, start=1):
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4().hex}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(filepath)
                saved_image_urls.append(f"/static/uploads/{unique_filename}")

                findings, detected_img_path = detect_stones_report(
                    image_path=filepath,
                    model_path=r"C:\kaggle\working\kidney_stone_ssl\simclr_yolo11n\weights\best.pt",
                    output_dir=app.config['OUTPUT_FOLDER'],
                    patient_id=f"{patient_id}_{idx}"
                )

                all_findings.append(f"Image {idx}: {findings}")
                detected_image_urls.append(detected_img_path.replace("\\", "/"))
            else:
                return jsonify(success=False, message="Unsupported file type."), 400

        combined_findings = " ".join(all_findings)
        session['patient_id'] = patient_id

        # Generate report text files
        from patient_report import report_generation
        report_english_path, report_telugu_path = report_generation(combined_findings)

        # Read English report file directly
        with open(report_english_path, "r", encoding="utf-8") as f:
            english_text = f.read()

        # Generate audio using asyncio
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            tasks = [
                generate_english_audio(report_english_path),
                generate_telugu_audio(report_telugu_path)
            ]
            loop.run_until_complete(asyncio.gather(*tasks))
            loop.close()
        except Exception as e:
            app.logger.error(f"Audio generation error: {e}")
            return jsonify(success=False, message="Error generating voice."), 500

        return jsonify(
            success=True,
            patient_code=patient_id,
            detected_images=detected_image_urls,
            findings=english_text,  # <-- directly sending English report content
            english_audio="/static/audio/patient_english_report.mp3",
            telugu_audio="/static/audio/patient_telugu_report.mp3"
        )

    except Exception as e:
        app.logger.error(f"Unexpected error: {e}")
        return jsonify(success=False, message="An unexpected error occurred."), 500

@app.route('/static/audio/<path:filename>')
def serve_audio(filename):
    return send_from_directory('static/audio', filename)

if __name__ == "__main__":
    app.run(debug=True)