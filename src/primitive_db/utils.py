import json
import os

from primitive_db.constants import DATA_DIR


def _load_json(filepath, default):
    try:
        with open(filepath, encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return default


def _save_json(filepath, data):
    temporary_path = f"{filepath}.{os.urandom(8).hex()}.tmp"
    file = open(temporary_path, "x", encoding="utf-8")
    try:
        with file:
            json.dump(data, file, ensure_ascii=False, indent=2)
            file.write("\n")
        os.replace(temporary_path, filepath)
    finally:
        if os.path.exists(temporary_path):
            os.remove(temporary_path)


def validate_table_name(table_name):
    if not table_name.isidentifier():
        raise ValueError(f"Некорректное имя таблицы: {table_name}.")


def _table_path(table_name):
    validate_table_name(table_name)
    return os.path.join(DATA_DIR, f"{table_name}.json")


def load_metadata(filepath):
    return _load_json(filepath, {})


def save_metadata(filepath, data):
    _save_json(filepath, data)


def load_table_data(table_name):
    return _load_json(_table_path(table_name), [])


def save_table_data(table_name, data):
    filepath = _table_path(table_name)
    os.makedirs(DATA_DIR, exist_ok=True)
    _save_json(filepath, data)


def remove_table_data(table_name):
    try:
        os.remove(_table_path(table_name))
    except FileNotFoundError:
        pass
