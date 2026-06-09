#!/usr/bin/env python3
"""初始化 MySQL：创建库 + 建表（开发库与测试库）。

用法（在 server 目录下）：
  python scripts/init_database.py

依赖 server/.env 中的 DATABASE_URL，或以下环境变量：
  MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

import pymysql
from dotenv import load_dotenv

SERVER_DIR = Path(__file__).resolve().parents[1]
SQL_DIR = SERVER_DIR / "db" / "sql"
TABLES_SQL_DIR = SQL_DIR / "tables"
DATABASES = ("ai_alchemy", "ai_alchemy_test")


def load_mysql_config() -> dict[str, str | int]:
    load_dotenv(SERVER_DIR / ".env")

    database_url = os.getenv("DATABASE_URL", "").strip()
    if database_url:
        return parse_database_url(database_url)

    host = os.getenv("MYSQL_HOST", "127.0.0.1")
    port = int(os.getenv("MYSQL_PORT", "3306"))
    user = os.getenv("MYSQL_USER", "root")
    password = os.getenv("MYSQL_PASSWORD", "")
    return {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
    }


def parse_database_url(url: str) -> dict[str, str | int]:
    # mysql+pymysql://user:pass@host:3306/dbname?charset=utf8mb4
    normalized = url.replace("mysql+pymysql://", "mysql://", 1)
    parsed = urlparse(normalized)
    if not parsed.hostname or not parsed.username:
        raise ValueError("DATABASE_URL 格式无效")
    return {
        "host": parsed.hostname,
        "port": parsed.port or 3306,
        "user": unquote(parsed.username),
        "password": unquote(parsed.password or ""),
    }


def read_sql(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def split_statements(sql: str) -> list[str]:
    statements: list[str] = []
    for part in re.split(r";\s*\n", sql):
        cleaned = "\n".join(
            line for line in part.splitlines() if line.strip() and not line.strip().startswith("--")
        ).strip()
        if cleaned:
            statements.append(cleaned)
    return statements


def execute_sql_file(cursor: pymysql.cursors.Cursor, path: Path) -> None:
    for statement in split_statements(read_sql(path)):
        cursor.execute(statement)


def list_table_sql_files() -> list[Path]:
    if not TABLES_SQL_DIR.is_dir():
        return []
    return sorted(TABLES_SQL_DIR.glob("*.sql"))


def execute_sql_files_in_database(
    config: dict[str, str | int],
    database: str,
    sql_paths: list[Path],
) -> None:
    connection = pymysql.connect(
        host=str(config["host"]),
        port=int(config["port"]),
        user=str(config["user"]),
        password=str(config["password"]),
        database=database,
        charset="utf8mb4",
        autocommit=True,
    )
    try:
        with connection.cursor() as cursor:
            for sql_path in sql_paths:
                for statement in split_statements(read_sql(sql_path)):
                    cursor.execute(statement)
    finally:
        connection.close()


def verify_tables(config: dict[str, str | int], database: str) -> list[str]:
    connection = pymysql.connect(
        host=str(config["host"]),
        port=int(config["port"]),
        user=str(config["user"]),
        password=str(config["password"]),
        database=database,
        charset="utf8mb4",
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            return sorted(row[0] for row in cursor.fetchall())
    finally:
        connection.close()


def main() -> int:
    config = load_mysql_config()
    create_db_sql = SQL_DIR / "01_create_databases.sql"
    table_sql_files = list_table_sql_files()

    if not create_db_sql.exists() or not table_sql_files:
        print("错误：SQL 文件缺失（需 01_create_databases.sql 与 sql/tables/*.sql）", file=sys.stderr)
        return 1

    print(f"连接 MySQL {config['host']}:{config['port']} 用户={config['user']}")

    connection = pymysql.connect(
        host=str(config["host"]),
        port=int(config["port"]),
        user=str(config["user"]),
        password=str(config["password"]),
        charset="utf8mb4",
        autocommit=True,
    )
    try:
        with connection.cursor() as cursor:
            print("执行 01_create_databases.sql ...")
            execute_sql_file(cursor, create_db_sql)
    finally:
        connection.close()

    expected_tables = {"users", "quiz_records", "wrong_questions", "exp_logs", "generation_tasks"}

    for database in DATABASES:
        print(f"在库 `{database}` 执行建表脚本 ({len(table_sql_files)} 个文件) ...")
        for sql_path in table_sql_files:
            print(f"  - {sql_path.name}")
        execute_sql_files_in_database(config, database, table_sql_files)
        tables = set(verify_tables(config, database))
        missing = expected_tables - tables
        if missing:
            print(f"错误：库 `{database}` 缺少表: {', '.join(sorted(missing))}", file=sys.stderr)
            return 1
        print(f"库 `{database}` 表已就绪: {', '.join(sorted(tables))}")

    print("数据库初始化完成。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
