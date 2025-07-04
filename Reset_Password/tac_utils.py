import random
import string
from datetime import datetime, timedelta, timezone
from Reset_Password.email_credential import get_email_credentials
import smtplib
from email.mime.text import MIMEText
import re

def generate_tac_code(length=6):
    return ''.join(random.choices(string.digits, k=length))

def is_valid_email(email):
    # Basic email validation
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def send_tac_email(firebase_db, user_email, tac_code):
    if not is_valid_email(user_email):
        print("Invalid email address.")
        return False

    try:
        creds = get_email_credentials(firebase_db)
        if not creds:
            print("Email credentials not found in Firebase. Please ensure they are properly set up.")
            return False

        sender_email = creds.get("sender_email")
        sender_password = creds.get("sender_password")

        if not sender_email or not sender_password:
            print("Incomplete email credentials. Both email and password are required.")
            return False

        email_body = f"""
Dear User,

We have received a request for a password reset.

Your TAC code for password reset is:

{tac_code}

Please note that this code will be expired in 10 minutes.
If you didn't request this code, please ignore this email.

Best regards,
MMU Security Department
"""

        msg = MIMEText(email_body)
        msg["Subject"] = "ANPR System Password Reset - TAC Verification Code"
        msg["From"] = sender_email
        msg["To"] = user_email

        try:
            with smtplib.SMTP("smtp-mail.outlook.com", 587) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, [user_email], msg.as_string())
            print("TAC code sent successfully.")
            return True
        except smtplib.SMTPAuthenticationError:
            print("Failed to authenticate with Outlook. Please check your email and password.")
            return False
        except Exception as e:
            print(f"Failed to send email: {str(e)}")
            return False
    except Exception as e:
        print(f"Error in send_tac_email: {str(e)}")
        return False

def create_and_send_tac(user_email, firebase_db=None, user_id=None):
    if not is_valid_email(user_email):
        return None

    tac_code = generate_tac_code()

    # Store TAC data in Firebase
    if firebase_db and user_id:
        expires_at = datetime.utcnow().replace(tzinfo=timezone.utc) + timedelta(minutes=10)
        tac_data = {
            "code": tac_code,
            "expires_at": expires_at,
            "attempts_left": 3
        }
        try:
            firebase_db.db.collection("tac_verifications").document(user_id).set(tac_data)
        except Exception as e:
            print(f"Failed to store TAC data: {e}")

    # Send the TAC code via email
    if send_tac_email(firebase_db, user_email, tac_code):
        return tac_code
    return None

def verify_tac(user_id, tac_code, firebase_db):
    try:
        doc_ref = firebase_db.db.collection("tac_verifications").document(user_id)
        tac_data = doc_ref.get().to_dict()
        
        if not tac_data:
            return False
            
        # Check if TAC has expired
        expires_at = tac_data.get("expires_at")
        if expires_at and datetime.now(timezone.utc) > expires_at:
            doc_ref.delete()
            return False
            
        # Check attempts left
        attempts_left = tac_data.get("attempts_left", 0)
        if attempts_left <= 0:
            doc_ref.delete()
            return False
            
        # Verify the code
        if tac_data.get("code") == tac_code:
            doc_ref.delete()
            return True
            
        # Decrease attempts left
        doc_ref.update({"attempts_left": attempts_left - 1})
        return False
        
    except Exception as e:
        print(f"Error verifying TAC: {e}")
        return False 