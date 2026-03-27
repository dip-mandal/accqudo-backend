# backend/app/services/auth/router.py
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import random
import uuid
import os
import bcrypt # 🌟 NEW: Using the official bcrypt library directly
from datetime import datetime, timedelta

from app.db.session import get_db
from app.db.models import Tenant 
from app.core.redis import redis_client
from app.core.security import create_access_token
from app.core.email import send_otp_email, send_welcome_email, send_login_alert

router = APIRouter()

# --- 🌟 NEW: Modern, Crash-Proof Password Hashing ---
def get_password_hash(password: str) -> str:
    # bcrypt requires bytes, so we encode the string
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_pwd = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_pwd.decode('utf-8') # Return as string for the database

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        password_bytes = plain_password.encode('utf-8')
        hashed_password_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_password_bytes)
    except ValueError:
        return False

# --- Pydantic Schemas ---
class OTPRequest(BaseModel):
    email: EmailStr
    purpose: str = "login" # "login", "register", or "reset"

class RegisterVerify(BaseModel):
    name: str
    email: EmailStr
    otp: str
    password: str 

class LoginVerify(BaseModel):
    email: EmailStr
    otp: str = None
    password: str = None

class ResetPasswordVerify(BaseModel):
    email: EmailStr
    otp: str
    new_password: str

# ---------------------------------------------------------
# 1. REQUEST OTP
# ---------------------------------------------------------
@router.post("/request-otp")
async def request_otp(payload: OTPRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tenant).where(Tenant.email == payload.email))
    user = result.scalars().first()
    
    if payload.purpose in ["login", "reset"] and not user:
        raise HTTPException(status_code=404, detail="Email not found.")
    if payload.purpose == "register" and user:
        raise HTTPException(status_code=400, detail="Email already registered.")

    otp = str(random.randint(100000, 999999))
    
    redis_key = f"otp:{payload.purpose}:{payload.email}"
    await redis_client.setex(redis_key, 600, otp)

    email_sent = send_otp_email(to_email=payload.email, otp_code=otp, purpose=payload.purpose)
    
    if not email_sent:
        print(f"\n❌ SMTP FAILED. DEV OTP FOR {payload.email}: [{otp}]\n")
        return {"message": "OTP generated in console (Dev Mode)."}

    return {"message": "OTP sent successfully."}

# ---------------------------------------------------------
# 2. VERIFY OTP & REGISTER
# ---------------------------------------------------------
@router.post("/register")
async def verify_and_register(payload: RegisterVerify, db: AsyncSession = Depends(get_db)):
    redis_key = f"otp:register:{payload.email}"
    stored_otp = await redis_client.get(redis_key)

    # 🌟 FIX: Removed .decode("utf-8")
    if not stored_otp or str(stored_otp) != payload.otp:
        raise HTTPException(status_code=401, detail="Invalid or expired OTP.")

    await redis_client.delete(redis_key)

    tenant_id = str(uuid.uuid4())
    subdomain = payload.name.lower().replace(" ", "").replace(".", "") + str(random.randint(10, 99))
    hashed_pw = get_password_hash(payload.password) if payload.password else None
    
    new_tenant = Tenant(id=tenant_id, name=payload.name, email=payload.email, subdomain=subdomain, hashed_password=hashed_pw)
    db.add(new_tenant)
    await db.commit()

    send_welcome_email(to_email=payload.email, name=payload.name)

    access_token = create_access_token(data={"sub": new_tenant.email, "tenant_id": new_tenant.id})
    return {"access_token": access_token, "token_type": "bearer", "subdomain": subdomain}

# ---------------------------------------------------------
# 3. LOGIN
# ---------------------------------------------------------
@router.post("/login")
async def login(req: Request, payload: LoginVerify, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tenant).where(Tenant.email == payload.email))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    if payload.otp:
        redis_key = f"otp:login:{payload.email}"
        stored_otp = await redis_client.get(redis_key)
        
        # 🌟 FIX: Removed .decode("utf-8")
        if not stored_otp or str(stored_otp) != payload.otp:
            raise HTTPException(status_code=401, detail="Invalid or expired OTP.")
        await redis_client.delete(redis_key)
        
    elif payload.password:
        if not user.hashed_password or not verify_password(payload.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid password.")
            
    else:
        raise HTTPException(status_code=400, detail="Must provide either OTP or Password.")

    access_token = create_access_token(data={"sub": user.email, "tenant_id": user.id})
    
    ip_address = req.client.host if req.client else "Unknown IP"
    user_agent = req.headers.get("user-agent", "Unknown Device")
    send_login_alert(to_email=user.email, ip_address=ip_address, user_agent=user_agent)

    return {"access_token": access_token, "token_type": "bearer", "subdomain": user.subdomain}

# ---------------------------------------------------------
# 4. RESET PASSWORD
# ---------------------------------------------------------
@router.post("/forgot-password")
async def forgot_password(payload: OTPRequest, db: AsyncSession = Depends(get_db)):
    payload.purpose = "reset"
    return await request_otp(payload, db)

@router.post("/reset-password")
async def reset_password(payload: ResetPasswordVerify, db: AsyncSession = Depends(get_db)):
    redis_key = f"otp:reset:{payload.email}"
    stored_otp = await redis_client.get(redis_key)

    # 🌟 FIX: Removed .decode("utf-8")
    if not stored_otp or str(stored_otp) != payload.otp:
        raise HTTPException(status_code=401, detail="Invalid or expired OTP.")

    await redis_client.delete(redis_key)

    result = await db.execute(select(Tenant).where(Tenant.email == payload.email))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    user.hashed_password = get_password_hash(payload.new_password)
    await db.commit()

    return {"message": "Password reset successfully. You can now log in."}





from app.api.dependencies import get_current_user
# --- Protected Test Route ---
@router.get("/me")
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    return {
        "message": "You have successfully accessed a protected route!",
        "your_data": current_user
    }