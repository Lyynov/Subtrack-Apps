#!/usr/bin/env python3
import os
import sys
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import smtplib

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import SessionLocal
from app.db.models import Subscription, Notification, NotificationStatus, User
from app.services.notification_service import (
    generate_subscription_reminders,
    mark_notification_as_sent
)
from app.utils.email_utils import send_subscription_reminder_email
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.getLevelName(settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(settings.LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("notification_scheduler")

def generate_upcoming_reminders():
    """
    Generate reminder notifications for upcoming subscription payments
    """
    logger.info("Generating upcoming subscription reminders...")
    
    db = SessionLocal()
    try:
        # Generate reminders for next 7 days
        reminders = generate_subscription_reminders(db, days_ahead=7)
        logger.info(f"Generated {len(reminders)} reminders for upcoming subscriptions")
    except Exception as e:
        logger.error(f"Error generating reminders: {str(e)}")
    finally:
        db.close()

def send_pending_notifications():
    """
    Send all pending notifications that are due
    """
    logger.info("Sending pending notifications...")
    
    db = SessionLocal()
    try:
        # Get all pending notifications scheduled for now or earlier
        now = datetime.now()
        notifications = db.query(Notification).filter(
            Notification.status == NotificationStatus.PENDING,
            Notification.scheduled_at <= now
        ).all()
        
        logger.info(f"Found {len(notifications)} pending notifications to send")
        
        for notification in notifications:
            try:
                # Get user and subscription info if applicable
                user = db.query(User).filter(User.id == notification.user_id).first()
                subscription = notification.subscription
                
                if not user:
                    logger.warning(f"User not found for notification {notification.id}")
                    continue
                
                # Send based on notification type
                if notification.type == "email":
                    if subscription:
                        # This is a subscription reminder
                        days_before = subscription.reminder_days
                        billing_date = subscription.next_billing_date.strftime("%Y-%m-%d")
                        
                        result = send_subscription_reminder_email(
                            user_email=user.email,
                            user_name=user.full_name,
                            subscription_name=subscription.name,
                            days_before=days_before,
                            billing_date=billing_date,
                            amount=subscription.amount,
                            currency=subscription.currency
                        )
                    else:
                        # This is a generic notification
                        from app.utils.email_utils import send_email
                        
                        result = send_email(
                            recipient_email=user.email,
                            subject=notification.subject,
                            body_html=notification.message,
                            body_text=notification.message
                        )
                    
                    if result:
                        mark_notification_as_sent(db, notification.id)
                        logger.info(f"Notification {notification.id} sent successfully via email")
                    else:
                        logger.error(f"Failed to send notification {notification.id} via email")
                
                elif notification.type == "push":
                    # Push notification implementation would go here
                    # For now, just mark as sent
                    mark_notification_as_sent(db, notification.id)
                    logger.info(f"Notification {notification.id} sent successfully via push notification")
                
                else:
                    logger.warning(f"Unsupported notification type '{notification.type}' for notification {notification.id}")
            
            except Exception as e:
                logger.error(f"Error sending notification {notification.id}: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error processing notifications: {str(e)}")
    finally:
        db.close()

def run_scheduler():
    """
    Run the scheduler for notification tasks
    """
    logger.info("Starting notification scheduler...")
    
    scheduler = BlockingScheduler()
    
    # Generate reminders daily at 1:00 AM
    scheduler.add_job(
        generate_upcoming_reminders,
        CronTrigger(hour=1, minute=0),
        id="generate_reminders",
        name="Generate subscription reminders",
        replace_existing=True
    )
    
    # Send notifications every 15 minutes
    scheduler.add_job(
        send_pending_notifications,
        CronTrigger(minute="*/15"),
        id="send_notifications",
        name="Send pending notifications",
        replace_existing=True
    )
    
    # Run immediately on startup
    scheduler.add_job(generate_upcoming_reminders, id="initial_generate_reminders")
    scheduler.add_job(send_pending_notifications, id="initial_send_notifications")
    
    logger.info("Scheduler started. Press Ctrl+C to exit.")
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")

if __name__ == "__main__":
    run_scheduler()