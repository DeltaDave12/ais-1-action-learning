import streamlit as st
import time
from inference_pipeline import run_inference
from sentence_transformers import SentenceTransformer, util
import re
from export_pdf import export_conversation_to_pdf
from topic_cag_logic import count_consecutive_same_topic
from auth import register_user, authenticate_user, verify_totp, get_user_id
import qrcode
from io import BytesIO
from api_requests import create_session_conversation, get_session_conversations, get_session_conversation, update_session_conversation, delete_session_conversation, get_user_by_username
import asyncio
from datetime import datetime, timezone

print("DEBUG: app.py loaded")
st.set_page_config(page_title="Multi-Conversation Chatbot", layout="wide")

async def load_user_conversations(user_id: str):
    all_sessions = await get_session_conversations(user_id=user_id)  # Filter on user_id backend side

    conversations = {}
    sessionid_to_id = {}
    for session in all_sessions:
        sid = session.get('session_id')
        db_id = session.get('id')
        if sid is None:  # Skip rows with no session id
            continue
        sid_str = str(sid)
        conversations[sid_str] = session.get('messages', [])
        sessionid_to_id[sid_str] = db_id
    return conversations, sessionid_to_id

async def get_next_session_id(user_id: str) -> int:
    sessions = await get_session_conversations(user_id=user_id)
    session_ids = [s.get("session_id") for s in sessions if s.get("session_id") is not None]
    if session_ids:
        max_id = max(session_ids)
        return max_id + 1
    else:
        return 1  # start from 1 if no sessions exist


# Remove phantom container and header at the very top, and make main block transparent
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 0rem !important;
        margin-top: 0rem !important;
        background: transparent !important;
        box-shadow: none !important;
        border-radius: 0 !important;
    }
    header[data-testid="stHeader"] {
        height: 0rem;
        min-height: 0rem;
        visibility: hidden;
        display: none;
        box-shadow: none;
    }
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    </style>
    """
, unsafe_allow_html=True)

# --- UI States ---
if "current_topic" not in st.session_state:
    st.session_state.current_topic = None
if "last_user_prompt" not in st.session_state:
    st.session_state.last_user_prompt = None
if "topic_model" not in st.session_state:
    st.session_state.topic_model = SentenceTransformer('all-MiniLM-L6-v2')

# --- Authentication UI ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'pending_2fa' not in st.session_state:
    st.session_state.pending_2fa = False
if 'pending_username' not in st.session_state:
    st.session_state.pending_username = None
if 'sessionid_to_id' not in st.session_state:
    st.session_state.sessionid_to_id = {}
if "conversations" not in st.session_state:
    st.session_state.conversations = {}


if not st.session_state.authenticated:
    st.markdown("""
        <style>
        .block-container {
            max-width: 60%;
            margin: 2rem auto !important;
            padding-top: 4rem !important;
            background: #fff !important;
            border-radius: 16px !important;
            box-shadow: 0 4px 24px rgba(0,0,0,0.08) !important;
        }
        .login-title {
            text-align: center;
            font-size: 2.2rem;
            font-weight: 700;
            margin-bottom: 1.2rem;
        }
        .login-subtext {
            text-align: center;
            color: #888;
            margin-bottom: 1.2rem;
        }
        .stButton>button {
            width: 100%;
            border-radius: 8px;
            font-size: 1.1rem;
            padding: 0.6rem 0;
        }
        </style>
    """, unsafe_allow_html=True)
    st.markdown('<div class="login-title">🔐 Login or Register</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-subtext">Welcome to <b>AL_Git Chatbot</b>. Please log in or create an account to continue.</div>', unsafe_allow_html=True)
    auth_mode = st.radio('Choose mode', ['Login', 'Register'], horizontal=True)
    username = st.text_input('👤 Username')
    password = st.text_input('🔑 Password', type='password')
    if auth_mode == 'Register':
        if st.button('📝 Register', type='primary'):
            success, result = register_user(username, password)
            if success:
                st.success(f"Registered! Your user ID: {result['user_id']}")
                # Prepare payload data for new session conversation with empty messages
                user_id = result['user_id']
                try:
                    initial_session_id = asyncio.run(get_next_session_id(user_id))
                except Exception as e:
                    st.error(f"Could not determine new session_id: {e}")
                    initial_session_id = 1  # fallback

                payload_task = create_session_conversation(
                    session_id=initial_session_id,
                    last_updated=datetime.now(timezone.utc).isoformat(),
                    messages=[],
                    username=username,
                    password=password,
                    user_id=user_id,
                )
                try:
                    created_session = asyncio.run(payload_task)
                    st.success(f"User session entry created successfully with session_id {initial_session_id}.")
                    # Update session id mapping in state if needed
                    st.session_state.sessionid_to_id[str(initial_session_id)] = created_session.get("id")
                    # Also add to conversations state
                    st.session_state.conversations[str(initial_session_id)] = []
                except Exception as e:
                    st.error(f"Failed to create user session: {e}")

                st.info(f"Set up your authenticator app with this secret: {result['totp_secret']}")
                app_name = 'AL_Git'
                totp_uri = f"otpauth://totp/{app_name}:{username}?secret={result['totp_secret']}&issuer={app_name}"
                qr = qrcode.make(totp_uri)
                buf = BytesIO()
                qr.save(buf, format='PNG')
                st.image(buf.getvalue(), caption='Scan this QR code with Google Authenticator')
                st.markdown("""
                **How to use Google Authenticator:**
                1. Open the Google Authenticator app on your phone.
                2. Tap the "+" button to add a new account.
                3. Choose "Scan a QR code" and scan the QR code above.
                4. If you can't scan, choose "Enter a setup key" and enter the secret above.
                5. After setup, use the 6-digit code shown in the app to log in.
                """)
            else:
                st.error(result)
    else:
        if st.button('🔓 Login', type='primary'):
            #success, user = authenticate_user(username, password)
            #print("success: ", success, " user: ", user)
            #if success:
                try:
                    users = asyncio.run(get_user_by_username(username))
                except Exception as e:
                    st.error(f"Error fetching user info: {e}")
                    users = []
                if not users:
                    st.error("User does not exist. Please register.")
                else:
                    # Check password locally (assuming same password for all user entries, or check first)
                    user_record = users[0]
                    print("user_record", user_record)
                    if user_record.get("password") != password:
                        st.error("Incorrect password.")
                    else:
                        # Password matched - proceed with 2FA flow
                        st.session_state.pending_2fa = True
                        st.session_state.pending_username = username
                        st.info('Enter your 2FA code from your authenticator app.')
    if st.session_state.pending_2fa:
        code = st.text_input('🔢 2FA Code', key='two_factor_code')
        if st.button('✅ Verify 2FA', key='verify_2fa_button'):
            print("st.session_state.pending_username: ", st.session_state.pending_username)
            print("code: ", code)
            # if verify_totp(st.session_state.pending_username, code):
            if 1 == 1:
                st.session_state.authenticated = True
                st.session_state.username = st.session_state.pending_username
                users = asyncio.run(get_user_by_username(username))
                user_record = users[0]
                st.session_state.user_id = user_record.get("user_id")
                st.session_state.pending_2fa = False
                st.session_state.pending_username = None
                st.success('Login successful!')
                st.session_state.conversations, st.session_state.sessionid_to_id = asyncio.run(load_user_conversations(st.session_state.user_id))
                st.rerun()  # better practice than st.rerun()
                if not st.session_state.conversations:
                    # If user has no conversation, create a blank one with session_id=1 or generated
                    initial_session_id = 1
                    empty_session = {
                        "session_id": initial_session_id,
                        "last_updated": datetime.now(timezone.utc).isoformat(),
                        "messages": [],
                        "username": st.session_state.username,
                        "password": "",  # or omit
                        "user_id": st.session_state.user_id
                    }
                    # Push empty session to backend
                    # await create_session_conversation(**empty_session) - async handled appropriately
                    st.session_state.conversations = {str(initial_session_id): []}
                st.session_state.current_conv = list(st.session_state.conversations.keys())[0]
                        # st.session_state.conversations = asyncio.run(load_user_conversations(user_id))
            else:
                st.error('Invalid 2FA code.')

    st.stop()

# Move st.title to after authentication
if st.session_state.authenticated:
    st.title("🤖 Multi-Conversation Chatbot")

# Initialize session state for conversations store and current selected conversation
if "conversations" not in st.session_state:
    st.session_state.conversations = {
        "Conversation 1": []  # start with one empty conversation
    }
if "current_conv" not in st.session_state:
    st.session_state.current_conv = "Conversation 1"

def clear_current_conversation():
    st.session_state.conversations[st.session_state.current_conv] = []

def add_new_conversation():
    # Generate a new unique conversation name
    existing = st.session_state.conversations.keys()
    i = 1
    while f"Conversation {i}" in existing:
        i += 1
    new_name = f"Conversation {i}"
    st.session_state.conversations[new_name] = []
    st.session_state.current_conv = new_name

def is_new_topic(new_prompt, last_prompt, threshold=0.4):
    if not last_prompt:
        return True
    emb1 = st.session_state.topic_model.encode([new_prompt])[0]
    emb2 = st.session_state.topic_model.encode([last_prompt])[0]
    similarity = util.cos_sim(emb1, emb2).item()
    return similarity < threshold

def get_last_user_and_assistant(messages):
    last_user = None
    last_assistant = None
    for msg in reversed(messages[:-1]):  # Exclude the current user prompt
        if last_assistant is None and msg["role"] == "assistant":
            last_assistant = msg["content"]
        elif last_user is None and msg["role"] == "user":
            last_user = msg["content"]
        if last_user and last_assistant:
            break
    return last_user, last_assistant

# Sidebar for selecting conversations
st.sidebar.header("Conversations")
conversation_names = list(st.session_state.conversations.keys())

selected_conv = st.sidebar.radio("Select Conversation", conversation_names,
                                 index=conversation_names.index(st.session_state.current_conv)
                                 if st.session_state.current_conv in conversation_names else 0)
st.session_state.current_conv = selected_conv

if st.sidebar.button("New Conversation"):
    # Create new session_id: get max existing + 1
    def parse_int_or_none(s):
        try:
            return int(s)
        except (ValueError, TypeError):
            return None

    int_keys = [parse_int_or_none(k) for k in st.session_state.conversations.keys()]
    int_keys = [k for k in int_keys if k is not None]

    if int_keys:
        max_id = max(int_keys)
    else:
        max_id = 0  # no valid integer keys; start from 0
    new_session_id = str(max_id + 1)
    st.session_state.conversations[new_session_id] = []
    st.session_state.current_conv = new_session_id

    # Also push it to backend with empty messages
    new_session = {
        "session_id": int(new_session_id),
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "messages": [],
        "username": st.session_state.username,
        "password": "",  # or omit
        "user_id": st.session_state.user_id,
    }
    created_session = asyncio.run(create_session_conversation(**new_session))
    new_id = str(new_session_id)
    st.session_state.conversations[new_id] = []
    st.session_state.sessionid_to_id[new_id] = created_session.get("id")
    st.session_state.current_conv = new_id


if st.sidebar.button("Clear Current Conversation"):
    conv_key = st.session_state.current_conv
    db_id = st.session_state.sessionid_to_id.get(conv_key)

    if db_id is None:
        st.error(f"Cannot find DB conversation id for session {conv_key}.")
    else:
        st.session_state.conversations[conv_key] = []
        asyncio.run(update_session_conversation(
            conversation_id=db_id,
            update_fields={"messages": [], "last_updated": datetime.now(timezone.utc).isoformat()}
        ))



# Display the messages of the current conversation
st.subheader(f"Chat - {st.session_state.current_conv}")

messages = st.session_state.conversations.get(st.session_state.current_conv, [])

for message in messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("What is your question?")

if prompt:
    messages = st.session_state.conversations[st.session_state.current_conv]
    # Add user message
    print("DEBUG: User prompt is", prompt)
    messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response using inference_pipeline
    with st.chat_message("assistant"):
        print("DEBUG: Assistant block entered")

        with st.spinner("Thinking..."):
            # Check for repeated topic
            same_topic_count = count_consecutive_same_topic(messages, st.session_state.topic_model, threshold=0.4)
            force_cag = same_topic_count >= 3
            # Call your backend inference function
            if is_new_topic(prompt, st.session_state.last_user_prompt, threshold=0.1):
                st.session_state.current_topic = prompt
                result = run_inference(prompt)
            else:
                last_user, last_assistant = get_last_user_and_assistant(messages)
                if last_user and last_assistant:
                    continuation_prompt = (
                        f"User: {last_user}\n"
                        f"Assistant: {last_assistant}\n"
                        f"User: {prompt}\n"
                        "Assistant:"
                    )
                    result = run_inference(continuation_prompt)
                else:
                    result = run_inference(prompt)
            # Override strategy if needed
            display_strategy = "CAG" if force_cag else result['strategy']
            response = f"**Emotion:** {result['emotion']}\n\n**Strategy:** {display_strategy}\n\n**Answer:** {result['answer']}"
            print("LENGTH OF RESPONSE:", len(response))
            st.markdown(response)
    messages.append({"role": "assistant", "content": response})
    st.session_state.last_user_prompt = prompt
    st.session_state.conversations[st.session_state.current_conv] = messages

    update_fields = {
        "messages": messages,
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "username": st.session_state.username,
        "user_id": st.session_state.user_id
    }
    db_id = st.session_state.sessionid_to_id.get(st.session_state.current_conv)
    if db_id is None:
        st.error("Cannot find conversation id in session mapping!")
    else:
        asyncio.run(update_session_conversation(conversation_id=db_id, update_fields=update_fields))



# Save back messages to state (actually it's mutable so not strictly necessary)
st.session_state.conversations[st.session_state.current_conv] = messages

shorten_response = None
if messages and messages[-1]["role"] == "assistant":
    last_answer = messages[-1]["content"]
    if st.button("Shorten"):
        try:
            print("DEBUG: Shorten button clicked")
            topic = st.session_state.current_topic or "the previous topic"
            clean_answer = re.sub(r'\*\*.*?\*\*', '', last_answer)
            prompt = (
                f"Topic: {topic}\n\n"
                f"Answer: {clean_answer}\n\n"
                "Summarize the above answer in 3-4 sentences using the CAG strategy. Be concise and do not repeat details. Only output the summary."
            )
            result = run_inference(prompt)
            summary = result['answer']
            st.markdown(summary)
            messages.append({"role": "assistant", "content": summary})
        except Exception as e:
            print("ERROR in shorten button:", e)
            st.error(f"Error: {e}")

# Place the Export Conversation as PDF button on the right
col1, col2, col3 = st.columns([1, 1, 1])
with col3:
    if st.button("Export Conversation as PDF"):
        conversation = st.session_state.conversations[st.session_state.current_conv]
        export_conversation_to_pdf(conversation, "conversation_export.pdf")
        with open("conversation_export.pdf", "rb") as f:
            st.download_button("Download PDF", f, file_name="conversation_export.pdf")
