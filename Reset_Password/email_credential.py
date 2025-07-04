import os
from dotenv import load_dotenv
from cryptography.fernet import Fernet

load_dotenv()

def encrypt_value(plain_value):
    encryption_key = os.getenv("ENCRYPTION_KEY")
    if encryption_key is None:
        raise Exception("ENCRYPTION_KEY is not set in the environment.")
    fernet = Fernet(encryption_key.encode())
    encrypted_value = fernet.encrypt(plain_value.encode())
    return encrypted_value.decode()


def decrypt_value(encrypted_value):
    encryption_key = os.getenv("ENCRYPTION_KEY")
    if encryption_key is None:
        raise Exception("ENCRYPTION_KEY is not set in the environment.")
    fernet = Fernet(encryption_key.encode())
    decrypted_value = fernet.decrypt(encrypted_value.encode())
    return decrypted_value.decode()


def set_email_credentials(firebase_db_instance, sender_email, plain_password):
    encrypted_email = encrypt_value(sender_email)
    encrypted_password = encrypt_value(plain_password)
    credentials_data = {
        "sender_email": encrypted_email,
        "sender_password": encrypted_password
    }
    firebase_db_instance.db.collection("config").document("email_credentials").set(credentials_data)
    print("Email credentials stored securely.")


def get_email_credentials(firebase_db_instance):
    doc_ref = firebase_db_instance.db.collection("config").document("email_credentials")
    doc = doc_ref.get()
    if doc.exists:
        credentials = doc.to_dict()
        encrypted_email = credentials.get("sender_email")
        if encrypted_email:
            credentials["sender_email"] = decrypt_value(encrypted_email)
        encrypted_password = credentials.get("sender_password")
        if encrypted_password:
            credentials["sender_password"] = decrypt_value(encrypted_password)
        return credentials
    else:
        return None
