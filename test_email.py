import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load .env if you use it locally, or set environment variables
# load_dotenv()

def test_email():
    """
    Standalone script to test email configuration.
    Useful for verifying credentials and recipient lists without running the full crawler.
    """
    user = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_APP_PASSWORD")
    recipient_field = os.getenv("RECIPIENT_EMAIL")

    print("--- Email Configuration Test ---")
    print(f"SMTP User: {user}")
    print(f"Recipients: {recipient_field}")
    
    if not all([user, password, recipient_field]):
        print("ERROR: Missing environment variables (EMAIL_USER, EMAIL_APP_PASSWORD, or RECIPIENT_EMAIL)")
        return

    recipients = [r.strip() for r in recipient_field.split(",") if r.strip()]
    
    try:
        msg = MIMEMultipart()
        msg["From"] = user
        msg["To"] = ", ".join(recipients)
        msg["Subject"] = "Crawler Email Test - Connection Success"
        
        body = "If you are reading this, your email configuration for the Bulletin Board Crawler is working correctly."
        msg.attach(MIMEText(body, "plain"))
        
        print("Connecting to smtp.gmail.com:587...")
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            print("Logging in...")
            server.login(user, password)
            print(f"Sending to {recipients}...")
            server.sendmail(user, recipients, msg.as_string())
            
        print("SUCCESS: Test email sent!")
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_email()
