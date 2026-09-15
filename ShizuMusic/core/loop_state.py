# --------------------------------------------------------------------------------
#  ShizuMusic © 2026
#  Developed by Bad Munda ❤️
# --------------------------------------------------------------------------------

# chat_id -> loop remaining
#  0  = disabled
# -1  = infinite
#  N  = remaining additional plays
_loop: dict = {}


def get_loop(chat_id: int) -> int:
    return _loop.get(chat_id, 0)


def set_loop(chat_id: int, value: int) -> None:
    if value == 0:
        _loop.pop(chat_id, None)
    else:
        _loop[chat_id] = value


def clear_loop(chat_id: int) -> None:
    _loop.pop(chat_id, None)


def is_looping(chat_id: int) -> bool:
    return get_loop(chat_id) != 0


def consume_loop(chat_id: int) -> bool:
    """Return True if same track should replay; decrement finite count."""
    val = get_loop(chat_id)
    if val == 0:
        return False
    if val == -1:
        return True
    if val > 0:
        set_loop(chat_id, val - 1)
        return True
    return False
