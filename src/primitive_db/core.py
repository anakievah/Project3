from __future__ import annotations

from typing import Any

from src.constants import VALID_TYPES
from src.decorators import confirm_action, create_cacher, handle_db_errors, log_time
from .utils import load_table_data, save_table_data

_cacher = create_cacher()


def _parse_column_spec(spec: str) -> tuple[str, str]:
    if ":" not in spec:
        raise ValueError(f"Не указан тип столбца: {spec}")
    name, type_name = spec.split(":", 1)
    name = name.strip()
    type_name = type_name.strip()
    if type_name not in VALID_TYPES:
        raise ValueError(f"Недопустимый тип столбца: {type_name}")
    return name, type_name


@handle_db_errors
def list_tables(metadata: dict[str, Any]) -> list[str]:
    """Return list of table names."""
    return sorted(metadata.keys())

@handle_db_errors
def create_table(
    metadata: dict[str, Any],
    table_name: str,
    columns_spec: list[str],
) -> dict[str, Any]:
    """Create table schema in metadata."""
    if table_name in metadata:
        raise ValueError(f'Таблица "{table_name}" уже существует.')
    parsed_columns = [("ID", "int")]
    for spec in columns_spec:
        parsed_columns.append(_parse_column_spec(spec))
    metadata[table_name] = {"columns": parsed_columns}
    print(
        f'Таблица "{table_name}" создана. '
        f"Столбцы: {', '.join(f'{n}:{t}' for n, t in parsed_columns)}",
    )
    return metadata


@confirm_action("удаление таблицы")
@handle_db_errors
def drop_table(metadata: dict[str, Any], table_name: str) -> dict[str, Any]:
    """Remove table schema from metadata."""
    if table_name not in metadata:
        raise KeyError(table_name)
    metadata.pop(table_name)

    # удаляем файл данных
    from .utils import _table_path
    data_file = _table_path(table_name)
    import os
    if os.path.exists(data_file):
        os.remove(data_file)

    print(f'Таблица "{table_name}" удалена.')
    return metadata


def _convert_value(raw: str, type_name: str) -> Any:
    if type_name == "int":
        return int(raw)
    if type_name == "bool":
        lower = str(raw).lower()
        if lower == "true":
            return True
        if lower == "false":
            return False
        raise ValueError(f"Ожидалось логическое значение, получено: {raw}")
    # str
    return str(raw)


def _get_schema(metadata: dict[str, Any], table_name: str) -> list[tuple[str, str]]:
    if table_name not in metadata:
        raise KeyError(table_name)
    return list(metadata[table_name]["columns"])


@log_time
@handle_db_errors
def insert(
    metadata: dict[str, Any],
    table_name: str,
    values: list[str],
) -> list[dict[str, Any]]:
    """Insert record into table."""
    schema = _get_schema(metadata, table_name)
    # первый столбец ID:int не задается пользователем
    non_id_columns = schema[1:]
    if len(values) != len(non_id_columns):
        raise ValueError("Количество значений не совпадает со схемой.")
    data = load_table_data(table_name)
    if data:
        new_id = max(int(row["ID"]) for row in data) + 1
    else:
        new_id = 1
    record: dict[str, Any] = {"ID": new_id}
    for raw_val, (col_name, col_type) in zip(values, non_id_columns, strict=True):
        record[col_name] = _convert_value(raw_val, col_type)
    data.append(record)
    print(f'Запись с ID={new_id} добавлена в таблицу "{table_name}".')
    return data


def _match_where(record: dict[str, Any], where: dict[str, Any]) -> bool:
    for key, val in where.items():
        if key not in record or record[key] != val:
            return False
    return True


@log_time
@handle_db_errors
def select(
    metadata: dict[str, Any],
    table_name: str,
    where: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    _ = _get_schema(metadata, table_name)

    if where is None:
        return load_table_data(table_name)

    key = (table_name, frozenset(where.items()))

    def load() -> list[dict[str, Any]]:
        data = load_table_data(table_name)
        return [row for row in data if _match_where(row, where)]

    return _cacher(key, load)

@log_time
@handle_db_errors
def update(
    metadata: dict[str, Any],
    table_name: str,
    set_clause: dict[str, Any],
    where: dict[str, Any],
) -> list[dict[str, Any]]:
    """Update records matching where with new values from set_clause."""
    schema = _get_schema(metadata, table_name)
    type_by_name = {name: t for name, t in schema}
    data = load_table_data(table_name)
    updated_count = 0
    for row in data:
        if _match_where(row, where):
            for col, raw_val in set_clause.items():
                if col not in type_by_name:
                    raise KeyError(col)
                col_type = type_by_name[col]
                row[col] = _convert_value(str(raw_val), col_type)
            updated_count += 1
    print(
        f'Обновлено записей в таблице "{table_name}": {updated_count}.',
    )
    return data


@confirm_action("удаление записей")
@log_time
@handle_db_errors
def delete(
    metadata: dict[str, Any],
    table_name: str,
    where: dict[str, Any],
) -> list[dict[str, Any]]:
    """Delete records matching where from table."""
    _ = _get_schema(metadata, table_name)
    data = load_table_data(table_name)
    new_data = [row for row in data if not _match_where(row, where)]
    removed = len(data) - len(new_data)
    print(
        f'Удалено записей из таблицы "{table_name}": {removed}.',
    )
    return new_data


@handle_db_errors
def info(metadata: dict[str, Any], table_name: str) -> dict[str, Any]:
    """Return table schema and record count."""
    schema = _get_schema(metadata, table_name)
    data = load_table_data(table_name)
    return {"columns": schema, "rows": len(data)}
