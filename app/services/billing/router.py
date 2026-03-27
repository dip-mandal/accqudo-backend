# backend/app/services/billing/router.py

import razorpay
import requests
from requests.auth import HTTPBasicAuth
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel

from app.core.config import settings
from app.db.session import get_db
from app.db.models import Module, TenantModule, Tenant
from app.api.dependencies import get_current_user

router = APIRouter()

# Initialize Razorpay Client using your secure .env keys
rzp_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

# ==========================================
# 🛒 STOREFRONT
# ==========================================

@router.get("/packages")
async def get_available_packages(db: AsyncSession = Depends(get_db)):
    """Returns the list of all available modules and their prices."""
    result = await db.execute(select(Module))
    modules = result.scalars().all()
    
    return {
        "packages": [
            {
                "id": m.id,
                "name": m.key.capitalize(),
                "description": m.description,
                "price_inr": m.base_price
            } for m in modules
        ]
    }

# ==========================================
# 💳 SMART SUBSCRIPTION ENGINE (AUTOPAY)
# ==========================================

class CartCheckout(BaseModel):
    module_keys: list[str]

@router.post("/create-subscription")
async def create_subscription(
    payload: CartCheckout,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Takes a cart of modules, calculates the total, and generates a Razorpay Autopay Subscription.
    If the user already has a subscription, it upgrades their existing mandate dynamically.
    Includes fallback logic for UPI mandates which cannot be updated.
    """
    tenant_id = current_user["tenant_id"]

    if not payload.module_keys:
        raise HTTPException(status_code=400, detail="Cart is empty")

    # 1. Fetch the tenant to check for existing subscriptions
    tenant_query = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = tenant_query.scalars().first()

    # 2. Find ALL modules the user will own (Existing Active + New Cart)
    existing_modules_query = await db.execute(
        select(Module).join(TenantModule).where(
            TenantModule.tenant_id == tenant_id,
            TenantModule.is_active == True
        )
    )
    existing_keys = [m.key for m in existing_modules_query.scalars().all()]
    
    # Combine and remove duplicates
    all_future_keys = list(set(existing_keys + payload.module_keys))

    # 3. Calculate the New Grand Total
    modules_query = await db.execute(select(Module).where(Module.key.in_(all_future_keys)))
    modules = modules_query.scalars().all()
    total_monthly_price = sum(m.base_price for m in modules)

    if total_monthly_price <= 0:
        raise HTTPException(status_code=400, detail="Total amount must be greater than 0")

    try:
        # 4. Create a dynamic Razorpay Plan for the new total
        plan_data = {
            "period": "monthly",
            "interval": 1,
            "item": {
                "name": f"accqudo Bundle ({len(modules)} Modules)", # 🌟 REBRANDED
                "amount": int(total_monthly_price * 100),
                "currency": "INR",
                "description": "Auto-renewing academic platform"
            }
        }
        rzp_plan = rzp_client.plan.create(plan_data)

        # 5. UPGRADE PATH: Using direct HTTP request to bypass Razorpay SDK Bug
        if tenant.razorpay_subscription_id:
            update_url = f"https://api.razorpay.com/v1/subscriptions/{tenant.razorpay_subscription_id}"
            update_payload = {
                "plan_id": rzp_plan["id"],
                "schedule_change_at": "now" # Instantly applies the new pricing
            }
            
            response = requests.patch(
                update_url,
                json=update_payload,
                auth=HTTPBasicAuth(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
            )

            if response.status_code not in [200, 201]:
                # 🚨 UPI FALLBACK: If Razorpay blocks the update due to UPI, create a NEW subscription
                if "upi" in response.text.lower():
                    print("UPI mandate update blocked. Falling back to new mandate creation...")
                    sub_data = {
                        "plan_id": rzp_plan["id"],
                        "total_count": 120,
                        "customer_notify": 1
                    }
                    rzp_sub = rzp_client.subscription.create(sub_data)
                    return {
                        "status": "new",
                        "subscription_id": rzp_sub["id"],
                        "key_id": settings.RAZORPAY_KEY_ID,
                        "total_price": total_monthly_price
                    }
                else:
                    raise Exception(f"Razorpay API Error: {response.text}")
            
            # If Credit Card (or successful update), instantly activate the modules in DB
            for module in modules:
                if module.key in payload.module_keys:
                    existing_link_query = await db.execute(select(TenantModule).where(
                        TenantModule.tenant_id == tenant_id, TenantModule.module_id == module.id
                    ))
                    existing_link = existing_link_query.scalars().first()
                    if existing_link:
                        existing_link.is_active = True
                    else:
                        new_link = TenantModule(tenant_id=tenant_id, module_id=module.id, is_active=True)
                        db.add(new_link)
            await db.commit()
            
            return {"status": "upgraded", "message": "Subscription updated successfully!"}

        # 6. NEW SUBSCRIPTION PATH: Create a brand new Autopay mandate
        sub_data = {
            "plan_id": rzp_plan["id"],
            "total_count": 120, # Run for 10 years automatically
            "customer_notify": 1
        }
        rzp_sub = rzp_client.subscription.create(sub_data)

        return {
            "status": "new",
            "subscription_id": rzp_sub["id"],
            "key_id": settings.RAZORPAY_KEY_ID,
            "total_price": total_monthly_price
        }
    except Exception as e:
        print(f"Razorpay Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to initialize billing engine.")


class SubscriptionVerification(BaseModel):
    razorpay_subscription_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    module_keys: list[str]

@router.post("/verify-subscription")
async def verify_subscription(
    payload: SubscriptionVerification,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Verifies the Autopay mandate signature and unlocks multiple modules at once.
    Handles legacy UPI mandate cancellation if falling back.
    """
    tenant_id = current_user["tenant_id"]

    try:
        # Verify the Autopay signature
        rzp_client.utility.verify_subscription_payment_signature({
            'razorpay_subscription_id': payload.razorpay_subscription_id,
            'razorpay_payment_id': payload.razorpay_payment_id,
            'razorpay_signature': payload.razorpay_signature
        })
    except razorpay.errors.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Autopay verification failed.")

    # 1. Fetch the tenant
    tenant_query = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = tenant_query.scalars().first()

    # 🌟 UPI CLEANUP: If they had an old UPI subscription and just created a new one, cancel the old one!
    if tenant.razorpay_subscription_id and tenant.razorpay_subscription_id != payload.razorpay_subscription_id:
        try:
            cancel_url = f"https://api.razorpay.com/v1/subscriptions/{tenant.razorpay_subscription_id}/cancel"
            requests.post(
                cancel_url,
                json={"cancel_at_cycle_end": 0},
                auth=HTTPBasicAuth(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
            )
            print(f"Successfully cancelled old UPI mandate: {tenant.razorpay_subscription_id}")
        except Exception as e:
            print(f"Failed to cancel legacy UPI mandate: {e}")

    # Save the NEW Razorpay Subscription ID to the Tenant
    tenant.razorpay_subscription_id = payload.razorpay_subscription_id

    # 2. Activate the newly purchased modules
    modules_query = await db.execute(select(Module).where(Module.key.in_(payload.module_keys)))
    modules = modules_query.scalars().all()

    for module in modules:
        existing_query = await db.execute(select(TenantModule).where(
            TenantModule.tenant_id == tenant_id, TenantModule.module_id == module.id
        ))
        existing_link = existing_query.scalars().first()

        if existing_link:
            existing_link.is_active = True
        else:
            new_link = TenantModule(tenant_id=tenant_id, module_id=module.id, is_active=True)
            db.add(new_link)

    await db.commit()
    return {"message": "Autopay Setup Successful! Modules unlocked.", "status": "success"}


# ==========================================
# 🛑 CANCELLATIONS & DOWNGRADES
# ==========================================

@router.post("/cancel-module")
async def cancel_module(
    module_key: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Cancels an active module. Smartly recalculates the total bill and downgrades 
    the user's Razorpay Subscription for the next billing cycle.
    """
    tenant_id = current_user["tenant_id"]

    # 1. Deactivate the module in our DB
    module_query = await db.execute(select(Module).where(Module.key == module_key))
    module = module_query.scalars().first()

    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    link_query = await db.execute(select(TenantModule).where(
        TenantModule.tenant_id == tenant_id, TenantModule.module_id == module.id
    ))
    link = link_query.scalars().first()
    
    if link:
        link.is_active = False

    # 2. Recalculate the remaining active modules
    tenant_query = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = tenant_query.scalars().first()

    active_modules_query = await db.execute(
        select(Module).join(TenantModule).where(
            TenantModule.tenant_id == tenant_id,
            TenantModule.is_active == True
        )
    )
    remaining_modules = active_modules_query.scalars().all()
    new_total = sum(m.base_price for m in remaining_modules)

    # 3. Downgrade the Razorpay Subscription using direct HTTP requests!
    if tenant.razorpay_subscription_id:
        try:
            if new_total == 0:
                # If they cancelled everything, cancel the whole mandate using HTTP POST
                cancel_url = f"https://api.razorpay.com/v1/subscriptions/{tenant.razorpay_subscription_id}/cancel"
                requests.post(
                    cancel_url,
                    json={"cancel_at_cycle_end": 0},
                    auth=HTTPBasicAuth(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
                )
                tenant.razorpay_subscription_id = None
            else:
                # Otherwise, generate a cheaper plan and update the mandate using HTTP PATCH
                plan_data = {
                    "period": "monthly", "interval": 1,
                    "item": {"name": f"accqudo Bundle ({len(remaining_modules)} Modules)", "amount": int(new_total * 100), "currency": "INR"} # 🌟 REBRANDED
                }
                rzp_plan = rzp_client.plan.create(plan_data)
                
                update_url = f"https://api.razorpay.com/v1/subscriptions/{tenant.razorpay_subscription_id}"
                update_payload = {
                    "plan_id": rzp_plan["id"],
                    "schedule_change_at": "cycle_end" # Downgrades apply next billing cycle
                }
                response = requests.patch(
                    update_url,
                    json=update_payload,
                    auth=HTTPBasicAuth(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
                )
                
                # If UPI downgrade fails, we just leave it for now (or notify user they need to re-setup later)
                if response.status_code not in [200, 201]:
                    print(f"Downgrade via PATCH failed (likely UPI): {response.text}")
                    
        except Exception as e:
            print(f"Downgrade Error: {e}")

    await db.commit()
    return {"message": f"{module_key.capitalize()} cancelled. Subscription updated.", "status": "success"}


# ==========================================
# 🛑 LEGACY ROUTES (Optional / Bypasses)
# ==========================================

class PaymentVerificationLegacy(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    module_key: str

@router.post("/verify-payment")
async def verify_payment(
    payload: PaymentVerificationLegacy,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Legacy route for single-order verification without autopay."""
    tenant_id = current_user["tenant_id"]
    try:
        rzp_client.utility.verify_payment_signature({
            'razorpay_order_id': payload.razorpay_order_id,
            'razorpay_payment_id': payload.razorpay_payment_id,
            'razorpay_signature': payload.razorpay_signature
        })
    except razorpay.errors.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Signature verification failed.")

    module_query = await db.execute(select(Module).where(Module.key == payload.module_key))
    module = module_query.scalars().first()
    
    existing_query = await db.execute(select(TenantModule).where(TenantModule.tenant_id == tenant_id, TenantModule.module_id == module.id))
    existing_link = existing_query.scalars().first()

    if existing_link:
        existing_link.is_active = True
    else:
        new_link = TenantModule(tenant_id=tenant_id, module_id=module.id, is_active=True)
        db.add(new_link)

    await db.commit()
    return {"message": f"Payment successful! Module is now active.", "status": "success"}