"""Сообщения: отправка и получение сообщений в чате."""
import json
import os
import psycopg2

SCHEMA = "t_p28244525_messenger_simple_reg"

def get_conn():
    return psycopg2.connect(os.environ["DATABASE_URL"])

def cors_headers():
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, X-Auth-Token",
        "Content-Type": "application/json"
    }

def get_user_by_token(cur, token):
    cur.execute(f"SELECT u.id, u.username FROM {SCHEMA}.sessions s JOIN {SCHEMA}.users u ON s.user_id = u.id WHERE s.token = %s", (token,))
    return cur.fetchone()

def handler(event: dict, context) -> dict:
    """Отправка и получение сообщений в чате."""
    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 200, "headers": cors_headers(), "body": ""}

    path = event.get("path", "/")
    method = event.get("httpMethod", "GET")
    token = event.get("headers", {}).get("X-Auth-Token", "")
    body = {}
    if event.get("body"):
        body = json.loads(event["body"])
    params = event.get("queryStringParameters") or {}

    conn = get_conn()
    cur = conn.cursor()

    user = get_user_by_token(cur, token)
    if not user:
        conn.close()
        return {"statusCode": 401, "headers": cors_headers(), "body": json.dumps({"error": "Не авторизован"})}

    user_id = user[0]

    # Получить сообщения чата
    if path.endswith("/list") and method == "GET":
        chat_id = params.get("chat_id")
        if not chat_id:
            conn.close()
            return {"statusCode": 400, "headers": cors_headers(), "body": json.dumps({"error": "Укажите chat_id"})}

        # Проверка что пользователь в чате
        cur.execute(f"SELECT 1 FROM {SCHEMA}.chat_members WHERE chat_id = %s AND user_id = %s", (chat_id, user_id))
        if not cur.fetchone():
            conn.close()
            return {"statusCode": 403, "headers": cors_headers(), "body": json.dumps({"error": "Нет доступа"})}

        cur.execute(f"""
            SELECT m.id, m.text, m.created_at, u.id, u.username
            FROM {SCHEMA}.messages m
            JOIN {SCHEMA}.users u ON m.sender_id = u.id
            WHERE m.chat_id = %s
            ORDER BY m.created_at ASC
            LIMIT 100
        """, (chat_id,))
        rows = cur.fetchall()
        messages = [{"id": r[0], "text": r[1], "created_at": r[2].isoformat(), "sender_id": r[3], "sender": r[4]} for r in rows]
        conn.close()
        return {"statusCode": 200, "headers": cors_headers(), "body": json.dumps({"messages": messages})}

    # Отправить сообщение
    if path.endswith("/send") and method == "POST":
        chat_id = body.get("chat_id")
        text = body.get("text", "").strip()
        if not chat_id or not text:
            conn.close()
            return {"statusCode": 400, "headers": cors_headers(), "body": json.dumps({"error": "Укажите chat_id и text"})}

        cur.execute(f"SELECT 1 FROM {SCHEMA}.chat_members WHERE chat_id = %s AND user_id = %s", (chat_id, user_id))
        if not cur.fetchone():
            conn.close()
            return {"statusCode": 403, "headers": cors_headers(), "body": json.dumps({"error": "Нет доступа"})}

        cur.execute(f"INSERT INTO {SCHEMA}.messages (chat_id, sender_id, text) VALUES (%s, %s, %s) RETURNING id, created_at", (chat_id, user_id, text))
        msg = cur.fetchone()
        conn.commit()
        conn.close()
        return {"statusCode": 200, "headers": cors_headers(), "body": json.dumps({"id": msg[0], "created_at": msg[1].isoformat()})}

    conn.close()
    return {"statusCode": 404, "headers": cors_headers(), "body": json.dumps({"error": "Not found"})}
