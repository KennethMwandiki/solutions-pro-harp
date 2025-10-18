# SPDX-License-Identifier: MIT
import jwt
import time

def sign_payload(payload: dict, key: str) -> str:
    # Compact JWT signature over essential fields
    claims = {
        "ts": int(time.time()),
        "hash_hint": hash(str(payload)) & 0xFFFFFFFF
    }
    token = jwt.encode(claims, key, algorithm="HS256")
    return token
