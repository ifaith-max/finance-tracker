"""数据层：负责和 SQLite 打交道（建表、增删改查、统计）。"""

import sqlite3
from contextlib import contextmanager

from config import DB_FILE


@contextmanager
def _db():
    """打开数据库连接，用完自动关闭并提交修改。"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # 让结果可以用列名访问，如 row["amount"]
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """建表（表不存在时才创建）。"""
    with _db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                type     TEXT    NOT NULL,
                amount   REAL    NOT NULL,
                category TEXT    NOT NULL,
                date     TEXT    NOT NULL,
                note     TEXT    DEFAULT ''
            )
            """
        )


def add_transaction(type_, amount, category, date, note):
    """新增一条账目。"""
    with _db() as conn:
        conn.execute(
            "INSERT INTO transactions (type, amount, category, date, note) "
            "VALUES (?, ?, ?, ?, ?)",
            (type_, amount, category, date, note),
        )


def list_transactions(month=None, category=None):
    """按月份、分类筛选，返回记录（日期新到旧）。"""
    sql = "SELECT * FROM transactions WHERE 1=1"
    params = []
    if month:
        sql += " AND substr(date, 1, 7) = ?"
        params.append(month)
    if category:
        sql += " AND category = ?"
        params.append(category)
    sql += " ORDER BY date DESC, id DESC"
    with _db() as conn:
        return conn.execute(sql, params).fetchall()


def get_transaction(id_):
    """按 id 取单条记录（编辑时预填用）。"""
    with _db() as conn:
        return conn.execute(
            "SELECT * FROM transactions WHERE id = ?", (id_,)
        ).fetchone()


def update_transaction(id_, type_, amount, category, date, note):
    """按 id 更新一条账目。"""
    with _db() as conn:
        conn.execute(
            "UPDATE transactions SET type = ?, amount = ?, category = ?, date = ?, note = ? "
            "WHERE id = ?",
            (type_, amount, category, date, note, id_),
        )


def delete_transaction(id_):
    """按 id 删除一条账目。"""
    with _db() as conn:
        conn.execute("DELETE FROM transactions WHERE id = ?", (id_,))


def get_stats(month=None, type_=None):
    """按分类分组统计，返回 (category, count, total)，金额降序。"""
    sql = (
        "SELECT category, COUNT(*) AS count, SUM(amount) AS total "
        "FROM transactions WHERE 1=1"
    )
    params = []
    if month:
        sql += " AND substr(date, 1, 7) = ?"
        params.append(month)
    if type_:
        sql += " AND type = ?"
        params.append(type_)
    sql += " GROUP BY category ORDER BY total DESC"
    with _db() as conn:
        return conn.execute(sql, params).fetchall()


def get_months():
    """返回数据中已有的月份（如 '2026-11'），新到旧。"""
    with _db() as conn:
        rows = conn.execute(
            "SELECT DISTINCT substr(date, 1, 7) AS month "
            "FROM transactions ORDER BY month DESC"
        ).fetchall()
    return [r["month"] for r in rows]
