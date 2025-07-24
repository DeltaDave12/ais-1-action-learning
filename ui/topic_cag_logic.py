from sentence_transformers import util

def count_consecutive_same_topic(messages, topic_model, threshold=0.4):
    # Count how many consecutive user messages are on the same topic as the latest
    if not messages or len(messages) < 2:
        return 1
    last_user_msg = messages[-1]["content"] if messages[-1]["role"] == "user" else None
    if not last_user_msg:
        return 0
    count = 1
    for i in range(len(messages) - 2, -1, -1):
        msg = messages[i]
        if msg["role"] != "user":
            continue
        emb1 = topic_model.encode([last_user_msg])[0]
        emb2 = topic_model.encode([msg["content"]])[0]
        similarity = util.cos_sim(emb1, emb2).item()
        if similarity >= threshold:
            count += 1
        else:
            break
    return count 