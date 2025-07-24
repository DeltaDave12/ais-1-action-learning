from typing import List, Dict

def should_trigger_topic_summary(messages: List[Dict], topic_model, threshold: float = 0.4, n: int = 7) -> bool:
    """
    Returns True if the last n user prompts are on the same topic (using topic similarity).
    """
    from topic_cag_logic import count_consecutive_same_topic
    return count_consecutive_same_topic(messages, topic_model, threshold) >= n


def get_last_n_topic_messages(messages: List[Dict], topic_model, threshold: float = 0.4, n: int = 7) -> List[Dict]:
    """
    Returns the last n user messages and all assistant messages that follow them (including summaries from Shorten button).
    """
    # Find indices of user messages
    user_indices = [i for i, m in enumerate(messages) if m["role"] == "user"]
    if len(user_indices) < n:
        return []
    last_n_user_indices = user_indices[-n:]
    # Collect all messages from the first of these user messages to the end
    start_idx = last_n_user_indices[0]
    return messages[start_idx:] 