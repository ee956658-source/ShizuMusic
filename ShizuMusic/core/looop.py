# Per-chat loop state
_loop_states: dict[int, bool] = {}

def is_loop(chat_id: int) -> bool:
    return _loop_states.get(int(chat_id), False)

def set_loop(chat_id: int, enabled: bool) -> None:
    _loop_states[int(chat_id)] = bool(enabled)

def clear_loop(chat_id: int) -> None:
    _loop_states.pop(int(chat_id), None)
