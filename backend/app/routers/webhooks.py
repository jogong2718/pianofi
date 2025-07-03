from fastapi import APIRouter, HTTPException, Request, Depends
from app.config_loader import Config
import stripe
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session
from datetime import datetime
import json

router = APIRouter()

DATABASE_URL = Config.DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=10,
    max_overflow=20
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def create_or_update_customer(db: Session, stripe_customer_id: str, user_id: str):
    """Create or update customer in database"""
    try:
        # Check if customer already exists by user_id
        result = db.execute(
            text("SELECT id, stripe_customer_id FROM customers WHERE id = :user_id"),
            {"user_id": user_id}
        )
        existing_customer = result.fetchone()
        
        if existing_customer:
            # Update existing customer with new stripe_customer_id
            db.execute(
                text("UPDATE customers SET stripe_customer_id = :stripe_customer_id WHERE id = :user_id"),
                {
                    "stripe_customer_id": stripe_customer_id,
                    "user_id": user_id
                }
            )
            logging.info(f"Updated customer {user_id} with Stripe customer {stripe_customer_id}")
        else:
            # Create new customer
            db.execute(
                text("INSERT INTO customers (id, stripe_customer_id) VALUES (:user_id, :stripe_customer_id)"),
                {
                    "user_id": user_id,
                    "stripe_customer_id": stripe_customer_id
                }
            )
            logging.info(f"Created customer {user_id} with Stripe customer {stripe_customer_id}")
        
        db.commit()
        
    except Exception as e:
        db.rollback()
        logging.error(f"Error creating/updating customer: {str(e)}")
        raise

async def create_or_update_subscription(db: Session, subscription_data: dict):
    """Create or update subscription in database"""
    try:
        # Extract subscription data
        subscription_id = subscription_data['id']
        customer_id = subscription_data['customer']
        price_id = subscription_data['items']['data'][0]['price']['id']
        status = subscription_data['status']
        quantity = subscription_data.get('quantity', 1)
        cancel_at_period_end = subscription_data.get('cancel_at_period_end', False)
        
        # Extract price data from subscription
        price_data = subscription_data['items']['data'][0]['price']
        
        # Create/update the price first
        await create_or_update_price(db, price_data)
        
        # Also create/update the product if it doesn't exist
        product_id = price_data['product']
        product_data = {
            'id': product_id,
            'active': True,
            'name': f'Product {product_id}',  # You might want to fetch this from Stripe
            'description': None,
            'image': None,
            'metadata': {}
        }
        await create_or_update_product(db, product_data)
        
        # Handle missing period dates - get them from subscription items
        current_period_start = None
        current_period_end = None
        
        # Get period dates from subscription items
        if subscription_data['items']['data']:
            item = subscription_data['items']['data'][0]
            if 'current_period_start' in item:
                current_period_start = datetime.fromtimestamp(item['current_period_start'])
            if 'current_period_end' in item:
                current_period_end = datetime.fromtimestamp(item['current_period_end'])
        
        # Fallback to subscription level dates if available
        if not current_period_start and 'start_date' in subscription_data:
            current_period_start = datetime.fromtimestamp(subscription_data['start_date'])
        if not current_period_end and 'billing_cycle_anchor' in subscription_data:
            current_period_end = datetime.fromtimestamp(subscription_data['billing_cycle_anchor'])
            
        canceled_at = datetime.fromtimestamp(subscription_data['canceled_at']) if subscription_data.get('canceled_at') else None
        trial_start = datetime.fromtimestamp(subscription_data['trial_start']) if subscription_data.get('trial_start') else None
        trial_end = datetime.fromtimestamp(subscription_data['trial_end']) if subscription_data.get('trial_end') else None
        metadata = json.dumps(subscription_data.get('metadata', {}))
        
        # Get user_id from customer record
        result = db.execute(
            text("SELECT id FROM customers WHERE stripe_customer_id = :customer_id"),
            {"customer_id": customer_id}
        )
        customer_record = result.fetchone()
        
        if not customer_record:
            # Get user_id from subscription metadata (set during checkout)
            user_id = subscription_data.get('metadata', {}).get('user_id')
            if not user_id:
                logging.error(f"No user_id found in subscription metadata for customer {customer_id}")
                return
            
            # Create customer record
            await create_or_update_customer(db, customer_id, user_id)
            user_id = user_id
        else:
            user_id = customer_record[0]

        # Cancel other active subscriptions for this user when creating a new active one
        if status == 'active':
            # Cancel all other active subscriptions for this user in the database
            result = db.execute(
                text("""
                    UPDATE subscriptions SET 
                        status = 'canceled',
                        canceled_at = NOW()
                    WHERE user_id = :user_id 
                    AND id != :subscription_id
                    AND status IN ('active', 'trialing', 'past_due')
                """),
                {
                    "user_id": user_id,
                    "subscription_id": subscription_id
                }
            )
            
            # Log how many subscriptions were canceled
            canceled_count = result.rowcount
            if canceled_count > 0:
                logging.info(f"Canceled {canceled_count} other active subscriptions for user {user_id} due to new subscription {subscription_id}")
        
        
        # Check if subscription already exists
        result = db.execute(
            text("SELECT id FROM subscriptions WHERE id = :subscription_id"),
            {"subscription_id": subscription_id}
        )
        existing_subscription = result.fetchone()
        
        if existing_subscription:
            # Update existing subscription
            db.execute(
                text("""
                    UPDATE subscriptions SET 
                        price_id = :price_id,
                        status = :status,
                        quantity = :quantity,
                        cancel_at_period_end = :cancel_at_period_end,
                        current_period_start = :current_period_start,
                        current_period_end = :current_period_end,
                        canceled_at = :canceled_at,
                        trial_start = :trial_start,
                        trial_end = :trial_end,
                        metadata = :metadata
                    WHERE id = :subscription_id
                """),
                {
                    "subscription_id": subscription_id,
                    "price_id": price_id,
                    "status": status,
                    "quantity": quantity,
                    "cancel_at_period_end": cancel_at_period_end,
                    "current_period_start": current_period_start,
                    "current_period_end": current_period_end,
                    "canceled_at": canceled_at,
                    "trial_start": trial_start,
                    "trial_end": trial_end,
                    "metadata": metadata
                }
            )
            logging.info(f"Updated subscription {subscription_id}")
        else:
            # Create new subscription
            db.execute(
                text("""
                    INSERT INTO subscriptions (
                        id, user_id, price_id, status, quantity, cancel_at_period_end,
                        current_period_start, current_period_end, canceled_at,
                        trial_start, trial_end, metadata
                    ) VALUES (
                        :subscription_id, :user_id, :price_id, :status, :quantity, :cancel_at_period_end,
                        :current_period_start, :current_period_end, :canceled_at,
                        :trial_start, :trial_end, :metadata
                    )
                """),
                {
                    "subscription_id": subscription_id,
                    "user_id": user_id,
                    "price_id": price_id,
                    "status": status,
                    "quantity": quantity,
                    "cancel_at_period_end": cancel_at_period_end,
                    "current_period_start": current_period_start,
                    "current_period_end": current_period_end,
                    "canceled_at": canceled_at,
                    "trial_start": trial_start,
                    "trial_end": trial_end,
                    "metadata": metadata
                }
            )
            logging.info(f"Created subscription {subscription_id}")
        
        db.commit()
        
    except Exception as e:
        db.rollback()
        logging.error(f"Error creating/updating subscription: {str(e)}")
        logging.error(f"Subscription data: {subscription_data}")
        raise

async def cancel_subscription(db: Session, subscription_data: dict):
    """Cancel subscription in database"""
    try:
        subscription_id = subscription_data['id']
        canceled_at = datetime.fromtimestamp(subscription_data['canceled_at']) if subscription_data.get('canceled_at') else datetime.utcnow()
        
        db.execute(
            text("""
                UPDATE subscriptions SET 
                    status = 'canceled',
                    canceled_at = :canceled_at
                WHERE id = :subscription_id
            """),
            {
                "subscription_id": subscription_id,
                "canceled_at": canceled_at
            }
        )
        
        db.commit()
        logging.info(f"Canceled subscription {subscription_id}")
        
    except Exception as e:
        db.rollback()
        logging.error(f"Error canceling subscription: {str(e)}")
        raise

async def create_or_update_product(db: Session, product_data: dict):
    """Create or update product in database"""
    try:
        product_id = product_data['id']
        active = product_data.get('active', True)
        name = product_data.get('name')
        description = product_data.get('description')
        image = product_data.get('images', [None])[0]  # First image if available
        metadata = json.dumps(product_data.get('metadata', {}))
        
        # Check if product already exists
        result = db.execute(
            text("SELECT id FROM products WHERE id = :product_id"),
            {"product_id": product_id}
        )
        existing_product = result.fetchone()
        
        if existing_product:
            # Update existing product
            db.execute(
                text("""
                    UPDATE products SET 
                        active = :active,
                        name = :name,
                        description = :description,
                        image = :image,
                        metadata = :metadata
                    WHERE id = :product_id
                """),
                {
                    "product_id": product_id,
                    "active": active,
                    "name": name,
                    "description": description,
                    "image": image,
                    "metadata": metadata
                }
            )
            logging.info(f"Updated product {product_id}")
        else:
            # Create new product
            db.execute(
                text("""
                    INSERT INTO products (
                        id, active, name, description, image, metadata
                    ) VALUES (
                        :product_id, :active, :name, :description, :image, :metadata
                    )
                """),
                {
                    "product_id": product_id,
                    "active": active,
                    "name": name,
                    "description": description,
                    "image": image,
                    "metadata": metadata
                }
            )
            logging.info(f"Created product {product_id}")
        
        db.commit()
        
    except Exception as e:
        db.rollback()
        logging.error(f"Error creating/updating product: {str(e)}")
        raise

async def create_or_update_price(db: Session, price_data: dict):
    """Create or update price in database"""
    try:
        price_id = price_data['id']
        active = price_data.get('active', True)
        currency = price_data.get('currency')
        unit_amount = price_data.get('unit_amount')
        price_type = price_data.get('type')  # 'recurring' or 'one_time'
        
        # Recurring price fields
        recurring = price_data.get('recurring')
        interval = recurring.get('interval') if recurring else None
        interval_count = recurring.get('interval_count') if recurring else None
        trial_period_days = recurring.get('trial_period_days') if recurring else None
        
        metadata = json.dumps(price_data.get('metadata', {}))
        
        # Check if price already exists
        result = db.execute(
            text("SELECT id FROM prices WHERE id = :price_id"),
            {"price_id": price_id}
        )
        existing_price = result.fetchone()
        
        if existing_price:
            # Update existing price
            db.execute(
                text("""
                    UPDATE prices SET 
                        active = :active,
                        currency = :currency,
                        unit_amount = :unit_amount,
                        type = :type,
                        interval = :interval,
                        interval_count = :interval_count,
                        trial_period_days = :trial_period_days,
                        metadata = :metadata
                    WHERE id = :price_id
                """),
                {
                    "price_id": price_id,
                    "active": active,
                    "currency": currency,
                    "unit_amount": unit_amount,
                    "type": price_type,
                    "interval": interval,
                    "interval_count": interval_count,
                    "trial_period_days": trial_period_days,
                    "metadata": metadata
                }
            )
            logging.info(f"Updated price {price_id}")
        else:
            # Create new price
            db.execute(
                text("""
                    INSERT INTO prices (
                        id, active, currency, unit_amount, type, interval, 
                        interval_count, trial_period_days, metadata
                    ) VALUES (
                        :price_id, :active, :currency, :unit_amount, :type, :interval,
                        :interval_count, :trial_period_days, :metadata
                    )
                """),
                {
                    "price_id": price_id,
                    "active": active,
                    "currency": currency,
                    "unit_amount": unit_amount,
                    "type": price_type,
                    "interval": interval,
                    "interval_count": interval_count,
                    "trial_period_days": trial_period_days,
                    "metadata": metadata
                }
            )
            logging.info(f"Created price {price_id}")
        
        db.commit()
        
    except Exception as e:
        db.rollback()
        logging.error(f"Error creating/updating price: {str(e)}")
        raise

@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Handle Stripe webhooks to sync subscription data
    """
    try:
        body = await request.body()
        sig_header = request.headers.get('stripe-signature')
        
        event = stripe.Webhook.construct_event(
            body, sig_header, Config.STRIPE_KEYS['webhook_secret']
        )
        
        logging.info(f"🚀 Received Stripe webhook: {event['type']}")
        logging.info(f"🔍 Event data keys: {list(event['data']['object'].keys())}")
        logging.info(f"🔍 Full event data: {event['data']['object']}")
        
        # Handle different event types
        if event['type'] == 'customer.subscription.created':
            subscription = event['data']['object']
            await create_or_update_subscription(db, subscription)
            
        elif event['type'] == 'customer.subscription.updated':
            subscription = event['data']['object']
            await create_or_update_subscription(db, subscription)
            
        elif event['type'] == 'customer.subscription.deleted':
            subscription = event['data']['object']
            await cancel_subscription(db, subscription)
            
        elif event['type'] == 'invoice.payment_succeeded':
            # Handle successful payment
            invoice = event['data']['object']
            subscription_id = invoice.get('subscription')
            logging.info(f"Payment succeeded for subscription {subscription_id}")
            
        elif event['type'] == 'invoice.payment_failed':
            # Handle failed payment
            invoice = event['data']['object']
            subscription_id = invoice.get('subscription')
            logging.warning(f"Payment failed for subscription {subscription_id}")
        
         # Product webhook events
        elif event['type'] == 'product.created':
            product = event['data']['object']
            await create_or_update_product(db, product)
            
        elif event['type'] == 'product.updated':
            product = event['data']['object']
            await create_or_update_product(db, product)
            
        # Price webhook events
        elif event['type'] == 'price.created':
            price = event['data']['object']
            await create_or_update_price(db, price)
            
        elif event['type'] == 'price.updated':
            price = event['data']['object']
            await create_or_update_price(db, price)
        
        else:
            logging.info(f"Unhandled webhook event type: {event['type']}")
            
        return {"status": "success"}
        
    except stripe.error.SignatureVerificationError as e:
        logging.error(f"Stripe signature verification failed: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        logging.error(f"Webhook error: {str(e)}")
        logging.error(f"Event type: {event.get('type', 'unknown') if 'event' in locals() else 'event not parsed'}")
        raise HTTPException(status_code=400, detail=str(e))