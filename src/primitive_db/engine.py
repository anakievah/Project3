from __future__ import annotations

from typing import Any

from prettytable import PrettyTable
import prompt  # type: ignore[import-not-found]

from src.constants import (
    HELP_HEADER_DATA,
    HELP_HEADER_TABLES,
    INVALID_VALUE_TEMPLATE,
    META_FILE,
    PROMPT_COMMAND,
    UNKNOWN_COMMAND_TEMPLATE,
)

from . import core
from .parser import (
    parse_create_table,
    parse_insert,
    parse_set,
    parse_where,
    split_command,
)
from .utils import load_metadata, save_metadata, load_table_data, save_table_data


def print_help_tables() -> None:
    """Print help for table management commands."""
    print()
    print(HELP_HEADER_TABLES)
    print("Функции:")
    print("  create_table <имя> <столбец1:тип> ...  - создать таблицу")
    print("  list_tables                             - список таблиц")
    print("  drop_table <имя>                        - удалить таблицу")
    print()
    print("Общие команды:")
    print("  help    - справка")
    print("  exit    - выход")
    print()


def print_help_data() -> None:
    """Print help for CRUD operations."""
    print()
    print(HELP_HEADER_DATA)
    print("Функции:")
    print("  insert into <имя> values (v1, v2, ...)           - добавить запись")
    print(
        "  select from <имя> [where колонка = значение]    - выбрать записи",
    )
    print(
        "  update <имя> set колонка = значение "
        "where колонка = значение  - обновить записи",
    )
    print(
        "  delete from <имя> where колонка = значение      - удалить записи",
    )
    print("  info <имя>                                      - информация о таблице")
    print()
    print("Общие команды:")
    print("  help    - справка")
    print("  exit    - выход")
    print()


def welcome() -> None:
    """Initial greeting and minimal instructions."""
    print("Добро пожаловать в примитивную консольную БД.")
    print("Для просмотра доступных команд введите: help")
    print("Для выхода используйте: exit")
    print()


def _print_select_result(rows: list[dict[str, Any]]) -> None:
    if not rows:
        print("Данные не найдены.")
        return
    columns = list(rows[0].keys())
    table = PrettyTable()
    table.field_names = columns
    for row in rows:
        table.add_row([row.get(col, "") for col in columns])
    print(table)


def _handle_info(metadata: dict[str, Any], tokens: list[str]) -> None:
    if len(tokens) != 2:
        raise ValueError("Ожидалось: info <имя_таблицы>.")
    table_name = tokens[1]
    result = core.info(metadata, table_name)
    if not result:
        return
    print()
    print(f"Таблица: {table_name}")
    cols = result["columns"]
    print(
        "Столбцы: "
        + ", ".join(f"{name}:{type_name}" for name, type_name in cols),
    )
    print(f"Количество записей: {result['rows']}")
    print()


def run() -> None:
    """Main REPL loop."""
    while True:
        metadata = load_metadata(META_FILE)
        try:
            raw = input(PROMPT_COMMAND)
        except (EOFError, KeyboardInterrupt):
            print("\nВыход из программы.")
            break

        line = raw.strip()
        if not line:
            continue

        if line.lower() == "exit":
            print("Работа завершена.")
            break

        if line.lower() == "help":
            print_help_tables()
            print_help_data()
            continue

        try:
            tokens = split_command(line)
            if not tokens:
                continue
            cmd = tokens[0].lower()

            if cmd == "create_table":
                table_name, columns_spec = parse_create_table(tokens[1:])
                new_meta = core.create_table(metadata, table_name, columns_spec)
                if new_meta is not None:
                    save_metadata(META_FILE, new_meta)

            elif cmd == "list_tables":
                names = core.list_tables(metadata) or []
                if not names:
                    print("Таблицы ещё не созданы.")
                else:
                    print("Существующие таблицы:")
                    for name in names:
                        print(f"- {name}")

            elif cmd == "drop_table":
                if len(tokens) != 2:
                    raise ValueError("Ожидалось: drop_table <имя_таблицы>.")
                table_name = tokens[1]
                new_meta = core.drop_table(metadata, table_name)
                if new_meta is not None:
                    save_metadata(META_FILE, new_meta)

            elif cmd == "insert":
                table_name, values = parse_insert(tokens)
                data = core.insert(metadata, table_name, values)
                if data is not None:
                    save_table_data(table_name, data)

            elif cmd == "select":
                if len(tokens) < 3 or tokens[1].lower() != "from":
                    raise ValueError(
                        "Ожидалось: select from <таблица> [where колонка = значение].",
                    )
                table_name = tokens[2]
                where = None
                if len(tokens) > 3:
                    # ищем where
                    if tokens[3].lower() != "where":
                        raise ValueError(
                            "Ожидалось ключевое слово where после имени таблицы.",
                        )
                    where = parse_where(tokens[4:])
                rows = core.select(metadata, table_name, where) or []
                _print_select_result(rows)

            elif cmd == "update":
                # update <table> set ... where ...
                if len(tokens) < 6 or tokens[2].lower() != "set":
                    raise ValueError(
                        "Ожидалось: update <таблица> set кол=знач where кол=знач.",
                    )
                table_name = tokens[1]
                if "where" not in [t.lower() for t in tokens]:
                    raise ValueError("Ожидалось условие where.")
                where_index = next(
                    i for i, t in enumerate(tokens) if t.lower() == "where"
                )
                set_tokens = tokens[3:where_index]
                where_tokens = tokens[where_index + 1 :]
                set_clause = parse_set(set_tokens)
                where_clause = parse_where(where_tokens)
                data = core.update(metadata, table_name, set_clause, where_clause)
                if data is not None:
                    save_table_data(table_name, data)

            elif cmd == "delete":
                # delete from <table> where ...
                if len(tokens) < 5 or tokens[1].lower() != "from":
                    raise ValueError(
                        "Ожидалось: delete from <таблица> where кол=знач.",
                    )
                if "where" not in [t.lower() for t in tokens]:
                    raise ValueError("Ожидалось условие where.")
                table_name = tokens[2]
                where_index = next(
                    i for i, t in enumerate(tokens) if t.lower() == "where"
                )
                where_tokens = tokens[where_index + 1 :]
                where_clause = parse_where(where_tokens)
                data = core.delete(metadata, table_name, where_clause)
                if data is not None:
                    save_table_data(table_name, data)

            elif cmd == "info":
                _handle_info(metadata, tokens)

            else:
                print(UNKNOWN_COMMAND_TEMPLATE.format(cmd=line))

        except ValueError as exc:
            print(INVALID_VALUE_TEMPLATE.format(val=exc))
        except Exception as exc:  # noqa: BLE001
            # fallback для неклассифицированных ошибок
            print(f"Ошибка обработки команды: {exc}")
