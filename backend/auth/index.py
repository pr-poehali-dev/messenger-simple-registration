"""Авторизация: регистрация, вход, выход, проверка сессии."""
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

def handler(event: dict, context) -> dict:
    """Регистрация, вход и выход пользователей."""
    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 200, "headers": cors_headers(), "body": ""}

    path = event.get("path", "/")
    method = event.get("httpMethod", "GET")
    body = {}
    if event.get("body"):
        body = json.loads(event["body"])

    conn = get_conn()
    cur = conn.cursor()

    # Регистрация
    if path.endswith("/register") and method == "POST":
        username = body.get("username", "").strip()
        password = body.get("password", "")
        if not username or not password:
            conn.close()
            return {"statusCode": 400, "headers": cors_headers(), "body": json.dumps({"error": "Введите ник и пароль"})}
        if len(username) < 3:
            conn.close()
            return {"statusCode": 400, "headers": cors_headers(), "body": json.dumps({"error": "Ник минимум 3 символа"})}

        try:
            cur.execute(f"INSERT INTO {SCHEMA}.users (username, password_hash) VALUES (%s, %s) RETURNING id, username", (username, hash_password(password)))
            user = cur.fetchone()
            token = secrets.token_hex(32)
            cur.execute(f"INSERT INTO {SCHEMA}.sessions (user_id, token) VALUES (%s, %s)", (user[0], token))
            conn.commit()
            conn.close()
            return {"statusCode": 200, "headers": cors_headers(), "body": json.dumps({"token": token, "user_id": user[0], "username": user[1]})}
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            conn.close()
            return {"statusCode": 409, "headers": cors_headers(), "body": json.dumps({"error": "Ник уже занят"})}

    # Вход
    if path.endswith("/login") and method == "POST":
        username = body.get("username", "").strip()
        password = body.get("password", "")
        cur.execute(f"SELECT id, username FROM {SCHEMA}.users WHERE username = %s AND password_hash = %s", (username, hash_password(password)))
        user = cur.fetchone()
        if not user:
            conn.close()
            return {"statusCode": 401, "headers": cors_headers(), "body": json.dumps({"error": "Неверный ник или пароль"})}
        token = secrets.token_hex(32)
        cur.execute(f"INSERT INTO {SCHEMA}.sessions (user_id, token) VALUES (%s, %s)", (user[0], token))
        conn.commit()
        conn.close()
        return {"statusCode": 200, "headers": cors_headers(), "body": json.dumps({"token": token, "user_id": user[0], "username": user[1]})}

    # Проверка токена
    if path.endswith("/me") and method == "GET":
        token = event.get("headers", {}).get("X-Auth-Token", "")
        if not token:
            conn.close()
            return {"statusCode": 401, "headers": cors_headers(), "body": json.dumps({"error": "Не авторизован"})}
        cur.execute(f"SELECT u.id, u.username FROM {SCHEMA}.sessions s JOIN {SCHEMA}.users u ON s.user_id = u.id WHERE s.token = %s", (token,))
        user = cur.fetchone()
        conn.close()
        if not user:
            return {"statusCode": 401, "headers": cors_headers(), "body": json.dumps({"error": "Сессия истекла"})}
        return {"statusCode": 200, "headers": cors_headers(), "body": json.dumps({"user_id": user[0], "username": user[1]})}

    conn.close()
    return {"statusCode": 404, "headers": cors_headers(), "body": json.dumps({"error": "Not found"})}
