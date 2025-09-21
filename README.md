
# **NH07 - Parallel Minds**

🏥 **Medical Report & Patient Management System**

---

## 📌 **Overview**

A complete **Medical Report Generation & Patient Management System** with advanced features like **3D visualization, chatbot assistance, patient summary reports, multilingual audio reports, and interactive dashboards**.

---

## ✨ **Features**

* 📋 **Patient Report Generation** – Export reports in **PDF, TXT** formats
* 🧑‍⚕️ **Doctor Support Module** – Manage and review reports
* 🖼️ **3D Model Visualization** – Interactive scan visualization
* 📊 **Dashboard & History** – Recent patient records and statistics
* 🤖 **Chatbot Assistance** – Smart conversational support for kidney health
* 🔊 **Multilingual Audio Reports** – English & Telugu patient summaries

---

## ⚙️ **Requirements**

Install dependencies:

```bash
pip install flask reportlab pillow pandas numpy torch torchvision torchaudio scikit-learn ultralytics flask-cors opencv-python gTTS matplotlib
```

---

## 📂 **Project Structure**

```
NH07-ParallelMinds/
│
├── app.py                   # Main Flask entry point
├── doctorreport.py           # Doctor report generator
├── patient_report.py         # Patient report handler
├── reportpatient.py          # Patient report processor
├── kidney_report.py          # Kidney report generation
├── speech.py                 # Text-to-speech module
│
├── templates/                # HTML Frontend Pages
│   ├── index.html            # Home Page
│   ├── 3dmodel.html          # 3D Model Visualization Page
│   ├── dashboard.html        # Dashboard
│   ├── patientsview.html     # Recent Patients
│   ├── punlogin.html         # Chatbot UI
│   └── login.html            # Login Page
│
├── static/                   # Static files
│   ├── audio/                # Generated audio reports
│   │   ├── patient_english_report.mp3
│   │   └── patient_telugu_report.mp3
│   ├── css/                  # Stylesheets
│   ├── js/                   # JavaScript files
│   └── images/               # UI Images
│       └── temp_bg.png
│
├── detection_results.json    # Sample detection results
├── kidney_report.pdf         # Example kidney report
├── patient_Report.txt        # Example patient summary
├── scanned.jpg               # Example scanned image
└── README.md                 # Project documentation
```

---

## 🚀 **How to Run**

1. Clone the repository:

   ```bash
   git clone <repo_url>
   cd NH07-ParallelMinds
   ```
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

   
3. Run the Flask server:

   ```bash
   python app.py
   ```
4. Open in browser:

   ```
   http://127.0.0.1:5000/
   ```

---

