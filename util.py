
def is_valid_id(s: str):
    return all(c.isalnum() or c in "_-" for c in s) and 16 >= len(s) >= 3

