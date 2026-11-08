# Primitive DB

Простая база данных для терминала. Схемы таблиц хранятся в `db_meta.json`. У каждой таблицы свой файл с записями в папке `data/`.

## Установка и запуск

Нужны Python 3.12 и `uv`.

```sh
uv sync
uv run database
```

Через Make это `make install` и `make run`.

## Управление таблицами

```text
create_table users name:str age:int is_active:bool
list_tables
info users
```

Программа сама добавляет столбец `ID`. Для остальных столбцов укажи тип `int`, `str` или `bool`.

## CRUD-операции

```text
insert into users values ("Анна", 28, true)
select from users
select from users where age = 28
update users set age = 29 where ID = 1
delete from users where ID = 1
```

Текст в командах бери в кавычки. `insert` и `select` показывают время выполнения. Повторные запросы с тем же фильтром используют кэш.

Чтобы удалить таблицу из примера, введи `drop_table users`. Удаление записей и таблиц нужно подтвердить ответом `y`.

Если команда введена с ошибкой, программа покажет сообщение и снова попросит ввод. `help` открывает справку, `exit` закрывает программу.

## Демонстрация

[Запись Asciinema](https://asciinema.org/a/ylcNilYsVbbM02qI)

В записи показано, как создать таблицу, добавить и изменить запись, посмотреть результат и удалить данные с подтверждением.

## Проверка кода

```sh
uv run ruff check .
```

Или запусти `make lint`.
