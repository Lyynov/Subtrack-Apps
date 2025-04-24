#!/usr/bin/env python3
import os
import sys
import json
import logging
from datetime import datetime

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import SessionLocal, engine
from app.db.models import Base, User, Category, Subscription, PaymentHistory, Notification
from app.services.user_service import get_password_hash

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger("load_mock_data")

def load_mock_data():
    """
    Load mock data into the database
    """
    logger.info("Loading mock data into the database...")
    
    # Create database tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    # Load mock data from JSON file
    mock_data_path = os.path.join(os.path.dirname(__file__), '..', 'mock_data', 'mock_data.json')
    
    with open(mock_data_path, 'r') as f:
        mock_data = json.load(f)
    
    db = SessionLocal()
    try:
        # Check if data already exists
        if db.query(User).count() > 0:
            logger.warning("Database already has data. Skipping mock data load.")
            return
        
        # Load users
        logger.info("Loading users...")
        for user_data in mock_data.get('users', []):
            user = User(
                id=user_data['id'],
                email=user_data['email'],
                hashed_password=user_data['hashed_password'],
                full_name=user_data['full_name'],
                is_active=user_data['is_active'],
                role=user_data['role']
            )
            db.add(user)
        
        # Commit users to get their IDs
        db.commit()
        
        # Load categories
        logger.info("Loading categories...")
        for category_data in mock_data.get('categories', []):
            category = Category(
                id=category_data['id'],
                name=category_data['name'],
                description=category_data['description'],
                color=category_data['color'],
                user_id=category_data['user_id']
            )
            db.add(category)
        
        # Commit categories to get their IDs
        db.commit()
        
        # Load subscriptions
        logger.info("Loading subscriptions...")
        for subscription_data in mock_data.get('subscriptions', []):
            subscription = Subscription(
                id=subscription_data['id'],
                name=subscription_data['name'],
                description=subscription_data['description'],
                amount=subscription_data['amount'],
                currency=subscription_data['currency'],
                billing_cycle=subscription_data['billing_cycle'],
                billing_day=subscription_data['billing_day'],
                next_billing_date=datetime.strptime(subscription_data['next_billing_date'], '%Y-%m-%d').date(),
                start_date=datetime.strptime(subscription_data['start_date'], '%Y-%m-%d').date(),
                auto_renew=subscription_data['auto_renew'],
                reminder_days=subscription_data['reminder_days'],
                website_url=subscription_data['website_url'],
                is_active=subscription_data['is_active'],
                user_id=subscription_data['user_id'],
                category_id=subscription_data['category_id']
            )
            db.add(subscription)
        
        # Commit subscriptions to get their IDs
        db.commit()
        
        # Load payment history
        logger.info("Loading payment history...")
        for payment_data in mock_data.get('payment_history', []):
            payment = PaymentHistory(
                id=payment_data['id'],
                subscription_id=payment_data['subscription_id'],
                payment_date=datetime.strptime(payment_data['payment_date'], '%Y-%m-%d').date(),
                amount=payment_data['amount'],
                status=payment_data['status'],
                payment_method=payment_data['payment_method'],
                notes=payment_data['notes']
            )
            db.add(payment)
        
        # Load notifications
        logger.info("Loading notifications...")
        for notification_data in mock_data.get('notifications', []):
            notification = Notification(
                id=notification_data['id'],
                user_id=notification_data['user_id'],
                subscription_id=notification_data['subscription_id'],
                type=notification_data['type'],
                subject=notification_data['subject'],
                message=notification_data['message'],
                status=notification_data['status'],
                scheduled_at=datetime.strptime(notification_data['scheduled_at'], '%Y-%m-%dT%H:%M:%SZ')
            )
            db.add(notification)
        
        # Commit all remaining data
        db.commit()
        
        logger.info("Mock data loaded successfully!")
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error loading mock data: {str(e)}")
    finally:
        db.close()

def create_admin_user(email, password, full_name):
    """
    Create an admin user
    """
    logger.info(f"Creating admin user: {email}")
    
    db = SessionLocal()
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            logger.warning(f"User {email} already exists. Skipping.")
            return False
        
        # Create user
        hashed_password = get_password_hash(password)
        user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            is_active=True,
            role="admin"
        )
        db.add(user)
        db.commit()
        
        logger.info(f"Admin user {email} created successfully!")
        return True
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating admin user: {str(e)}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Load mock data into the database")
    parser.add_argument("--mock-data", action="store_true", help="Load mock data")
    parser.add_argument("--admin", action="store_true", help="Create admin user")
    parser.add_argument("--email", help="Admin email")
    parser.add_argument("--password", help="Admin password")
    parser.add_argument("--name", help="Admin full name")
    
    args = parser.parse_args()
    
    if args.mock_data:
        load_mock_data()
    
    if args.admin:
        if not args.email or not args.password or not args.name:
            logger.error("Email, password, and name are required to create admin user")
            sys.exit(1)
        
        success = create_admin_user(args.email, args.password, args.name)
        if not success:
            sys.exit(1)
    
    if not args.mock_data and not args.admin:
        parser.print_help()