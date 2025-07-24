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
from ui.api_utilities import create_session_conversation, get_session_conversations, get_session_conversation, update_session_conversation, delete_session_conversation, get_user_by_username, load_user_conversations, get_next_session_id, get_last_user_and_assistant, verify_totp_code
import asyncio
from datetime import datetime, timezone
from unity_game_embed import show_unity_game
from encouragement import get_encouragement
from speech_utils import transcribe_audio, synthesize_speech
import subprocess
import os

print("DEBUG: app.py loaded")
st.set_page_config(page_title="Multi-Conversation Chatbot", layout="wide")

# Hide the video placeholder from webrtc_streamer (audio-only mode)
st.markdown(
    '''
    <style>
    .stVideo {display: none !important;}
    [data-testid="stVideo"] {display: none !important;}
    .rtc-video {display: none !important;}
    .rtc-video-container {display: none !important;}
    </style>
    ''',
    unsafe_allow_html=True
)

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
if "show_secondary_feedback_options" not in st.session_state:
    st.session_state.show_secondary_feedback_options = False # Controls visibility of Shorten/Lengthen/etc.
if "is_feedback_postive" not in st.session_state:
    st.session_state.is_feedback_postive = None # To track if feedback positive or negative
if "is_ai_thinking" not in st.session_state:
    st.session_state.is_ai_thinking = False
if 'last_conv_for_last_user_prompt' not in st.session_state:
    st.session_state.last_conv_for_last_user_prompt = None

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

def reset_all_states():
    # Make a list of keys first to avoid "dictionary changed size during iteration" error
    for key in list(st.session_state.keys()):
        del st.session_state[key]

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
            print("IN REGISTER MODE")
            success, result = register_user(username, password)
            if success:
                st.success(f"Registered! Your user ID: {result['user_id']}")
                # Prepare payload data for new session conversation with empty messages
                user_id = result['user_id']
                totp_secret = result['totp_secret']
                # st.info(f"Set up your authenticator app with this secret: {result['totp_secret']}")
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
                    totp_secret=totp_secret
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
            else:
                st.error(result)
    else:
        if st.button('🔓 Login', type='primary'):
            #success, user = authenticate_user(username, password)
            #print("success: ", success, " user: ", user)
            #if success:
            #success, user = authenticate_user(username, password)
            try:
                users = asyncio.run(get_user_by_username(username))
            except Exception as e:
                st.error(f"Error fetching user info: {e}")
                users = []
            if not users:
                st.error("User does not exist. Please register.")
            else:
                authenticated_user_record = None
                for user_rec in users:
                    # Check if password is not None and matches
                    if user_rec.get("password") is not None and user_rec.get("password") == password:
                        authenticated_user_record = user_rec
                        break # Found a matching user record, exit loop
                if authenticated_user_record is None:
                    # If no user record found with a matching non-null password
                    st.error("Incorrect password.")
                else:
                    # Password matched - proceed with 2FA flow
                    st.session_state.pending_2fa = True
                    st.session_state.pending_username = username
                    st.info('Enter your 2FA code from your authenticator app.')
        if st.session_state.pending_2fa:
            code = st.text_input('🔢 2FA Code')
            if st.button('✅ Verify 2FA', type='primary'):
                if asyncio.run(verify_totp_code(st.session_state.pending_username, code)):
                # if 1 == 1:
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

def add_new_conversation():
    # Generate a new unique conversation name
    existing = st.session_state.conversations.keys()
    i = 1
    while f"Conversation {i}" in existing:
        i += 1
    new_name = f"Conversation {i}"
    st.session_state.conversations[new_name] = []
    st.session_state.current_conv = new_name
    st.session_state.is_ai_thinking = False
    st.session_state.show_secondary_feedback_options = False
    st.session_state.is_feedback_postive = None

def is_new_topic(new_prompt, last_prompt, threshold=0.4):
    if not last_prompt:
        return True
    emb1 = st.session_state.topic_model.encode([new_prompt])[0]
    emb2 = st.session_state.topic_model.encode([last_prompt])[0]
    similarity = util.cos_sim(emb1, emb2).item()
    return similarity < threshold

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
        st.session_state.conversations.pop(conv_key)
        asyncio.run(delete_session_conversation(conversation_id=db_id))
    st.session_state.is_ai_thinking = False
    st.session_state.show_secondary_feedback_options = False
    st.session_state.is_feedback_postive = None
    st.rerun()

if st.sidebar.button("Log Out"):
    reset_all_states()
    st.rerun()

# Add sidebar navigation for Unity game    
if 'page' not in st.session_state:           
    st.session_state.page = 'Chatbot'
                                                            
page = st.sidebar.radio('Navigation', ['Chatbot', 'Unity Game'], index=0)
st.session_state.page = page

if st.session_state.page == 'Unity Game':
    # Start the Unity game server if not already running
    server_command = [
        "python", "-m", "http.server", "8502"
    ]
    server_cwd = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Unity_game"))
    try:
        subprocess.Popen(server_command, cwd=server_cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        st.warning(f"Could not start Unity game server automatically: {e}")
    # Open the Unity game in a new browser tab automatically
    js = """
    <script>
    window.open('http://localhost:8502/index.html', '_blank');
    </script>
    """
    st.markdown(js, unsafe_allow_html=True)
    show_unity_game()
    st.stop()

if st.session_state.username:
    # Use st.sidebar.markdown to place content in the sidebar
    # You might want some styling to make it look like a proper footer
    st.sidebar.markdown("---") # Optional: A separator line
    st.sidebar.markdown(f"Logged in as: **{st.session_state.username}**")

# Display the messages of the current conversation
st.subheader(f"Chat - {st.session_state.current_conv}")

messages = st.session_state.conversations.get(st.session_state.current_conv, [])

if st.session_state.current_conv != st.session_state.last_conv_for_last_user_prompt:
    if messages:
        last_user_message_content = None
        for msg in reversed(messages):
            if msg.get('role') == 'user' or msg.get('owner') == 'user':
                last_user_message_content = msg.get('content') or msg.get('message')
                if last_user_message_content:
                    break
        st.session_state.last_user_prompt = last_user_message_content
    else:
        # No messages, clear last_user_prompt
        st.session_state.last_user_prompt = None
        
    st.session_state.last_conv_for_last_user_prompt = st.session_state.current_conv

for message in messages:
    with st.chat_message(message.get("role", message.get("owner", "user"))):  # fallback role
        st.markdown(message.get("content", message.get("message", "")))

prompt = st.chat_input("What is your question?")

if prompt:
    messages = st.session_state.conversations[st.session_state.current_conv]
    # Add user message
    print("DEBUG: User prompt is", prompt)
    messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.show_secondary_feedback_options = False
    st.session_state.is_feedback_postive = None
    st.session_state.is_ai_thinking = True
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
                last_user, last_assistant = asyncio.run(get_last_user_and_assistant(messages))
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
            encouragement = get_encouragement(result['emotion'])
            response = f"**Emotion:** {result['emotion']}\n\n**Strategy:** {display_strategy}\n\n**Answer:** {result['answer']}\n\n{encouragement}"
            st.markdown(response)
    messages.append({"role": "assistant", "content": response})
    st.session_state.last_user_prompt = prompt
    st.session_state.is_ai_thinking = False
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

if messages and messages[-1]["role"] == "assistant":
    st.markdown("---")  # Separator for clarity

    col1, col2 = st.columns([1, 1])  # Two equal columns side by side

    with col1:
        if st.button("Export Conversation as PDF"):
            conversation = st.session_state.conversations[st.session_state.current_conv]
            export_conversation_to_pdf(conversation, "conversation_export.pdf")
            with open("conversation_export.pdf", "rb") as f:
                st.download_button("Download PDF", f, file_name="conversation_export.pdf")

    with col2:
        audio_key = f"tts_audio_summary_{len(messages) - 1}"
        if st.button("🔊 Listen", key=audio_key):
            import re

            latest_assistant_content = messages[-1]["content"]
            # Extract the answer part after "**Answer:**"
            match = re.search(r'\*\*Answer:\*\*\s*(.*)', latest_assistant_content, re.DOTALL)
            answer_text = match.group(1).strip() if match else latest_assistant_content

            with st.spinner("Synthesizing speech..."):
                try:
                    audio_bytes = synthesize_speech(answer_text)
                    st.audio(audio_bytes, format="audio/wav")
                except Exception as e:
                    st.error(f"Speech synthesis failed: {e}")


if messages and messages[-1]["role"] == "assistant":
    st.write("Are you satisfied with this answer?")
    if st.session_state.is_ai_thinking == False:

        if st.button("Yes", key="feedback_yes"):
                print("DEBUG: User chose YES")
                st.session_state.is_feedback_postive = True
                st.session_state.show_secondary_feedback_options = False # Ensure this is hidden
                st.rerun()

        if st.button("No", key="feedback_no"):
                st.write("Okay, how can I help improve it?")
                print("DEBUG: User chose NO")
                st.session_state.show_secondary_feedback_options = True # Show secondary options
                # Here you would typically send negative feedback to your backend/log

    if st.session_state.is_feedback_postive == True:
        st.write("Thanks for your positive feedback!")

    if st.session_state.show_secondary_feedback_options:
        last_answer = messages[-1]["content"] # Get the answer to work on
        if st.button("Shorten", key="secondary_shorten"):
            try:
                print("DEBUG: Shorten button clicked (secondary)")
                clean_answer = re.sub(r'\*\*.*?\*\*', '', last_answer)
                # Build the prompt for shortening as a new user message
                new_prompt = (
                    f"Answer: {clean_answer}\n\n"
                    "Summarize the above answer in 3-4 sentences using the CAG strategy. "
                    "Be concise and do not repeat details. Only output the summary."
                )
                st.session_state.conversations[st.session_state.current_conv] = messages
                # Hide secondary feedback options after action
                st.session_state.show_secondary_feedback_options = False
                st.session_state.is_ai_thinking = True
                # Generate AI response
                with st.spinner("Generating shortened response..."):
                    result = run_inference(new_prompt)
                    response = result['answer']
                # Append AI response as assistant message
                messages.append({"role": "assistant", "content": response})
                st.session_state.conversations[st.session_state.current_conv] = messages    
                st.session_state.is_ai_thinking = False
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
                st.rerun()
            except Exception as e:
                st.error(f"Error shortening: {e}")


        if st.button("Lengthen", key="secondary_lengthen"):
            try:
                print("DEBUG: Lengthen button clicked")
                clean_answer = re.sub(r'\*\*.*?\*\*', '', last_answer)
                new_prompt = (
                    f"Answer: {clean_answer}\n\n"
                    "Elaborate on the above answer, adding more detail and examples. Expand it to about 1.5 times its current length. Only output the expanded answer."
                )
                st.session_state.conversations[st.session_state.current_conv] = messages
                st.session_state.show_secondary_feedback_options = False
                st.session_state.is_ai_thinking = True
                # Generate AI response
                with st.spinner("Generating a longer response..."):
                    result = run_inference(new_prompt)
                    response = result['answer']
                # Append AI response as assistant message
                messages.append({"role": "assistant", "content": response})
                st.session_state.conversations[st.session_state.current_conv] = messages    
                # Hide secondary feedback options after action
                st.session_state.is_ai_thinking = False
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
                st.rerun()
            except Exception as e:
                st.error(f"Error lengthening: {e}")

        if st.button("Change Source", key="secondary_source"):
            print("DEBUG: Change Source button clicked")
            original_prompt_for_llm = st.session_state.last_user_prompt
            if original_prompt_for_llm:
                    new_prompt = (
                    f"Given the user's original query: '{original_prompt_for_llm}', and the previous answer was unsatisfactory "
                    f"because they want a 'change of source' or 'different perspective'. Please provide a new answer focusing "
                    f"on a different angle, source, or approach. Only output the new answer."
                )
                    st.session_state.show_secondary_feedback_options = False
                    st.session_state.is_ai_thinking = True
                    with st.spinner("Generating answer from a different perspective/source..."):
                        result = run_inference(new_prompt)
                    response = result['answer']
                    messages.append({"role": "assistant", "content": response})
                    st.session_state.conversations[st.session_state.current_conv] = messages    
                    # Hide secondary feedback options after action
                    st.session_state.is_ai_thinking = False
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
                    st.rerun()
            else:
                    st.warning("Cannot change source: original prompt not available.")
            
            # Reset feedback state as action is taken