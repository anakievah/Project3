from __future__ import annotations

import shlex
from typing import Any


def split_command(line: str) -> list[str]:
    """Split user input into tokens."""
    # Для Windows лучше posix=False, но команды здесь простые.
    return shlex.split(line, posix=False)


def parse_create_table(args: list[str]) -> tuple[str, list[str]]:
    """Parse create_table <name> col1:type col2:type ..."""
    if len(args) < 2:
        raise ValueError("Недостаточно аргументов для create_table.")
    table_name = args[0]
    columns_spec = args[1:]
    return table_name, columns_spec


def _parse_literal(value: str) -> Any:
    """Convert string literal to Python type according to simple rules."""
    lower = value.lower()
    if lower == "true":
        return True
    if lower == "false":
        return False
    if value.isdigit() or (value.startswith("-") and value[1:].isdigit()):
        return int(value)
    # строковые значения считаем уже очищенными от кавычек
    return value


def parse_values_segment(segment: str) -> list[str]:
    """Parse '(v1, v2, ...)' into a list of raw string values."""
    if not (segment.startswith("(") and segment.endswith(")")):
        raise ValueError("Ожидался список значений в скобках.")
    inner = segment[1:-1]
    parts = [p.strip() for p in inner.split(",") if p.strip()]
    # удаляем внешние кавычки у строк, если они есть
    cleaned: list[str] = []
    for item in parts:
        if (item.startswith('"') and item.endswith('"')) or (
            item.startswith("'") and item.endswith("'")
        ):
            cleaned.append(item[1:-1])
        else:
            cleaned.append(item)
    return cleaned


def parse_insert(tokens: list[str]) -> tuple[str, list[str]]:
    """Parse: insert into <table> values (<...>)"""
    # ожидаем: insert, into, <table>, values, (<...>)
    if len(tokens) < 5:
        raise ValueError("Недостаточно аргументов для insert.")
    if tokens[0].lower() != "insert" or tokens[1].lower() != "into":
        raise ValueError("Неверный синтаксис команды insert.")
    if "values" not in [t.lower() for t in tokens]:
        raise ValueError("Отсутствует ключевое слово values.")
    table_name = tokens[2]
    # всё после 'values' собираем обратно в одну строку
    values_index = next(
        i for i, t in enumerate(tokens) if t.lower() == "values"
    )
    values_segment = " ".join(tokens[values_index + 1 :]).strip()
    values = parse_values_segment(values_segment)
    return table_name, values


def parse_where(tokens: list[str]) -> dict[str, Any]:
    """Parse 'col = value' tokens into dict."""
    if len(tokens) < 3:
        raise ValueError("Некорректное условие where.")
    if tokens[1] != "=":
        raise ValueError("Ожидался оператор '=' в where.")
    column = tokens[0]
    value_str = " ".join(tokens[2:])
    if (
        (value_str.startswith('"') and value_str.endswith('"'))
        or (value_str.startswith("'") and value_str.endswith("'"))
    ):
        value_str = value_str[1:-1]
    value = _parse_literal(value_str)
    return {column: value}


def parse_set(tokens: list[str]) -> dict[str, Any]:
    """Parse 'col = value' for set clause."""
    return parse_where(tokens)
