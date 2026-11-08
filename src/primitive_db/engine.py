import prompt
from prettytable import PrettyTable

from primitive_db import core
from primitive_db.constants import ID_COLUMN, META_FILE
from primitive_db.decorators import handle_db_errors
from primitive_db.parser import parse_command
from primitive_db.utils import (
    load_metadata,
    load_table_data,
    remove_table_data,
    save_metadata,
    save_table_data,
)

COMMAND_HELP = {
    "create_table": "<таблица> <столбец:тип> ... - создать таблицу",
    "list_tables": "- показать список всех таблиц",
    "drop_table": "<таблица> - удалить таблицу",
    "insert": "into <таблица> values (<значения>) - добавить запись",
    "select": "from <таблица> [where <столбец> = <значение>] - прочитать записи",
    "update": (
        "<таблица> set <столбец> = <значение> "
        "where <столбец> = <значение> - обновить записи"
    ),
    "delete": "from <таблица> where <столбец> = <значение> - удалить записи",
    "info": "<таблица> - показать информацию о таблице",
    "help": "- справочная информация",
    "exit": "- выход из программы",
}


def print_help() -> None:
    print("\n***База данных***")
    print("Функции:")
    for command, description in COMMAND_HELP.items():
        print(f"<command> {command} {description}")


def _format_columns(columns):
    return ", ".join(f"{name}:{column_type}" for name, column_type in columns.items())


def _create_table(metadata, table_name, columns):
    updated = core.create_table(metadata, table_name, columns)
    if updated is not None:
        save_table_data(table_name, [])
        save_metadata(META_FILE, updated)
        schema = _format_columns(updated[table_name])
        print(f'Таблица "{table_name}" успешно создана со столбцами: {schema}')


def _drop_table(metadata, table_name):
    core.get_table_columns(metadata, table_name)
    updated = core.drop_table(metadata, table_name)
    if updated is not None:
        save_metadata(META_FILE, updated)
        remove_table_data(table_name)
        print(f'Таблица "{table_name}" успешно удалена.')


def _insert_row(metadata, table_name, values):
    rows = core.insert(metadata, table_name, values)
    if rows is not None:
        save_table_data(table_name, rows)
        row_id = rows[-1][ID_COLUMN]
        print(f'Запись с ID={row_id} успешно добавлена в таблицу "{table_name}".')


def _validate_clause(columns, clause):
    for column, value in clause.items():
        if column not in columns:
            raise KeyError(f'Столбец "{column}" не найден.')
        core.validate_value(value, columns[column])


def _print_rows(columns, rows):
    table = PrettyTable(list(columns))
    for row in rows:
        table.add_row([row[column] for column in columns])
    print(table)


def _save_row_changes(table_name, original, changed, where, message):
    if changed is None:
        return
    ids = [row[ID_COLUMN] for row in original if core.matches_where(row, where)]
    if not ids:
        print("Подходящие записи не найдены.")
        return
    save_table_data(table_name, changed)
    for row_id in ids:
        print(f"Запись с ID={row_id} {message}")


def _run_data_command(command, metadata, table_name, *args):
    if command == "insert":
        _insert_row(metadata, table_name, args[0])
        return

    columns = core.get_table_columns(metadata, table_name)
    rows = load_table_data(table_name)
    if command == "info":
        print(f"Таблица: {table_name}")
        print(f"Столбцы: {_format_columns(columns)}")
        print(f"Количество записей: {len(rows)}")
        return

    where = args[-1]
    if where is not None:
        _validate_clause(columns, where)
    if command == "select":
        selected = core.select(rows, where)
        if selected is not None:
            _print_rows(columns, selected)
    elif command == "update":
        values = args[0]
        _validate_clause(columns, values)
        changed = core.update(rows, values, where)
        message = f'в таблице "{table_name}" успешно обновлена.'
        _save_row_changes(table_name, rows, changed, where, message)
    else:
        changed = core.delete(rows, where)
        message = f'успешно удалена из таблицы "{table_name}".'
        _save_row_changes(table_name, rows, changed, where, message)


@handle_db_errors
def _run_command(command, *args):
    metadata = load_metadata(META_FILE)
    if command == "list_tables":
        for table_name in metadata:
            print(f"- {table_name}")
    elif command == "create_table":
        _create_table(metadata, *args)
    elif command == "drop_table":
        _drop_table(metadata, *args)
    else:
        _run_data_command(command, metadata, *args)


def run() -> None:
    print_help()
    while True:
        try:
            command, *args = parse_command(prompt.string(">>> Введите команду: "))
        except (EOFError, KeyboardInterrupt):
            print()
            return
        except ValueError as error:
            print(f"Некорректное значение: {error}. Попробуйте снова.")
            continue

        if command == "exit":
            return
        if command == "help":
            print_help()
        elif command in COMMAND_HELP:
            _run_command(command, *args)
        elif command:
            print(f"Функции {command} нет. Попробуйте снова.")
