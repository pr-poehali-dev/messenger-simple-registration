"""Сообщения: отправка и получение. Action передаётся в теле или query."""
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

def ok(data: dict) -> dict:
    return {"statusCode": 200, "headers": cors_headers(), "body": json.dumps(data)}

def err(msg: str, code: int = 400) -> dict:
    return {"statusCode": code, "headers": cors_headers(), "body": json.dumps({"error": msg})}

def get_user_by_token(cur, token):
    cur.execute(f"SELECT u.id, u.username FROM {SCHEMA}.sessions s JOIN {SCHEMA}.users u ON s.user_id = u.id WHERE s.token = %s", (token,))
    return cur.fetchone()

def handler(event: dict, context) -> dict:
    """Сообщения. action=list|send передаётся в теле или query."""
    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 200, "headers": cors_headers(), "body": ""}

    token = event.get("headers", {}).get("X-Auth-Token", "")
    body = {}
    if event.get("body"):
        body = json.loads(event["body"])

    params = event.get("queryStringParameters") or {}
    action = body.get("action") or params.get("action", "list")

    conn = get_conn()
    cur = conn.cursor()
    user = get_user_by_token(cur, token)
    if not user:
        conn.close()
        return err("Не авторизован", 401)
    user_id = user[0]

    if action == "list":
        chat_id = params.get("chat_id") or body.get("chat_id")
        if not chat_id:
            conn.close()
            return err("Укажите chat_id")
        cur.execute(f"SELECT 1 FROM {SCHEMA}.chat_members WHERE chat_id = %s AND user_id = %s", (chat_id, user_id))
        if not cur.fetchone():
            conn.close()
            return err("Нет доступа", 403)
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
        return ok({"messages": messages})

    if action == "send":
        chat_id = body.get("chat_id")
        text = body.get("text", "").strip()
        if not chat_id or not text:
            conn.close()
            return err("Укажите chat_id и text")
        cur.execute(f"SELECT 1 FROM {SCHEMA}.chat_members WHERE chat_id = %s AND user_id = %s", (chat_id, user_id))
        if not cur.fetchone():
            conn.close()
            return err("Нет доступа", 403)
        cur.execute(f"INSERT INTO {SCHEMA}.messages (chat_id, sender_id, text) VALUES (%s, %s, %s) RETURNING id, created_at", (chat_id, user_id, text))
        msg = cur.fetchone()
        conn.commit()
        conn.close()
        return ok({"id": msg[0], "created_at": msg[1].isoformat()})

    conn.close()
    return err("Неизвестное действие", 404)
