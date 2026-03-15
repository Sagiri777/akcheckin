import base64
import hashlib
import hmac
import json
import random
import time
import zipfile
from io import BytesIO
from typing import Any

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

HASH_KEY = "62AE221E4C5D4CAD4B851D7380F4ED2C"
LOG_TOKEN_KEY = "pM6Umv*^hVQuB6t&"


def now() -> int:
    return int(time.time())


def get_md5(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def u8_sign(data: dict[str, Any]) -> str:
    sign_str = "&".join(f"{k}={v}" for k, v in data.items())
    secret_key = "91240f70c09a08a6bc72af1a5c8d4670"
    return hmac.new(secret_key.encode(), sign_str.encode(), hashlib.sha1).hexdigest()


def get_random_devices() -> dict[str, str]:
    def rand_hex(length: int) -> str:
        return "".join(random.choice("0123456789abcdef") for _ in range(length))

    def rand_digits(length: int) -> str:
        return "".join(str(random.randint(0, 9)) for _ in range(length))

    return {
        "deviceId": get_md5(rand_hex(12)),
        "deviceId2": f"85{rand_digits(13)}",
        "deviceId3": get_md5(rand_hex(12)),
    }


def merge_dict(old: dict[str, Any], new_data: dict[str, Any], mode: str = "modify") -> None:
    for key, value in new_data.items():
        if key in old:
            if isinstance(value, dict) and isinstance(old[key], dict):
                merge_dict(old[key], value, mode)
            elif mode == "modify":
                old[key] = value
            elif mode == "delete":
                old.pop(key, None)
        else:
            old[key] = value


def _battle_key(login_time: int) -> bytes:
    return hashlib.md5(f"{LOG_TOKEN_KEY}{login_time}".encode()).digest()


def decrypt_battle_data(data: str, login_time: int) -> dict[str, Any]:
    encrypted = bytes.fromhex(data[:-32])
    iv = bytes.fromhex(data[-32:])
    cipher = AES.new(_battle_key(login_time), AES.MODE_CBC, iv)
    decrypted = unpad(cipher.decrypt(encrypted), AES.block_size)
    return json.loads(decrypted.decode())


def encrypt_battle_data(data: dict[str, Any], login_time: int) -> str:
    raw = json.dumps(data, ensure_ascii=False).encode()
    iv = random.randbytes(16)
    cipher = AES.new(_battle_key(login_time), AES.MODE_CBC, iv)
    encrypted = cipher.encrypt(pad(raw, AES.block_size))
    return encrypted.hex() + iv.hex()


def encrypt_is_cheat(battle_id: str) -> str:
    shifted = bytes((b + 7) % 256 for b in battle_id.encode())
    return base64.b64encode(shifted).decode()


def decrypt_is_cheat(is_cheat: str) -> str:
    raw = base64.b64decode(is_cheat)
    return bytes((b - 7) % 256 for b in raw).decode()


def get_battle_data_access(login_time: int) -> str:
    return get_md5(f"{HASH_KEY}{login_time}").upper()


def decrypt_battle_replay(battle_replay: str) -> dict[str, Any]:
    data = base64.b64decode(battle_replay)
    with zipfile.ZipFile(BytesIO(data)) as zf:
        return json.loads(zf.read("default_entry").decode())


def sleep(seconds: float) -> None:
    time.sleep(seconds)


def select_tags(tags: list[int]) -> tuple[list[int], int, int]:
    selected: list[int] = []
    special_tag = 0
    duration = 32400
    if 11 in tags:
        special_tag = 11
    elif 14 in tags:
        special_tag = 14
        selected = [14]
    elif 27 in tags:
        selected = [27]
    elif 7 in tags and 12 in tags:
        selected = [7, 12]
    elif 7 in tags and 20 in tags:
        selected = [7, 20]
    elif 7 in tags and 23 in tags:
        selected = [7, 23]
    elif 7 in tags and 24 in tags:
        selected = [7, 24]
    elif 26 in tags and 19 in tags:
        selected = [26, 19]
    elif 26 in tags and 22 in tags:
        selected = [26, 22]
    elif 26 in tags and 3 in tags:
        selected = [26, 3]
    elif 26 in tags and 23 in tags:
        selected = [26, 23]
    elif 25 in tags and 12 in tags:
        selected = [25, 12]
    elif 25 in tags and 24 in tags:
        selected = [25, 24]
    elif 21 in tags and 24 in tags:
        selected = [21, 24]
    elif 9 in tags and 24 in tags:
        selected = [9, 24]
    elif 4 in tags and 24 in tags:
        selected = [4, 24]
    elif 13 in tags and 21 in tags:
        selected = [13, 21]
    elif 13 in tags and 6 in tags:
        selected = [4, 24]
    elif 13 in tags and 19 in tags and 10 in tags:
        selected = [13, 19, 10]
    elif 13 in tags and 19 in tags and 2 in tags:
        selected = [13, 19, 2]
    elif 12 in tags and 8 in tags:
        selected = [12, 8]
    elif 12 in tags and 18 in tags:
        selected = [12, 18]
    elif 12 in tags and 23 in tags:
        selected = [12, 23]
    elif 16 in tags and 8 in tags:
        selected = [16, 8]
    elif 16 in tags and 18 in tags:
        selected = [16, 18]
    elif 16 in tags and 5 in tags:
        selected = [16, 5]
    elif 16 in tags and 20 in tags:
        selected = [16, 20]
    elif 15 in tags and 6 in tags:
        selected = [15, 6]
    elif 15 in tags and 19 in tags:
        selected = [15, 19]
    elif 23 in tags and 19 in tags and 6 in tags:
        selected = [23, 19, 6]
    elif 19 in tags and 5 in tags:
        selected = [19, 5]
    elif 19 in tags and 21 in tags:
        selected = [19, 21]
    elif 19 in tags and 3 in tags:
        selected = [19, 3]
    elif 22 in tags and 1 in tags:
        selected = [22, 1]
    elif 22 in tags and 6 in tags:
        selected = [22, 6]
    elif 22 in tags and 10 in tags:
        selected = [22, 10]
    elif 22 in tags and 21 in tags:
        selected = [22, 21]
    elif 20 in tags and 22 in tags:
        selected = [20, 22]
    elif 20 in tags and 3 in tags:
        selected = [20, 3]
    elif 20 in tags and 5 in tags:
        selected = [20, 5]
    elif 7 in tags:
        selected = [7]
    elif 26 in tags:
        selected = [26]
    elif 24 in tags:
        selected = [24]
    elif 25 in tags:
        selected = [25]
    elif 12 in tags:
        selected = [12]
    elif 13 in tags:
        selected = [13]
    elif 16 in tags:
        selected = [16]
    elif 15 in tags and 8 in tags:
        selected = [15, 8]
    elif 15 in tags and 18 in tags:
        selected = [15, 18]
    elif 15 in tags and 5 in tags:
        selected = [15, 5]
    elif 15 in tags and 23 in tags:
        selected = [15, 23]
    elif 20 in tags and 2 in tags:
        selected = [20, 2]
    elif 20 in tags and 10 in tags:
        selected = [20, 10]
    elif 23 in tags and 19 in tags and 2 in tags:
        selected = [23, 19, 6]
    elif 23 in tags and 6 in tags:
        selected = [23, 6]
    elif 23 in tags and 2 in tags:
        selected = [23, 2]
    elif 23 in tags and 9 in tags:
        selected = [23, 9]
    elif 23 in tags and 1 in tags:
        selected = [23, 1]

    return selected, special_tag, duration
