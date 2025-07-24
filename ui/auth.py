import streamlit as st
import uuid
import pyotp
import hashlib

def ensure_user_db():
    if 'user_db' not in st.session_state:
        st.session_state.user_db = {}

# Helper to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Register a new user
def register_user(username, password):
    ensure_user_db()
    if username in st.session_state.user_db:
        return False, 'Username already exists.'
    user_id = str(uuid.uuid4())
    totp_secret = pyotp.random_base32()
    st.session_state.user_db[username] = {
        'password_hash': hash_password(password),
        'user_id': user_id,
        'totp_secret': totp_secret
    }
    return True, {'user_id': user_id, 'totp_secret': totp_secret}

# Authenticate username and password
def authenticate_user(username, password):
    ensure_user_db()
    user = st.session_state.user_db.get(username)
    if not user:
        return False, 'User not found.'
    if user['password_hash'] != hash_password(password):
        return False, 'Incorrect password.'
    return True, user

# Verify TOTP code
def verify_totp(username, code):
    ensure_user_db()
    user = st.session_state.user_db.get(username)
    if not user:
        return False
    totp = pyotp.TOTP(user['totp_secret'])
    return totp.verify(code)

# Get user ID
def get_user_id(username):
    ensure_user_db()
    user = st.session_state.user_db.get(username)
    if user:
        return user['user_id']
    return None 