from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from .routes import auth, resume

app = FastAPI(
    title="ResumeIQ AI API",
    description="Full-stack AI Resume Analyzer and ATS Optimizer (MongoDB)",
    version="1.0.0"
)

# Set up CORS middleware to allow local frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Auth and Resume API routers
app.include_router(auth.router)
app.include_router(resume.router)

# Mount frontend files under root static files to enable single-port local deployment
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
