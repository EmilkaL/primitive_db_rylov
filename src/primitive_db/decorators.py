import time


def handle_db_errors(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError:
            print("Ошибка: Файл данных не найден.")
        except KeyError as error:
            detail = error.args[0] if error.args else "Таблица или столбец не найден."
            print(f"Ошибка: {detail}")
        except ValueError as error:
            print(f"Ошибка валидации: {error}")
        except OSError as error:
            print(f"Ошибка работы с файлами: {error}")

    return wrapper


def confirm_action(action_name):
    def decorate(func):
        def wrapper(*args, **kwargs):
            try:
                answer = input(
                    f'Вы уверены, что хотите выполнить "{action_name}"? [y/n]: '
                )
            except (EOFError, KeyboardInterrupt):
                answer = ""

            if answer.strip().lower() == "y":
                return func(*args, **kwargs)

            print("Операция отменена.")

        return wrapper

    return decorate


def log_time(func):
    def wrapper(*args, **kwargs):
        started = time.monotonic()
        result = func(*args, **kwargs)
        duration = time.monotonic() - started
        print(f"Функция {func.__name__} выполнилась за {duration:.3f} секунд.")
        return result

    return wrapper


def create_cacher():
    cache = {}

    def cache_result(key, value_func):
        if key not in cache:
            cache[key] = value_func()
        return cache[key]

    return cache_result
