import httpx
from typing import Optional, List, Dict, Any

API_BASE_URL = "http://localhost:8000"


async def create_session_conversation(
    session_id: Optional[int] = None,
    last_updated: Optional[str] = None,   # ISO datetime string
    messages: Optional[List[Dict[str, Any]]] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    payload = {
        "session_id": session_id,
        "last_updated": last_updated,
        "messages": messages,
        "username": username,
        "password": password,
        "user_id": user_id,
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
