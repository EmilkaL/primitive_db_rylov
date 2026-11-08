from primitive_db.constants import ID_COLUMN, VALID_TYPES
from primitive_db.decorators import (
    confirm_action,
    create_cacher,
    handle_db_errors,
    log_time,
)
from primitive_db.utils import load_table_data, validate_table_name

_cache_selection = create_cacher()


def get_table_columns(metadata, table_name):
    if table_name not in metadata:
        raise KeyError(f'Таблица "{table_name}" не существует.')
    return metadata[table_name]


def validate_value(value, column_type):
    if type(value) is not VALID_TYPES[column_type]:
        raise ValueError(f"Некорректное значение: {value!r}. Ожидается {column_type}.")


def matches_where(row, where_clause):
    return all(row[column] == value for column, value in where_clause.items())


@handle_db_errors
def create_table(metadata, table_name, columns):
    validate_table_name(table_name)
    if table_name in metadata:
        raise KeyError(f'Таблица "{table_name}" уже существует.')

    schema = {}
    for column in columns:
        name, _, column_type = column.partition(":")
        if not name.isidentifier() or column_type not in VALID_TYPES:
            raise ValueError(f"Некорректное значение: {column}. Попробуйте снова.")
        if name in schema:
            raise ValueError(f'Столбец "{name}" указан несколько раз.')
        if name == ID_COLUMN and column_type != "int":
            raise ValueError(f"Столбец {ID_COLUMN} должен иметь тип int.")
        schema[name] = column_type

    metadata[table_name] = {ID_COLUMN: "int", **schema}
    return metadata


@handle_db_errors
@confirm_action("удаление таблицы")
def drop_table(metadata, table_name):
    get_table_columns(metadata, table_name)
    del metadata[table_name]
    return metadata


@handle_db_errors
@log_time
def insert(metadata, table_name, values):
    columns = get_table_columns(metadata, table_name)
    data_columns = [column for column in columns if column != ID_COLUMN]
    if len(values) != len(data_columns):
        raise ValueError(f"Ожидается значений: {len(data_columns)}.")

    table_data = load_table_data(table_name)
    next_id = max((row[ID_COLUMN] for row in table_data), default=0) + 1
    record = {ID_COLUMN: next_id}
    for column, value in zip(data_columns, values):
        validate_value(value, columns[column])
        record[column] = value
    return [*table_data, record]


@handle_db_errors
@log_time
def select(table_data, where_clause=None):
    if not where_clause:
        return table_data

    rows = tuple(tuple(row.items()) for row in table_data)
    condition = tuple(sorted(where_clause.items()))
    indexes = _cache_selection(
        (rows, condition),
        lambda: [
            index for index, row in enumerate(table_data)
            if matches_where(row, where_clause)
        ],
    )
    return [table_data[index] for index in indexes]


@handle_db_errors
def update(table_data, set_clause, where_clause):
    if ID_COLUMN in set_clause:
        raise ValueError(f"Столбец {ID_COLUMN} нельзя изменять.")
    return [
        {**row, **set_clause} if matches_where(row, where_clause) else row
        for row in table_data
    ]


@handle_db_errors
@confirm_action("удаление записи")
def delete(table_data, where_clause):
    return [row for row in table_data if not matches_where(row, where_clause)]
