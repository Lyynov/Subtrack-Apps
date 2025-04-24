import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import logging
from typing import List, Optional
import os

from app.config import settings

logger = logging.getLogger(__name__)

def send_email(
    recipient_email: str, 
    subject: str, 
    body_html: str, 
    body_text: str = None,
    attachments: List[tuple] = None  # List of (filename, file_data) tuples
) -> bool:
    """
    Send an email using the configured SMTP settings
    
    Args:
        recipient_email: Email address of the recipient
        subject: Email subject
        body_html: HTML version of the email body
        body_text: Plain text version of the email body (optional)
        attachments: List of (filename, file_data) tuples (optional)
        
    Returns:
        True if email was sent successfully, False otherwise
    """
    # Check if email is configured
    if not settings.MAIL_SERVER or not settings.MAIL_USERNAME or not settings.MAIL_PASSWORD:
        logger.warning("Email settings not configured. Cannot send email.")
        return False
    
    # Create message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = settings.MAIL_FROM or settings.MAIL_USERNAME
    msg['To'] = recipient_email
    
    # Attach text part if provided
    if body_text:
        part1 = MIMEText(body_text, 'plain')
        msg.attach(part1)
    
    # Attach HTML part
    part2 = MIMEText(body_html, 'html')
    msg.attach(part2)
    
    # Attach files if provided
    if attachments:
        for filename, file_data in attachments:
            attachment = MIMEApplication(file_data)
            attachment.add_header('Content-Disposition', 'attachment', filename=filename)
            msg.attach(attachment)
    
    # Send email
    try:
        server = smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT)
        
        if settings.MAIL_TLS:
            server.starttls()
        
        server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
        server.sendmail(settings.MAIL_FROM or settings.MAIL_USERNAME, recipient_email, msg.as_string())
        server.quit()
        
        logger.info(f"Email sent to {recipient_email}: {subject}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False

def send_subscription_reminder_email(
    user_email: str,
    user_name: str,
    subscription_name: str,
    days_before: int,
    billing_date: str,
    amount: float,
    currency: str = "IDR"
) -> bool:
    """
    Send a subscription reminder email
    
    Args:
        user_email: Email address of the user
        user_name: Name of the user
        subscription_name: Name of the subscription
        days_before: Number of days before the billing date
        billing_date: Billing date in string format (YYYY-MM-DD)
        amount: Billing amount
        currency: Currency code (default: IDR)
        
    Returns:
        True if email was sent successfully, False otherwise
    """
    subject = f"{subscription_name} subscription renewal reminder"
    
    # Create HTML body
    html_body = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #1E90FF; color: white; padding: 10px 20px; text-align: center; }}
            .content {{ padding: 20px; border: 1px solid #ddd; border-top: none; }}
            .footer {{ font-size: 12px; color: #777; text-align: center; margin-top: 20px; }}
            .important {{ color: #FF5733; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>{settings.APP_NAME}</h2>
            </div>
            <div class="content">
                <p>Hello {user_name},</p>
                
                <p>This is a reminder that your <strong>{subscription_name}</strong> subscription will be renewed in <span class="important">{days_before} days</span> on <span class="important">{billing_date}</span>.</p>
                
                <p>Details:</p>
                <ul>
                    <li><strong>Subscription:</strong> {subscription_name}</li>
                    <li><strong>Amount:</strong> {currency} {amount:,.2f}</li>
                    <li><strong>Billing Date:</strong> {billing_date}</li>
                </ul>
                
                <p>Please ensure that your payment method is up-to-date and has sufficient funds to avoid any service interruption.</p>
                
                <p>You can view more details and manage your subscription in the {settings.APP_NAME} application.</p>
                
                <p>Thank you for using {settings.APP_NAME}!</p>
            </div>
            <div class="footer">
                <p>This is an automated message from {settings.APP_NAME}. Please do not reply to this email.</p>
                <p>If you have any questions, please contact our support team.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Create plain text body
    text_body = f"""
    Hello {user_name},
    
    This is a reminder that your {subscription_name} subscription will be renewed in {days_before} days on {billing_date}.
    
    Details:
    - Subscription: {subscription_name}
    - Amount: {currency} {amount:,.2f}
    - Billing Date: {billing_date}
    
    Please ensure that your payment method is up-to-date and has sufficient funds to avoid any service interruption.
    
    You can view more details and manage your subscription in the {settings.APP_NAME} application.
    
    Thank you for using {settings.APP_NAME}!
    
    This is an automated message from {settings.APP_NAME}. Please do not reply to this email.
    If you have any questions, please contact our support team.
    """
    
    return send_email(
        recipient_email=user_email,
        subject=subject,
        body_html=html_body,
        body_text=text_body
    )

def send_monthly_report_email(
    user_email: str,
    user_name: str,
    month_name: str,
    year: int,
    total_amount: float,
    subscription_count: int,
    pdf_report: bytes,
    currency: str = "IDR"
) -> bool:
    """
    Send a monthly report email with PDF attachment
    
    Args:
        user_email: Email address of the user
        user_name: Name of the user
        month_name: Name of the month
        year: Year
        total_amount: Total amount for the month
        subscription_count: Number of active subscriptions
        pdf_report: PDF report as bytes
        currency: Currency code (default: IDR)
        
    Returns:
        True if email was sent successfully, False otherwise
    """
    subject = f"{settings.APP_NAME} - {month_name} {year} Subscription Report"
    
    # Create HTML body
    html_body = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #1E90FF; color: white; padding: 10px 20px; text-align: center; }}
            .content {{ padding: 20px; border: 1px solid #ddd; border-top: none; }}
            .footer {{ font-size: 12px; color: #777; text-align: center; margin-top: 20px; }}
            .highlight {{ background-color: #f8f9fa; padding: 10px; border-left: 3px solid #1E90FF; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>{month_name} {year} Subscription Report</h2>
            </div>
            <div class="content">
                <p>Hello {user_name},</p>
                
                <p>Attached is your {month_name} {year} subscription report from {settings.APP_NAME}.</p>
                
                <div class="highlight">
                    <p><strong>Summary:</strong></p>
                    <ul>
                        <li>Total Amount: {currency} {total_amount:,.2f}</li>
                        <li>Active Subscriptions: {subscription_count}</li>
                    </ul>
                </div>
                
                <p>For detailed information, please see the attached PDF report or log in to your {settings.APP_NAME} account.</p>
                
                <p>Thank you for using {settings.APP_NAME} to manage your subscriptions!</p>
            </div>
            <div class="footer">
                <p>This is an automated message from {settings.APP_NAME}. Please do not reply to this email.</p>
                <p>If you have any questions, please contact our support team.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Create plain text body
    text_body = f"""
    Hello {user_name},
    
    Attached is your {month_name} {year} subscription report from {settings.APP_NAME}.
    
    Summary:
    - Total Amount: {currency} {total_amount:,.2f}
    - Active Subscriptions: {subscription_count}
    
    For detailed information, please see the attached PDF report or log in to your {settings.APP_NAME} account.
    
    Thank you for using {settings.APP_NAME} to manage your subscriptions!
    
    This is an automated message from {settings.APP_NAME}. Please do not reply to this email.
    If you have any questions, please contact our support team.
    """
    
    # Create attachment
    filename = f"{settings.APP_NAME}_Report_{month_name}_{year}.pdf"
    attachments = [(filename, pdf_report)]
    
    return send_email(
        recipient_email=user_email,
        subject=subject,
        body_html=html_body,
        body_text=text_body,
        attachments=attachments
    )