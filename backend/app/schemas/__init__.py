from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# Auth Schemas
class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserProfile(BaseModel):
    id: str  # Hex String from MongoDB ObjectId
    name: str
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    password: Optional[str] = None

# Analysis & Job Matching Schemas
class ResumeAnalysisResponse(BaseModel):
    id: str
    filename: str
    overall_score: float
    ats_score: float
    skills_score: float
    project_score: float
    experience_score: float
    detected_skills: Optional[Dict[str, List[str]]] = None
    analysis_results: Optional[Dict[str, Any]] = None
    target_role: Optional[str] = "Full Stack Developer"
    role_match: Optional[Dict[str, Any]] = None
    token_analysis: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True

class RoleAnalyzeRequest(BaseModel):
    analysis_id: str
    target_role: str

class RoleAnalyzeResponse(BaseModel):
    analysis_id: str
    target_role: str
    overall_score: float
    role_match_score: float
    token_efficiency_score: float
    ats_score: float
    skills_score: float
    role_match: Dict[str, Any]
    token_analysis: Dict[str, Any]

class JobMatchRequest(BaseModel):
    analysis_id: str
    job_description: str

class JobMatchResponse(BaseModel):
    id: str
    analysis_id: str
    match_score: float
    matched_skills: List[str]
    missing_skills: List[str]
    recommendations: List[str]
    created_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True
