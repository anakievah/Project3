from __future__ import annotations

import time
from functools import wraps
from typing import Any, Callable


def handle_db_errors(func: Callable[..., Any]) -> Callable[..., Any]:
    """Wrap DB function and print readable errors instead of raw traces."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except FileNotFoundError:
            print(
                "Ошибка: необходимый файл данных отсутствует. "
                "Проверьте, инициализирована ли база.",
            )
        except KeyError as exc:
            print(f"Ошибка: объект {exc!r} не найден (таблица или столбец).")
        except ValueError as exc:
            print(f"Ошибка проверки данных: {exc}")
        except Exception as exc:  # noqa: BLE001
            print(f"Непредвиденная ошибка: {exc}")
        return None

    return wrapper


def confirm_action(action_name: str) -> Callable:
    """Ask user to confirm dangerous operations."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            prompt = f'Вы уверены, что хотите выполнить "{action_name}"? [y/n]: '
            answer = input(prompt).strip().lower()
            if answer != "y":
                print("Операция отменена пользователем.")
                return None
            return func(*args, **kwargs)

        return wrapper

    return decorator


def log_time(func: Callable[..., Any]) -> Callable[..., Any]:
    """Measure and print execution time of wrapped function."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.monotonic()
        result = func(*args, **kwargs)
        duration = time.monotonic() - start
        print(f"Функция {func.__name__} выполнилась за {duration:.3f} сек.")
        return result

    return wrapper


def create_cacher() -> Callable[[Any, Callable[[], Any]], Any]:
    """Return closure for simple key-based caching."""

    cache: dict[Any, Any] = {}

    def cache_result(key: Any, value_func: Callable[[], Any]) -> Any:
        if key in cache:
            return cache[key]
        value = value_func()
        cache[key] = value
        return value

    return cache_result
