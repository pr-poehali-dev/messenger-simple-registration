"""Контакты: поиск пользователей, добавление. Action передаётся в теле или query."""
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
    """Контакты. action=all|list|add|remove передаётся в теле или query."""
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

    if action == "all":
        search = params.get("search", "") or body.get("search", "")
        if search:
            cur.execute(f"SELECT id, username FROM {SCHEMA}.users WHERE username ILIKE %s AND id != %s ORDER BY username LIMIT 50", (f"%{search}%", user_id))
        else:
            cur.execute(f"SELECT id, username FROM {SCHEMA}.users WHERE id != %s ORDER BY username LIMIT 50", (user_id,))
        rows = cur.fetchall()
        cur.execute(f"SELECT contact_id FROM {SCHEMA}.contacts WHERE user_id = %s", (user_id,))
        my_contacts = {r[0] for r in cur.fetchall()}
        users = [{"id": r[0], "username": r[1], "is_contact": r[0] in my_contacts} for r in rows]
        conn.close()
        return ok({"users": users})

    if action == "list":
        search = params.get("search", "") or body.get("search", "")
        if search:
            cur.execute(f"""
                SELECT u.id, u.username FROM {SCHEMA}.contacts c
                JOIN {SCHEMA}.users u ON c.contact_id = u.id
                WHERE c.user_id = %s AND u.username ILIKE %s
                ORDER BY u.username
            """, (user_id, f"%{search}%"))
        else:
            cur.execute(f"""
                SELECT u.id, u.username FROM {SCHEMA}.contacts c
                JOIN {SCHEMA}.users u ON c.contact_id = u.id
                WHERE c.user_id = %s ORDER BY u.username
            """, (user_id,))
        rows = cur.fetchall()
        conn.close()
        return ok({"contacts": [{"id": r[0], "username": r[1]} for r in rows]})

    if action == "add":
        contact_id = body.get("contact_id")
        if not contact_id:
            conn.close()
            return err("Укажите contact_id")
        cur.execute(f"INSERT INTO {SCHEMA}.contacts (user_id, contact_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (user_id, contact_id))
        conn.commit()
        conn.close()
        return ok({"ok": True})

    if action == "remove":
        contact_id = body.get("contact_id")
        if not contact_id:
            conn.close()
            return err("Укажите contact_id")
        conn.close()
        return ok({"ok": True})

    conn.close()
    return err("Неизвестное действие", 404)
