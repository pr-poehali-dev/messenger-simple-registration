"""Чаты: создание, список, добавление участников. Action передаётся в теле."""
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
    """Управление чатами. action=list|create|add_member передаётся в теле или query."""
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
        cur.execute(f"""
            SELECT c.id, c.name, c.is_group, c.created_by,
                   (SELECT text FROM {SCHEMA}.messages WHERE chat_id = c.id ORDER BY created_at DESC LIMIT 1) as last_msg,
                   (SELECT created_at FROM {SCHEMA}.messages WHERE chat_id = c.id ORDER BY created_at DESC LIMIT 1) as last_time
            FROM {SCHEMA}.chats c
            JOIN {SCHEMA}.chat_members cm ON cm.chat_id = c.id
            WHERE cm.user_id = %s
            ORDER BY last_time DESC NULLS LAST
        """, (user_id,))
        rows = cur.fetchall()
        chats = []
        for r in rows:
            cur.execute(f"""
                SELECT u.id, u.username FROM {SCHEMA}.chat_members cm
                JOIN {SCHEMA}.users u ON cm.user_id = u.id
                WHERE cm.chat_id = %s
            """, (r[0],))
            members = [{"id": m[0], "username": m[1]} for m in cur.fetchall()]
            chats.append({
                "id": r[0], "name": r[1], "is_group": r[2],
                "created_by": r[3], "last_message": r[4],
                "last_time": r[5].isoformat() if r[5] else None,
                "members": members
            })
        conn.close()
        return ok({"chats": chats})

    if action == "create":
        name = body.get("name", "")
        is_group = body.get("is_group", False)
        member_ids = body.get("member_ids", [])
        if not name:
            conn.close()
            return err("Укажите название чата")
        cur.execute(f"INSERT INTO {SCHEMA}.chats (name, is_group, created_by) VALUES (%s, %s, %s) RETURNING id", (name, is_group, user_id))
        chat_id = cur.fetchone()[0]
        for mid in list(set([user_id] + member_ids)):
            cur.execute(f"INSERT INTO {SCHEMA}.chat_members (chat_id, user_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (chat_id, mid))
        conn.commit()
        conn.close()
        return ok({"chat_id": chat_id})

    if action == "add_member":
        chat_id = body.get("chat_id")
        new_member_id = body.get("user_id")
        if not chat_id or not new_member_id:
            conn.close()
            return err("Укажите chat_id и user_id")
        cur.execute(f"INSERT INTO {SCHEMA}.chat_members (chat_id, user_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (chat_id, new_member_id))
        conn.commit()
        conn.close()
        return ok({"ok": True})

    conn.close()
    return err("Неизвестное действие", 404)
