from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from typing import List
from datetime import datetime
from bson import ObjectId
import json
from ..database import get_collection
from ..schemas import ResumeAnalysisResponse, JobMatchResponse
from ..utils import get_current_user, oauth2_scheme, settings
from jose import jwt
from ..services.pdf import extract_text_from_pdf
from ..services.ai import ai_service

router = APIRouter(prefix="/api/resume", tags=["resume"])

def clean_mongo_doc(doc: dict) -> dict:
    """Helper to convert MongoDB _id to string id key"""
    if doc and "_id" in doc:
        doc["id"] = str(doc["_id"])
    return doc

from fastapi.security import APIKeyHeader
from typing import Optional

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

@router.post("/upload", response_model=ResumeAnalysisResponse)
async def upload_resume(
    file: UploadFile = File(...),
    target_role: Optional[str] = Form("Full Stack Developer"),
    auth_header: Optional[str] = Depends(api_key_header)
):
    current_user_id = "guest_user"
    if auth_header:
        try:
            token = auth_header.split(" ")[1] if " " in auth_header else auth_header
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
            email = payload.get("sub")
            if email:
                users_collection = get_collection("users")
                user = await users_collection.find_one({"email": email})
                if user:
                    current_user_id = str(user["_id"])
        except Exception:
            pass

    if not file.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported."
        )
        
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds the 5MB limit."
        )
        
    try:
        text = extract_text_from_pdf(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to process PDF content: {str(e)}"
        )
        
    if not text or len(text.strip()) < 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PDF contains insufficient extractable text."
        )

    # Perform AI resume analysis with target role and token optimizer
    analysis_data = ai_service.analyze_resume(text, target_role=target_role or "Full Stack Developer")
    
    # Store in MongoDB / local DB
    analysis_collection = get_collection("resume_analyses")
    db_analysis = {
        "user_id": current_user_id,
        "filename": file.filename,
        "text": text,
        "target_role": analysis_data.get("target_role", target_role or "Full Stack Developer"),
        "overall_score": float(analysis_data.get("scores", {}).get("overall", 0.0)),
        "ats_score": float(analysis_data.get("scores", {}).get("ats_compatibility", 0.0)),
        "skills_score": float(analysis_data.get("scores", {}).get("skills", 0.0)),
        "project_score": float(analysis_data.get("scores", {}).get("projects", 0.0)),
        "experience_score": float(analysis_data.get("scores", {}).get("experience", 0.0)),
        "role_match": analysis_data.get("role_match", {}),
        "token_analysis": analysis_data.get("token_analysis", {}),
        "detected_skills": analysis_data.get("skills", {}),
        "analysis_results": analysis_data,
        "created_at": datetime.utcnow()
    }
    
    result = await analysis_collection.insert_one(db_analysis)
    db_analysis["id"] = str(result.inserted_id)
    return db_analysis

@router.post("/role-analyze")
async def analyze_target_role(
    analysis_id: str = Form(...),
    target_role: str = Form(...),
    auth_header: Optional[str] = Depends(api_key_header)
):
    analysis_collection = get_collection("resume_analyses")
    try:
        analysis = await analysis_collection.find_one({"_id": ObjectId(analysis_id)})
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid resume ID format.")
    
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume analysis record not found.")

    updated_eval = ai_service.analyze_for_role(
        resume_text=analysis["text"],
        target_role=target_role,
        detected_skills=analysis.get("detected_skills"),
        existing_scores=analysis.get("analysis_results", {}).get("scores")
    )

    try:
        await analysis_collection.update_one(
            {"_id": ObjectId(analysis_id)},
            {"$set": {
                "target_role": updated_eval["target_role"],
                "overall_score": updated_eval["overall_score"],
                "ats_score": updated_eval["ats_score"],
                "role_match": updated_eval["role_match"],
                "token_analysis": updated_eval["token_analysis"]
            }}
        )
    except Exception:
        pass

    return {
        "analysis_id": analysis_id,
        "target_role": updated_eval["target_role"],
        "overall_score": updated_eval["overall_score"],
        "ats_score": updated_eval["ats_score"],
        "role_match_score": updated_eval["role_match_score"],
        "token_efficiency_score": updated_eval["token_efficiency_score"],
        "skills_score": updated_eval["skills_score"],
        "role_match": updated_eval["role_match"],
        "token_analysis": updated_eval["token_analysis"]
    }

@router.post("/job-match", response_model=JobMatchResponse)
async def match_job(
    analysis_id: str = Form(...),
    job_description: str = Form(...),
    auth_header: Optional[str] = Depends(api_key_header)
):
    analysis_collection = get_collection("resume_analyses")
    try:
        analysis = await analysis_collection.find_one({
            "_id": ObjectId(analysis_id)
        })
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid resume ID format."
        )
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume analysis record not found"
        )
        
    if not job_description.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job description cannot be empty."
        )
        
    # Process matching with AI
    match_data = ai_service.match_job(analysis["text"], job_description)
    
    # Save match results in MongoDB
    matches_collection = get_collection("job_matches")
    db_match = {
        "analysis_id": analysis_id,
        "job_description": job_description,
        "match_score": float(match_data.get("match_score", 0.0)),
        "matched_skills": match_data.get("matched_skills", []),
        "missing_skills": match_data.get("missing_skills", []),
        "recommendations": match_data.get("recommendations", []),
        "created_at": datetime.utcnow()
    }
    
    result = await matches_collection.insert_one(db_match)
    db_match["id"] = str(result.inserted_id)
    return db_match

@router.get("/history", response_model=List[ResumeAnalysisResponse])
async def get_history(current_user: dict = Depends(get_current_user)):
    analysis_collection = get_collection("resume_analyses")
    cursor = analysis_collection.find({"user_id": current_user["id"]}).sort("created_at", -1)
    history = []
    async for doc in cursor:
        history.append(clean_mongo_doc(doc))
    return history

@router.get("/{analysis_id}", response_model=ResumeAnalysisResponse)
async def get_analysis_detail(
    analysis_id: str,
    auth_header: Optional[str] = Depends(api_key_header)
):
    analysis_collection = get_collection("resume_analyses")
    try:
        analysis = await analysis_collection.find_one({
            "_id": ObjectId(analysis_id)
        })
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid analysis ID format"
        )
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume analysis not found"
        )
    return clean_mongo_doc(analysis)

@router.delete("/{analysis_id}")
async def delete_analysis(
    analysis_id: str,
    auth_header: Optional[str] = Depends(api_key_header)
):
    analysis_collection = get_collection("resume_analyses")
    try:
        result = await analysis_collection.delete_one({
            "_id": ObjectId(analysis_id)
        })
    except Exception:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid analysis ID format"
        )
         
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume analysis not found"
        )
        
    return {"detail": "Analysis deleted successfully."}
