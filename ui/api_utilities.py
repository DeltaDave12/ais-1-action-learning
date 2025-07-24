import httpx
from typing import Optional, List, Dict, Any
import pyotp

API_BASE_URL = "http://localhost:8000"

async def create_session_conversation(
    session_id: Optional[int] = None,
    last_updated: Optional[str] = None,   # ISO datetime string
    messages: Optional[List[Dict[str, Any]]] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    user_id: Optional[str] = None,
    totp_secret: Optional[str] = None
) -> Dict[str, Any]:
    payload = {
        "session_id": session_id,
        "last_updated": last_updated,
        "messages": messages,
        "username": username,
        "password": password,
        "user_id": user_id,
        "totp_secret": totp_secret
    }
    payload = {k: v for k, v in payload.items() if v is not None}
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{API_BASE_URL}/session_conversations/", json=payload)
        response.raise_for_status()
        return response.json()


async def get_session_conversation(conversation_id: int) -> Dict[str, Any]:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/session_conversations/{conversation_id}")
        response.raise_for_status()
        return response.json()


async def get_session_conversations(skip: int = 0, limit: int = 100, user_id: Optional[str] = None):
    params = {"skip": skip, "limit": limit}
    if user_id:
        params["user_id"] = user_id
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/session_conversations/", params=params)
        response.raise_for_status()
        return response.json()


async def update_session_conversation(conversation_id: int, update_fields: Dict[str, Any]) -> Dict[str, Any]:
    async with httpx.AsyncClient() as client:
        response = await client.put(f"{API_BASE_URL}/session_conversations/{conversation_id}", json=update_fields)
        response.raise_for_status()
        return response.json()


async def delete_session_conversation(conversation_id: int) -> Dict[str, Any]:
    async with httpx.AsyncClient() as client:
        response = await client.delete(f"{API_BASE_URL}/session_conversations/{conversation_id}")
        response.raise_for_status()
        return response.json()

async def get_user_by_username(username: str) -> List[Dict[str, Any]]:
    params = {"limit": 100, "username": username}
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/session_conversations/", params=params)
        response.raise_for_status()
        return response.json()  # List of user-conversation dicts matching username
    
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

async def get_last_user_and_assistant(messages):
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

async def verify_totp_code(username, code):
    users = await get_user_by_username(username)
    user_with_totp = next((user for user in users if user.get('totp_secret') is not None), None)
    if not user_with_totp or not user_with_totp.get('totp_secret'):
        return False
    totp = pyotp.TOTP(user_with_totp['totp_secret'])
    return totp.verify(code)