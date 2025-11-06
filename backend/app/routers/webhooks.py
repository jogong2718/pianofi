# backend/app/routers/webhooks.py
from fastapi import APIRouter, HTTPException, Request, Depends
from app.database import get_db
from sqlalchemy.orm import Session
from app.services.webhook_service import handle_stripe_webhook
import logging, stripe

router = APIRouter()

@router.post("/stripe/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig = request.headers.get("stripe-signature")
    try:
        return handle_stripe_webhook(payload, sig, db)
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        logging.exception("Stripe webhook handling error")
        # Return 400 so Stripe retries; once fixed, it will re-deliver
        raise HTTPException(status_code=400, detail=str(e))
