from pathlib import Path

def _is_file(s: str) -> bool:
    try:
        return Path(s).is_file()
    except (OSError, TypeError):
        # catches `OSError: [Errno 63] File name too long`
        return False

def _get_if_file(s) -> str:
    if isinstance(s, Path):
        s = s.read_text()

    if _is_file(s):
        with open(s) as f:
            s = f.read()

    return s
