# ResumeIQ AI

ResumeIQ AI is a premium, futuristic, full-stack AI Resume Analyzer and ATS Optimization application built with FastAPI, MySQL, Three.js, and Gemini API.

## Features

- **3D Hero Page**: Landing page with custom 3D document floating model animations built using Three.js.
- **Secure Authentication**: Hashed passwords with JWT verification.
- **ATS Parsing**: Extract structure, skills, projects, and work experience parameters.
- **Detailed Analytics Dashboard**: Chart visualizations representing your score distributions.
- **Job Description Matcher**: Calculated match score percentages, extracted missing skills, and custom AI recommendations.

## Requirements

- Python 3.10+ (Installed via `py` Windows launcher)
- MySQL Server instance running locally

## Local Installation & Setup

1. **MySQL Setup**:
   Create a new local MySQL database named `resumeiq_db`.
   ```sql
   CREATE DATABASE resumeiq_db;
   ```

2. **Configure Environment variables**:
   Open the [backend/.env](file:///E:/AI%20resume%20analyzer/backend/.env) file and enter your MySQL database connection string and Gemini/OpenAI API keys:
   ```env
   DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/resumeiq_db
   GEMINI_API_KEY=YOUR_GEMINI_API_KEY
   ```

3. **Install dependencies**:
   Install python dependencies using the terminal command:
   ```bash
   py -m pip install -r backend/requirements.txt
   ```

4. **Run the Backend Server**:
   Start the FastAPI development server:
   ```bash
   py -m uvicorn backend.app.main:app --reload
   ```

5. **Access Application**:
   Open your browser and visit:
   [http://127.0.0.1:8000/index.html](http://127.0.0.1:8000/index.html)
