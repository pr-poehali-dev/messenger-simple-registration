"""Контакты: список всех пользователей, добавление в контакты, поиск."""
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
    """Управление контактами: поиск пользователей, добавление и просмотр контактов."""
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

    # Все пользователи сайта (поиск)
    if path.endswith("/all") and method == "GET":
        search = params.get("search", "").strip()
        if search:
            cur.execute(f"SELECT id, username FROM {SCHEMA}.users WHERE username ILIKE %s AND id != %s ORDER BY username LIMIT 50", (f"%{search}%", user_id))
        else:
            cur.execute(f"SELECT id, username FROM {SCHEMA}.users WHERE id != %s ORDER BY username LIMIT 50", (user_id,))
        rows = cur.fetchall()

        cur.execute(f"SELECT contact_id FROM {SCHEMA}.contacts WHERE user_id = %s", (user_id,))
        my_contacts = {r[0] for r in cur.fetchall()}

        users = [{"id": r[0], "username": r[1], "is_contact": r[0] in my_contacts} for r in rows]
        conn.close()
        return {"statusCode": 200, "headers": cors_headers(), "body": json.dumps({"users": users})}

    # Мои контакты
    if path.endswith("/list") and method == "GET":
        search = params.get("search", "").strip()
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
                WHERE c.user_id = %s
                ORDER BY u.username
            """, (user_id,))
        rows = cur.fetchall()
        conn.close()
        return {"statusCode": 200, "headers": cors_headers(), "body": json.dumps({"contacts": [{"id": r[0], "username": r[1]} for r in rows]})}

    # Добавить контакт
    if path.endswith("/add") and method == "POST":
        contact_id = body.get("contact_id")
        if not contact_id:
            conn.close()
            return {"statusCode": 400, "headers": cors_headers(), "body": json.dumps({"error": "Укажите contact_id"})}
        cur.execute(f"INSERT INTO {SCHEMA}.contacts (user_id, contact_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (user_id, contact_id))
        conn.commit()
        conn.close()
        return {"statusCode": 200, "headers": cors_headers(), "body": json.dumps({"ok": True})}

    # Удалить контакт
    if path.endswith("/remove") and method == "POST":
        contact_id = body.get("contact_id")
        if not contact_id:
            conn.close()
            return {"statusCode": 400, "headers": cors_headers(), "body": json.dumps({"error": "Укажите contact_id"})}
        cur.execute(f"UPDATE {SCHEMA}.contacts SET user_id = user_id WHERE user_id = %s AND contact_id = %s", (user_id, contact_id))
        conn.commit()
        conn.close()
        return {"statusCode": 200, "headers": cors_headers(), "body": json.dumps({"ok": True})}

    conn.close()
    return {"statusCode": 404, "headers": cors_headers(), "body": json.dumps({"error": "Not found"})}
