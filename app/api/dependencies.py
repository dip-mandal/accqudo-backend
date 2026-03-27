# backend/app/api/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

from app.core.config import settings

from sqlalchemy.future import select
from app.db.session import get_db
from app.db.models import TenantModule, Module
from sqlalchemy.ext.asyncio import AsyncSession

# This tells FastAPI to look for a Bearer token in the Authorization header
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    
    try:
        # Decode the token using our secret key
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        
        email: str = payload.get("sub")
        tenant_id: str = payload.get("tenant_id")
        role: str = payload.get("role")
        
        if email is None or tenant_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # Return the decoded payload so our routes know exactly who is making the request
        return {
            "email": email,
            "tenant_id": tenant_id,
            "role": role
        }
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired or is invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        



def require_module(module_key: str):
    """
    This is our SaaS Paywall Middleware. 
    It checks if the current tenant has active access to a specific module.
    """
    async def _check_module(
        current_user: dict = Depends(get_current_user), 
        db: AsyncSession = Depends(get_db)
    ):
        tenant_id = current_user["tenant_id"]
        
        # Query to see if the tenant has this specific module activated
        query = (
            select(TenantModule)
            .join(Module)
            .where(
                TenantModule.tenant_id == tenant_id,
                Module.key == module_key,
                TenantModule.is_active == True
            )
        )
        result = await db.execute(query)
        active_module = result.scalars().first()
        
        if not active_module:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Upgrade Required: Your subscription does not include the '{module_key}' module."
            )
            
        return current_user
    return _check_module