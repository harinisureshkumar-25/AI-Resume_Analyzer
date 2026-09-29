from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
from ..database import get_collection
from ..schemas import UserRegister, UserLogin, Token, UserProfile, ProfileUpdate
from ..utils import get_password_hash, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register", response_model=UserProfile)
async def register(user_data: UserRegister):
    users_collection = get_collection("users")
    
    # Check if user already exists
    existing_user = await users_collection.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email address already registered"
        )
    
    # Create new user document
    new_user = {
        "name": user_data.name,
        "email": user_data.email,
        "password_hash": get_password_hash(user_data.password),
        "created_at": datetime.utcnow()
    }
    
    result = await users_collection.insert_one(new_user)
    new_user["id"] = str(result.inserted_id)
    return new_user

@router.post("/login", response_model=Token)
async def login(login_data: UserLogin):
    users_collection = get_collection("users")
    user = await users_collection.find_one({"email": login_data.email})
    
    if not user or not verify_password(login_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user["email"]})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/profile", response_model=UserProfile)
async def get_profile(current_user: dict = Depends(get_current_user)):
    return current_user

@router.put("/profile", response_model=UserProfile)
async def update_profile(
    profile_data: ProfileUpdate,
    current_user: dict = Depends(get_current_user)
):
    users_collection = get_collection("users")
    update_data = {}
    
    if profile_data.name:
        update_data["name"] = profile_data.name
        current_user["name"] = profile_data.name
    if profile_data.password:
        update_data["password_hash"] = get_password_hash(profile_data.password)
        
    if update_data:
        from bson import ObjectId
        await users_collection.update_one(
            {"_id": ObjectId(current_user["id"])},
            {"$set": update_data}
        )
        
    return current_user
