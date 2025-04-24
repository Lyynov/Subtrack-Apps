import imaplib
import email
from email.header import decode_header
import re
import logging
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
import json
import base64
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import Subscription, User, Category
from app.schemas.subscription import SubscriptionCreate
from app.services.subscription_service import create_subscription, get_subscription_by_id

logger = logging.getLogger(__name__)

# Dictionary of known subscription services and their detection patterns
KNOWN_SERVICES = {
    "netflix": {
        "sender_patterns": ["@netflix.com"],
        "subject_patterns": ["pembayaran netflix", "netflix billing", "netflix payment", "tagihan netflix"],
        "amount_patterns": [
            r"(?:idr|rp)\.?\s*([0-9,.]+)",
            r"(?:idr|rp)\s*([0-9,.]+)",
            r"sejumlah\s*(?:idr|rp)\.?\s*([0-9,.]+)"
        ],
        "category_id": 1  # Entertainment category
    },
    "spotify": {
        "sender_patterns": ["@spotify.com"],
        "subject_patterns": ["pembayaran spotify", "spotify premium", "tagihan spotify"],
        "amount_patterns": [
            r"(?:idr|rp)\.?\s*([0-9,.]+)",
            r"(?:idr|rp)\s*([0-9,.]+)",
            r"sejumlah\s*(?:idr|rp)\.?\s*([0-9,.]+)"
        ],
        "category_id": 1  # Entertainment category
    },
    "adobe": {
        "sender_patterns": ["@adobe.com"],
        "subject_patterns": ["adobe creative cloud", "adobe payment", "adobe billing", "tagihan adobe"],
        "amount_patterns": [
            r"(?:idr|rp)\.?\s*([0-9,.]+)",
            r"(?:idr|rp)\s*([0-9,.]+)",
            r"sejumlah\s*(?:idr|rp)\.?\s*([0-9,.]+)"
        ],
        "category_id": 2  # Software category
    },
    "github": {
        "sender_patterns": ["@github.com"],
        "subject_patterns": ["github billing", "github payment", "tagihan github"],
        "amount_patterns": [
            r"(?:idr|rp)\.?\s*([0-9,.]+)",
            r"\$\s*([0-9,.]+)",
            r"US\$\s*([0-9,.]+)"
        ],
        "category_id": 2  # Software category
    },
    "domain": {
        "sender_patterns": ["@namecheap.com", "@godaddy.com", "@name.com", "@domains.com"],
        "subject_patterns": ["domain renewal", "domain expiration", "domain registration", "perpanjangan domain"],
        "amount_patterns": [
            r"(?:idr|rp)\.?\s*([0-9,.]+)",
            r"\$\s*([0-9,.]+)",
            r"US\$\s*([0-9,.]+)"
        ],
        "category_id": 4  # Hosting category
    },
    "hosting": {
        "sender_patterns": ["@digitalocean.com", "@hostinger.com", "@cpanel.net", "@hostgator.com", "@namecheap.com"],
        "subject_patterns": ["hosting renewal", "vps renewal", "cloud server", "hosting invoice"],
        "amount_patterns": [
            r"(?:idr|rp)\.?\s*([0-9,.]+)",
            r"\$\s*([0-9,.]+)",
            r"US\$\s*([0-9,.]+)"
        ],
        "category_id": 4  # Hosting category
    },
    "mobile": {
        "sender_patterns": ["@telkomsel.com", "@xl.co.id", "@indosat.com", "@tri.co.id"],
        "subject_patterns": ["tagihan bulanan", "monthly bill", "tagihan selular", "mobile bill"],
        "amount_patterns": [
            r"(?:idr|rp)\.?\s*([0-9,.]+)",
            r"(?:idr|rp)\s*([0-9,.]+)",
            r"total\s*(?:idr|rp)\.?\s*([0-9,.]+)"
        ],
        "category_id": 3  # Internet & Phone category
    },
    "internet": {
        "sender_patterns": ["@indihome.co.id", "@biznet.co.id", "@firstmedia.com", "@mncplay.id"],
        "subject_patterns": ["tagihan internet", "internet bill", "broadband bill", "fiber bill"],
        "amount_patterns": [
            r"(?:idr|rp)\.?\s*([0-9,.]+)",
            r"(?:idr|rp)\s*([0-9,.]+)",
            r"total\s*(?:idr|rp)\.?\s*([0-9,.]+)"
        ],
        "category_id": 3  # Internet & Phone category
    }
}

def clean_text(text: str) -> str:
    """Clean text for better parsing"""
    if not text:
        return ""
    # Convert to lowercase
    text = text.lower()
    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)
    # Remove non-breaking spaces
    text = text.replace('\xa0', ' ')
    return text.strip()

def decode_email_subject(subject: str) -> str:
    """Decode email subject to handle special characters and encodings"""
    if not subject:
        return ""
    
    decoded_subject = ""
    
    for part, encoding in decode_header(subject):
        if isinstance(part, bytes):
            # If it's bytes, decode it with the specified encoding or utf-8 as fallback
            try:
                decoded_part = part.decode(encoding or 'utf-8', errors='replace')
            except (LookupError, UnicodeDecodeError):
                decoded_part = part.decode('utf-8', errors='replace')
        else:
            # If it's already a string
            decoded_part = part
            
        decoded_subject += decoded_part
    
    return clean_text(decoded_subject)

def get_email_body(msg: email.message.Message) -> str:
    """Extract text from email body, whether it's plain text or HTML"""
    body = ""
    
    if msg.is_multipart():
        # Iterate through email parts
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            
            # Skip attachments
            if "attachment" in content_disposition:
                continue
            
            payload = part.get_payload(decode=True)
            if payload:
                # Handle text/plain parts
                if content_type == "text/plain":
                    try:
                        charset = part.get_content_charset() or 'utf-8'
                        body += payload.decode(charset, errors='replace')
                    except (LookupError, UnicodeDecodeError):
                        body += payload.decode('utf-8', errors='replace')
                
                # Handle HTML parts
                elif content_type == "text/html":
                    try:
                        charset = part.get_content_charset() or 'utf-8'
                        html = payload.decode(charset, errors='replace')
                        soup = BeautifulSoup(html, 'html.parser')
                        body += soup.get_text(separator=' ', strip=True)
                    except Exception as e:
                        logger.error(f"Error parsing HTML: {str(e)}")
    else:
        # Not multipart - get payload directly
        payload = msg.get_payload(decode=True)
        if payload:
            try:
                charset = msg.get_content_charset() or 'utf-8'
                body = payload.decode(charset, errors='replace')
                
                # If it's HTML, extract text
                if msg.get_content_type() == "text/html":
                    soup = BeautifulSoup(body, 'html.parser')
                    body = soup.get_text(separator=' ', strip=True)
            except Exception as e:
                logger.error(f"Error decoding payload: {str(e)}")
    
    return clean_text(body)

def extract_amount(text: str, patterns: List[str]) -> Optional[float]:
    """Extract amount from text using patterns"""
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                # Get the captured group and clean it
                amount_str = match.group(1)
                # Remove non-numeric characters except '.' and ','
                amount_str = re.sub(r'[^\d.,]', '', amount_str)
                # Replace comma with empty for internationalization
                amount_str = amount_str.replace(',', '')
                # Convert to float
                return float(amount_str)
            except (IndexError, ValueError) as e:
                logger.debug(f"Failed to extract amount from '{match.group(0)}': {str(e)}")
    
    return None

def extract_service_info(sender: str, subject: str, body: str) -> Tuple[Optional[str], Optional[int], Optional[float]]:
    """
    Attempt to identify subscription service, category, and amount from email
    Returns (service_name, category_id, amount)
    """
    sender = clean_text(sender)
    subject = clean_text(subject)
    body = clean_text(body)
    
    for service_name, patterns in KNOWN_SERVICES.items():
        # Check sender patterns
        sender_match = any(pattern in sender for pattern in patterns["sender_patterns"])
        
        # Check subject patterns
        subject_match = any(pattern in subject for pattern in patterns["subject_patterns"])
        
        if sender_match or subject_match:
            # Try to extract amount
            # First check subject for amount
            amount = extract_amount(subject, patterns["amount_patterns"])
            
            # If not found in subject, check body
            if amount is None:
                amount = extract_amount(body, patterns["amount_patterns"])
            
            return service_name, patterns["category_id"], amount
    
    # No match found
    return None, None, None

def extract_billing_date(text: str) -> Optional[datetime.date]:
    """Extract billing date from text"""
    # Common date patterns in Indonesian and English
    date_patterns = [
        # DD-MM-YYYY / DD/MM/YYYY
        r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})',
        # YYYY-MM-DD / YYYY/MM/DD
        r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})',
        # Month DD, YYYY (English)
        r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})',
        # DD Month YYYY (Indonesian)
        r'(\d{1,2})\s+(Januari|Februari|Maret|April|Mei|Juni|Juli|Agustus|September|Oktober|November|Desember)\s+(\d{4})',
    ]
    
    month_mapping = {
        'january': 1, 'februari': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
        'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12,
        'januari': 1, 'februari': 2, 'maret': 3, 'april': 4, 'mei': 5, 'juni': 6,
        'juli': 7, 'agustus': 8, 'september': 9, 'oktober': 10, 'november': 11, 'desember': 12
    }
    
    text = clean_text(text)
    
    # Check each pattern
    for pattern in date_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                # Different handling based on pattern
                if len(match.groups()) == 3:
                    if match.group(1).isdigit() and match.group(2).isdigit() and match.group(3).isdigit():
                        # DD-MM-YYYY or YYYY-MM-DD
                        if int(match.group(3)) > 31:  # It's YYYY-MM-DD
                            year = int(match.group(1))
                            month = int(match.group(2))
                            day = int(match.group(3))
                        else:  # It's DD-MM-YYYY
                            day = int(match.group(1))
                            month = int(match.group(2))
                            year = int(match.group(3))
                    else:
                        # Month name format
                        month_name = match.group(1).lower()
                        if month_name in month_mapping:
                            month = month_mapping[month_name]
                            if len(match.group(2)) <= 2:  # Check if the second group is a day
                                day = int(match.group(2))
                                year = int(match.group(3))
                            else:  # The second group is a year
                                day = int(match.group(3))
                                year = int(match.group(2))
                        else:
                            continue
                    
                    # Validate date
                    if 1 <= day <= 31 and 1 <= month <= 12 and 1900 <= year <= 2100:
                        return datetime(year, month, day).date()
            except (ValueError, IndexError):
                continue
    
    # No valid date found
    return None

def connect_to_mailbox() -> Optional[imaplib.IMAP4_SSL]:
    """Connect to the IMAP server and login"""
    if not settings.IMAP_SERVER or not settings.IMAP_USERNAME or not settings.IMAP_PASSWORD:
        logger.warning("IMAP settings not configured. Cannot connect to email server.")
        return None
    
    try:
        # Connect to the server
        if settings.IMAP_USE_SSL:
            mail = imaplib.IMAP4_SSL(settings.IMAP_SERVER, settings.IMAP_PORT)
        else:
            mail = imaplib.IMAP4(settings.IMAP_SERVER, settings.IMAP_PORT)
        
        # Login
        mail.login(settings.IMAP_USERNAME, settings.IMAP_PASSWORD)
        return mail
    except Exception as e:
        logger.error(f"Failed to connect to IMAP server: {str(e)}")
        return None

def fetch_emails(days_back: int = 30, folder: str = "INBOX") -> List[Dict[str, Any]]:
    """Fetch emails from the specified folder within the given time frame"""
    emails = []
    
    mail = connect_to_mailbox()
    if not mail:
        return emails
    
    try:
        # Select the mailbox
        result, _ = mail.select(folder)
        if result != 'OK':
            logger.error(f"Failed to select folder: {folder}")
            return emails
        
        # Calculate date range
        since_date = (datetime.now() - timedelta(days=days_back)).strftime("%d-%b-%Y")
        
        # Search for emails
        result, data = mail.search(None, f'(SINCE {since_date})')
        if result != 'OK':
            logger.error("Failed to search emails")
            return emails
        
        # Process each email
        for num in data[0].split():
            result, data = mail.fetch(num, '(RFC822)')
            if result != 'OK':
                logger.error(f"Failed to fetch email {num}")
                continue
            
            # Parse the email
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            # Extract email details
            sender = msg.get('From', '')
            subject = decode_email_subject(msg.get('Subject', ''))
            received_date = email.utils.parsedate_to_datetime(msg.get('Date', ''))
            body = get_email_body(msg)
            
            emails.append({
                'sender': sender,
                'subject': subject,
                'received_date': received_date,
                'body': body
            })
    
    except Exception as e:
        logger.error(f"Error fetching emails: {str(e)}")
    
    finally:
        # Close connection
        try:
            mail.close()
            mail.logout()
        except Exception:
            pass
    
    return emails

def parse_subscription_emails(db: Session, user_id: int, days_back: int = 30) -> List[Dict[str, Any]]:
    """
    Parse emails to detect subscription information
    Returns list of detected subscriptions
    """
    detected_subscriptions = []
    
    # Fetch emails
    emails = fetch_emails(days_back=days_back)
    if not emails:
        logger.info("No emails found to parse")
        return detected_subscriptions
    
    logger.info(f"Found {len(emails)} emails to parse")
    
    for email_data in emails:
        try:
            # Extract service information
            service_name, category_id, amount = extract_service_info(
                email_data['sender'],
                email_data['subject'],
                email_data['body']
            )
            
            if service_name and amount:
                # Try to extract billing date
                billing_date = extract_billing_date(email_data['body'])
                if not billing_date:
                    # If not found in body, use received date + 30 days as estimation
                    billing_date = (email_data['received_date'] + timedelta(days=30)).date()
                
                # Create subscription information
                subscription_info = {
                    'name': service_name.title(),
                    'amount': amount,
                    'billing_date': billing_date,
                    'category_id': category_id,
                    'email_sender': email_data['sender'],
                    'email_subject': email_data['subject'],
                    'detected_from_email': True
                }
                
                detected_subscriptions.append(subscription_info)
                logger.info(f"Detected subscription: {service_name.title()} - {amount}")
        except Exception as e:
            logger.error(f"Error parsing email: {str(e)}")
    
    # Remove duplicates (same service with different emails)
    unique_subscriptions = {}
    for sub in detected_subscriptions:
        service_name = sub['name'].lower()
        if service_name not in unique_subscriptions or unique_subscriptions[service_name]['amount'] < sub['amount']:
            unique_subscriptions[service_name] = sub
    
    return list(unique_subscriptions.values())

def create_subscriptions_from_emails(db: Session, user_id: int, days_back: int = 30) -> List[Dict[str, Any]]:
    """
    Parse emails and create subscriptions in database
    Returns list of created subscriptions
    """
    # Get detected subscriptions
    detected_subscriptions = parse_subscription_emails(db, user_id, days_back)
    created_subscriptions = []
    
    for sub_info in detected_subscriptions:
        try:
            # Check if the subscription already exists
            # This is a simple check by name - in real implementation, you might
            # want to check more fields or have a more sophisticated matching algorithm
            existing_subs = db.query(Subscription).filter(
                Subscription.user_id == user_id,
                Subscription.name.ilike(f"%{sub_info['name']}%")
            ).all()
            
            if existing_subs:
                logger.info(f"Subscription '{sub_info['name']}' already exists, skipping")
                continue
            
            # Set the billing cycle based on amount
            billing_cycle = "monthly"  # Default to monthly
            if sub_info['amount'] > 1000000:  # If amount is large, assume it's annual
                billing_cycle = "annual"
            
            # Calculate next billing date based on the detected billing date
            next_billing_date = sub_info['billing_date']
            
            # If billing date is in the past, adjust to next period
            today = datetime.now().date()
            if next_billing_date < today:
                if billing_cycle == "monthly":
                    # Move to next month, same day
                    if next_billing_date.month == 12:
                        next_billing_date = next_billing_date.replace(year=next_billing_date.year + 1, month=1)
                    else:
                        next_billing_date = next_billing_date.replace(month=next_billing_date.month + 1)
                elif billing_cycle == "annual":
                    # Move to next year, same month and day
                    next_billing_date = next_billing_date.replace(year=next_billing_date.year + 1)
            
            # Create the subscription
            sub_create = SubscriptionCreate(
                name=sub_info['name'],
                description=f"Automatically detected from email: {sub_info['email_subject']}",
                amount=sub_info['amount'],
                currency="IDR",  # Default to IDR, could be made smarter
                billing_cycle=billing_cycle,
                billing_day=next_billing_date.day,
                next_billing_date=next_billing_date,
                start_date=datetime.now().date(),
                auto_renew=True,
                reminder_days=3,
                website_url=None,
                notes=f"Created automatically from email parsing on {datetime.now().strftime('%Y-%m-%d')}",
                is_active=True,
                category_id=sub_info.get('category_id')
            )
            
            # Create in database
            db_subscription = create_subscription(db, sub_create, user_id)
            
            # Add to created list
            created_subscriptions.append({
                'id': db_subscription.id,
                'name': db_subscription.name,
                'amount': db_subscription.amount,
                'next_billing_date': db_subscription.next_billing_date,
                'billing_cycle': db_subscription.billing_cycle,
                'category_id': db_subscription.category_id,
                'detected_from_email': True
            })
            
            logger.info(f"Created subscription '{db_subscription.name}' from email")
        
        except Exception as e:
            logger.error(f"Error creating subscription from email: {str(e)}")
    
    return created_subscriptions

def scan_emails_for_all_users(db: Session, days_back: int = 30) -> Dict[int, List[Dict[str, Any]]]:
    """
    Scan emails for all users who have IMAP configured
    Returns a dictionary with user_id as key and list of created subscriptions as value
    """
    results = {}
    
    # Get all active users
    users = db.query(User).filter(User.is_active == True).all()
    
    for user in users:
        # This would usually be stored in user settings or preferences
        # For demo, we use global settings
        if settings.IMAP_SERVER and settings.IMAP_USERNAME and settings.IMAP_PASSWORD:
            logger.info(f"Scanning emails for user {user.id} ({user.email})")
            
            created_subs = create_subscriptions_from_emails(db, user.id, days_back)
            if created_subs:
                results[user.id] = created_subs
    
    return results