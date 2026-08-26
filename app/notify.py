import base64
import smtplib
from email.mime.text import MIMEText

import httpx
import jwt
from fastapi import HTTPException

from . import config

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"


class NotifyError(Exception):
    pass


def verify_token(authorization: str | None) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(
            token,
            config.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")
    email = payload.get("email")
    if not email:
        raise HTTPException(status_code=401, detail="Token has no email claim")
    return {"sub": payload.get("sub"), "email": email}


def _get_gmail_access_token() -> str:
    resp = httpx.post(
        GOOGLE_TOKEN_URL,
        data={
            "client_id": config.GOOGLE_CLIENT_ID,
            "client_secret": config.GOOGLE_CLIENT_SECRET,
            "refresh_token": config.GMAIL_REFRESH_TOKEN,
            "grant_type": "refresh_token",
        },
        timeout=10,
    )
    if resp.status_code != 200:
        raise NotifyError(f"Gmail token refresh failed: {resp.status_code} {resp.text}")
    return resp.json()["access_token"]


def _xoauth2_string(user: str, access_token: str) -> str:
    return f"user={user}\1auth=Bearer {access_token}\1\1"


def send_email(to: str, subject: str, body: str) -> None:
    access_token = _get_gmail_access_token()
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = config.GMAIL_SENDER_EMAIL
    msg["To"] = to

    with smtplib.SMTP("smtp.gmail.com", 587, timeout=10) as smtp:
        smtp.starttls()
        auth_string = _xoauth2_string(config.GMAIL_SENDER_EMAIL, access_token)
        b64_auth = base64.b64encode(auth_string.encode()).decode()
        code, response = smtp.docmd("AUTH", "XOAUTH2 " + b64_auth)
        if code != 235:
            raise NotifyError(f"Gmail SMTP auth failed: {code} {response}")
        smtp.sendmail(config.GMAIL_SENDER_EMAIL, [to], msg.as_string())
