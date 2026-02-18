import json
import time
from contextlib import contextmanager
from typing import Any

import pymysql
from pymysql.cursors import DictCursor

from config import settings

ALLOWED_STATUSES = {"Черновик", "Новая заявка", "В работе", "Готово", "Отменено"}


class DatabaseError(Exception):
    pass
	
	
def get_connection(retries: int = 15, delay: float = 2.0):
    last_error = None
    for _ in range(retries):
        try:
            return pymysql.connect(
                host=settings.mysql_host,
                port=settings.mysql_port,
                user=settings.mysql_user,
                password=settings.mysql_password,
                database=settings.mysql_db,
                charset="utf8mb4",
                cursorclass=DictCursor,
                autocommit=False,
            )
        except Exception as exc:
            last_error = exc
            time.sleep(delay)
    raise DatabaseError(f"Cannot connect to DB: {last_error}")


@contextmanager
def db_cursor():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            yield conn, cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db_if_needed() -> None:
    with db_cursor() as (_, cur):
        cur.execute("SELECT 1")


def cancel_old_drafts(user_id: int) -> int:
    with db_cursor() as (_, cur):
        cur.execute(
            "UPDATE orders SET status='Отменено', updated_at=NOW() WHERE user_id=%s AND status='Черновик'",
            (user_id,),
        )
        return cur.rowcount


def create_order(user_id: int, username: str | None, full_name: str | None, branch: str) -> int:
    with db_cursor() as (_, cur):
        cur.execute(
            """
            INSERT INTO orders (user_id, username, full_name, branch, status, order_payload)
            VALUES (%s, %s, %s, %s, 'Черновик', JSON_OBJECT())
            """,
            (user_id, username, full_name, branch),
        )
        return cur.lastrowid


def get_order(order_id: int) -> dict[str, Any] | None:
    with db_cursor() as (_, cur):
        cur.execute("SELECT * FROM orders WHERE id=%s", (order_id,))
        row = cur.fetchone()
        if row:
            row["order_payload"] = parse_payload(row.get("order_payload"))
        return row


def parse_payload(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except Exception:
        return {}


def update_order_payload(order_id: int, payload: dict[str, Any]) -> None:
    with db_cursor() as (_, cur):
        cur.execute(
            "UPDATE orders SET order_payload=%s, updated_at=NOW() WHERE id=%s",
            (json.dumps(payload, ensure_ascii=False), order_id),
        )


def get_order_payload(order_id: int) -> dict[str, Any]:
    row = get_order(order_id)
    return row.get("order_payload", {}) if row else {}


def set_order_meta(order_id: int, request_type: str | None = None, summary: str | None = None, status: str | None = None) -> None:
    fields = []
    params: list[Any] = []
    if request_type is not None:
        fields.append("request_type=%s")
        params.append(request_type)
    if summary is not None:
        fields.append("summary=%s")
        params.append(summary)
    if status is not None:
        if status not in ALLOWED_STATUSES:
            raise ValueError("Unknown status")
        fields.append("status=%s")
        params.append(status)
    if not fields:
        return
    params.append(order_id)
    with db_cursor() as (_, cur):
        cur.execute(f"UPDATE orders SET {', '.join(fields)}, updated_at=NOW() WHERE id=%s", tuple(params))


def finalize_order(order_id: int, request_type: str, summary: str) -> None:
    set_order_meta(order_id, request_type=request_type, summary=summary, status="Новая заявка")


def list_orders(filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    filters = filters or {}
    where = []
    params: list[Any] = []
    if filters.get("status"):
        where.append("status=%s")
        params.append(filters["status"])
    where_sql = f"WHERE {' AND '.join(where)}" if where else ""
    with db_cursor() as (_, cur):
        cur.execute(f"SELECT * FROM orders {where_sql} ORDER BY created_at DESC LIMIT 500", tuple(params))
        rows = cur.fetchall()
        for row in rows:
            row["order_payload"] = parse_payload(row.get("order_payload"))
        return rows


def get_order_statistics() -> dict[str, int]:
    with db_cursor() as (_, cur):
        cur.execute("SELECT COUNT(*) AS cnt FROM orders")
        total = cur.fetchone()["cnt"]
        cur.execute("SELECT COUNT(*) AS cnt FROM orders WHERE status='Новая заявка'")
        new_orders = cur.fetchone()["cnt"]
        cur.execute("SELECT COUNT(*) AS cnt FROM orders WHERE status='В работе'")
        in_work = cur.fetchone()["cnt"]
        return {"total_orders": total, "new_orders": new_orders, "active_orders": in_work}


def add_order_file(order_id: int, file_id: str, filename: str, mime: str | None, size: int | None) -> int:
    with db_cursor() as (_, cur):
        cur.execute(
            """
            INSERT INTO order_files (order_id, telegram_file_id, original_name, mime_type, file_size)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (order_id, file_id, filename, mime, size),
        )
        return cur.lastrowid


def list_order_files(order_id: int) -> list[dict[str, Any]]:
    with db_cursor() as (_, cur):
        cur.execute("SELECT * FROM order_files WHERE order_id=%s ORDER BY created_at ASC", (order_id,))
        return cur.fetchall()


def update_order_status(order_id: int, status: str) -> None:
    set_order_meta(order_id, status=status)


def get_bot_config() -> dict[str, str]:
    with db_cursor() as (_, cur):
        cur.execute("SELECT config_key, config_value FROM bot_config")
        rows = cur.fetchall()
        return {row["config_key"]: row["config_value"] for row in rows}


def set_bot_config(key: str, value: str) -> None:
    with db_cursor() as (_, cur):
        cur.execute(
            """
            INSERT INTO bot_config (config_key, config_value)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE config_value=VALUES(config_value), updated_at=NOW()
            """,
            (key, value),
        )
