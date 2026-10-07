import smtplib
from email.mime.text import MIMEText
import config
import logging

log = logging.getLogger(__name__)

def send_email_report(subject: str, body: str):
    if not config.GMAIL_ADDRESS or not config.GMAIL_APP_PASSWORD:
        log.info("Gmail credentials not set, skipping email notification.")
        return
    
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = config.GMAIL_ADDRESS
    msg["To"] = config.GMAIL_ADDRESS
    
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(config.GMAIL_ADDRESS, config.GMAIL_APP_PASSWORD)
            server.send_message(msg)
        log.info("Email report sent successfully!")
    except Exception as e:
        log.error(f"Failed to send email: {e}")
