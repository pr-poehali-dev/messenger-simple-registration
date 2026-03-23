"""Чаты: создание, список чатов, добавление участников."""
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
    """Управление чатами: создание, просмотр списка, добавление участников."""
    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 200, "headers": cors_headers(), "body": ""}

    path = event.get("path", "/")
    method = event.get("httpMethod", "GET")
    token = event.get("headers", {}).get("X-Auth-Token", "")
    body = {}
    if event.get("body"):
        body = json.loads(event["body"])

    conn = get_conn()
    cur = conn.cursor()

    user = get_user_by_token(cur, token)
    if not user:
        conn.close()
        return {"statusCode": 401, "headers": cors_headers(), "body": json.dumps({"error": "Не авторизован"})}

    user_id = user[0]

    # Список чатов пользователя
    if path.endswith("/list") and method == "GET":
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
        return {"statusCode": 200, "headers": cors_headers(), "body": json.dumps({"chats": chats})}

    # Создание чата
    if path.endswith("/create") and method == "POST":
        name = body.get("name", "")
        is_group = body.get("is_group", False)
        member_ids = body.get("member_ids", [])

        if not name:
            conn.close()
            return {"statusCode": 400, "headers": cors_headers(), "body": json.dumps({"error": "Укажите название чата"})}

        cur.execute(f"INSERT INTO {SCHEMA}.chats (name, is_group, created_by) VALUES (%s, %s, %s) RETURNING id", (name, is_group, user_id))
        chat_id = cur.fetchone()[0]

        all_members = list(set([user_id] + member_ids))
        for mid in all_members:
            cur.execute(f"INSERT INTO {SCHEMA}.chat_members (chat_id, user_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (chat_id, mid))

        conn.commit()
        conn.close()
        return {"statusCode": 200, "headers": cors_headers(), "body": json.dumps({"chat_id": chat_id})}

    # Добавить участника
    if path.endswith("/add-member") and method == "POST":
        chat_id = body.get("chat_id")
        new_member_id = body.get("user_id")
        if not chat_id or not new_member_id:
            conn.close()
            return {"statusCode": 400, "headers": cors_headers(), "body": json.dumps({"error": "Укажите chat_id и user_id"})}
        cur.execute(f"INSERT INTO {SCHEMA}.chat_members (chat_id, user_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (chat_id, new_member_id))
        conn.commit()
        conn.close()
        return {"statusCode": 200, "headers": cors_headers(), "body": json.dumps({"ok": True})}

    conn.close()
    return {"statusCode": 404, "headers": cors_headers(), "body": json.dumps({"error": "Not found"})}
