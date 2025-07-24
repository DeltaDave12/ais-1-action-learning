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
from unity_game_embed import show_unity_game
from encouragement import get_encouragement
from speech_utils import transcribe_audio, synthesize_speech
import subprocess
import os
from doc_input_utils import get_doc_content

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

# Initialize session state variables
if "current_topic" not in st.session_state:
    st.session_state.current_topic = None
if "last_user_prompt" not in st.session_state:
    st.session_state.last_user_prompt = None
if "topic_model" not in st.session_state:
    st.session_state.topic_model = SentenceTransformer('all-MiniLM-L6-v2')

print("DEBUG: app.py loaded")
st.set_page_config(page_title="Multi-Conversation Chatbot", layout="wide")

# Remove phantom container and header at the very top, and make main block transparent
st.markdown("""
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
""", unsafe_allow_html=True)

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
            success, user = authenticate_user(username, password)
            if success:
                st.session_state.pending_2fa = True
                st.session_state.pending_username = username
                st.info('Enter your 2FA code from your authenticator app.')
            else:
                st.error(user)
    if st.session_state.pending_2fa:
        code = st.text_input('🔢 2FA Code')
        if st.button('✅ Verify 2FA', type='primary'):
            if verify_totp(st.session_state.pending_username, code):
                st.session_state.authenticated = True
                st.session_state.username = st.session_state.pending_username
                st.session_state.user_id = get_user_id(st.session_state.username)
                st.session_state.pending_2fa = False
                st.session_state.pending_username = None
                st.success('Login successful!')
                st.rerun()
            else:
                st.error('Invalid 2FA code.')
    st.stop()

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
selected_conv = st.sidebar.radio("Select Conversation", conversation_names, index=conversation_names.index(st.session_state.current_conv))
st.session_state.current_conv = selected_conv

if st.sidebar.button("New Conversation"):
    add_new_conversation()

if st.sidebar.button("Clear Current Conversation"):
    clear_current_conversation()

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

# Display the messages of the current conversation
st.subheader(f"Chat - {st.session_state.current_conv}")

messages = st.session_state.conversations[st.session_state.current_conv]

for idx, message in enumerate(messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Document Upload for Chat Input (per conversation) ---
uploader_key = f"uploader_{st.session_state.current_conv}"
doc_input_key = f"doc_input_{st.session_state.current_conv}"

uploaded_file = st.file_uploader("Upload a document", type=["txt", "docx"], key=uploader_key)
doc_content = get_doc_content(uploaded_file)

# Find the latest assistant message
latest_assistant_idx = None
latest_assistant_content = None
for idx in range(len(messages)-1, -1, -1):
    if messages[idx]["role"] == "assistant":
        latest_assistant_idx = idx
        latest_assistant_content = messages[idx]["content"]
        break

if latest_assistant_content is not None or (doc_content or st.session_state.get(doc_input_key)):
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Shorten"):
            try:
                print("DEBUG: Shorten button clicked")
                topic = st.session_state.current_topic or "the previous topic"
                # Use the current value of the text area if present, otherwise latest assistant content
                answer_to_shorten = st.session_state.get(doc_input_key) or latest_assistant_content or ""
                clean_answer = re.sub(r'\*\*.*?\*\*', '', answer_to_shorten)
                prompt = (
                    f"Topic: {topic}\n\n"
                    f"Answer: {clean_answer}\n\n"
                    "Summarize the above answer in 3-4 sentences using the CAG strategy. Be concise and do not repeat details. Only output the summary."
                )
                result = run_inference(prompt)
                summary = result['answer']
                st.markdown(summary)
                messages.append({"role": "assistant", "content": summary})
                # Display Listen button for the summary
                col_sum1, col_sum2 = st.columns([1, 1])
                with col_sum2:
                    audio_key = f"tts_audio_summary_{len(messages)-1}"
                    if st.button("🔊 Listen", key=audio_key):
                        import re
                        match = re.search(r'\*\*Answer:\*\*\s*(.*?)(\n\n|$)', summary, re.DOTALL)
                        answer_text = match.group(1).strip() if match else summary
                        with st.spinner("Synthesizing speech..."):
                            try:
                                audio_bytes = synthesize_speech(answer_text)
                                st.audio(audio_bytes, format="audio/wav")
                            except Exception as e:
                                st.error(f"Speech synthesis failed: {e}")
            except Exception as e:
                print("ERROR in shorten button:", e)
                st.error(f"Error: {e}")
    with col2:
        audio_key = f"tts_audio_{latest_assistant_idx}_beside"
        if st.button("🔊 Listen", key=audio_key):
            # Extract only the answer part from the assistant message
            import re
            match = re.search(r'\*\*Answer:\*\*\s*(.*?)(\n\n|$)', latest_assistant_content or "", re.DOTALL)
            answer_text = match.group(1).strip() if match else (latest_assistant_content or "")
            with st.spinner("Synthesizing speech..."):
                try:
                    audio_bytes = synthesize_speech(answer_text)
                    st.audio(audio_bytes, format="audio/wav")
                except Exception as e:
                    st.error(f"Speech synthesis failed: {e}")

# --- Chat Input ---
if doc_content:
    prompt = st.text_area("What is your question?", value=doc_content, height=200, key=doc_input_key)
else:
    prompt = st.chat_input("What is your question?")

if prompt:
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
            encouragement = get_encouragement(result['emotion'])
            response = f"**Emotion:** {result['emotion']}\n\n**Strategy:** {display_strategy}\n\n**Answer:** {result['answer']}\n\n---\n{encouragement}"
            print("LENGTH OF RESPONSE:", len(response))
            st.markdown(response)
    messages.append({"role": "assistant", "content": response})
    st.session_state.last_user_prompt = prompt
    # Only clear the text area for this conversation after sending
    st.session_state[doc_input_key] = ""

# Save back messages to state (actually it's mutable so not strictly necessary)
st.session_state.conversations[st.session_state.current_conv] = messages

# Place the Export Conversation as PDF button on the right
col1, col2, col3 = st.columns([1, 1, 1])
with col3:
    if st.button("Export Conversation as PDF"):
        conversation = st.session_state.conversations[st.session_state.current_conv]
        export_conversation_to_pdf(conversation, "conversation_export.pdf")
        with open("conversation_export.pdf", "rb") as f:
            st.download_button("Download PDF", f, file_name="conversation_export.pdf")
