# Primitive DB Project

Примитивная консольная база данных на Python с использованием Poetry.

## Установка

```bash
make install
# или
poetry install
```

## Запуск

```bash
make project
# или
poetry run project
```

## Makefile

| Команда | Описание |
|---------|----------|
| `make install` | Установить зависимости |
| `make project` | Запустить БД |
| `make lint` | Проверка стиля |
| `make build` | Сборка пакета |
| `make publish` | Тест публикации |

## Команды БД

```
create_table users name:str age:int isActive:bool
insert into users values ("test", 20, true)
select from users
select from users where ID = 1
update users set age = 21 where ID = 1
info users
drop_table users
exit
```

## Демонстрация

[![asciicast](https://asciinema.org/a/zz7inXnZQYE4axhy.svg)](https://asciinema.org/a/zz7inXnZQYE4axhy)

## Проверки

```bash
make lint  # All checks passed!
```