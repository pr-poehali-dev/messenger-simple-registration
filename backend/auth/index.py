"""Авторизация: регистрация, вход, проверка сессии. Action передаётся в теле запроса."""
import json
import os
import hashlib
import secrets
import psycopg2

SCHEMA = "t_p28244525_messenger_simple_reg"

def get_conn():
    return psycopg2.connect(os.environ["DATABASE_URL"])

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def cors_headers():
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, X-Auth-Token",
        "Content-Type": "application/json"
    }

def ok(data: dict) -> dict:
    return {"statusCode": 200, "headers": cors_headers(), "body": json.dumps(data)}

def err(msg: str, code: int = 400) -> dict:
    return {"statusCode": code, "headers": cors_headers(), "body": json.dumps({"error": msg})}

def handler(event: dict, context) -> dict:
    """Регистрация и вход. action=register|login|me передаётся в теле."""
    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 200, "headers": cors_headers(), "body": ""}

    method = event.get("httpMethod", "GET")
    body = {}
    if event.get("body"):
        body = json.loads(event["body"])

    action = body.get("action") or event.get("queryStringParameters", {}).get("action", "")

    # Проверка токена (GET ?action=me)
    if action == "me":
        token = event.get("headers", {}).get("X-Auth-Token", "")
        if not token:
            return err("Не авторизован", 401)
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(f"SELECT u.id, u.username FROM {SCHEMA}.sessions s JOIN {SCHEMA}.users u ON s.user_id = u.id WHERE s.token = %s", (token,))
        user = cur.fetchone()
        conn.close()
        if not user:
            return err("Сессия истекла", 401)
        return ok({"user_id": user[0], "username": user[1]})

    if method != "POST":
        return err("Not found", 404)

    # Регистрация
    if action == "register":
        username = body.get("username", "").strip()
        password = body.get("password", "")
        if not username or not password:
            return err("Введите ник и пароль")
        if len(username) < 3:
            return err("Ник минимум 3 символа")
        conn = get_conn()
        cur = conn.cursor()
        try:
            cur.execute(f"INSERT INTO {SCHEMA}.users (username, password_hash) VALUES (%s, %s) RETURNING id, username", (username, hash_password(password)))
            user = cur.fetchone()
            token = secrets.token_hex(32)
            cur.execute(f"INSERT INTO {SCHEMA}.sessions (user_id, token) VALUES (%s, %s)", (user[0], token))
            conn.commit()
            conn.close()
            return ok({"token": token, "user_id": user[0], "username": user[1]})
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            conn.close()
            return err("Ник уже занят", 409)

    # Вход
    if action == "login":
        username = body.get("username", "").strip()
        password = body.get("password", "")
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(f"SELECT id, username FROM {SCHEMA}.users WHERE username = %s AND password_hash = %s", (username, hash_password(password)))
        user = cur.fetchone()
        if not user:
            conn.close()
            return err("Неверный ник или пароль", 401)
        token = secrets.token_hex(32)
        cur.execute(f"INSERT INTO {SCHEMA}.sessions (user_id, token) VALUES (%s, %s)", (user[0], token))
        conn.commit()
        conn.close()
        return ok({"token": token, "user_id": user[0], "username": user[1]})

    return err("Неизвестное действие", 404)
