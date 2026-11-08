import shlex


def _tokenize(text: str) -> list[str]:
    lexer = shlex.shlex(text, posix=False, punctuation_chars="=,()")
    lexer.whitespace_split = True
    lexer.commenters = ""
    try:
        return list(lexer)
    except ValueError as error:
        raise ValueError(text) from error


def _parse_value(token: str) -> str | int | bool:
    if token.startswith(("'", '"')):
        return token[1:-1]
    if token.lower() == "true":
        return True
    if token.lower() == "false":
        return False
    digits = token[1:] if token.startswith(("+", "-")) else token
    if digits.isdecimal():
        return int(token)
    raise ValueError(token)


def _parse_values(tokens: list[str]) -> list:
    match tokens:
        case ["()"] | ["(", ")"]:
            return []
        case ["(", *values, ")"] if len(values) % 2 == 1:
            if all(separator == "," for separator in values[1::2]):
                return [_parse_value(value) for value in values[::2]]
    raise ValueError(" ".join(tokens))


def _parse_condition(tokens: list[str]) -> dict:
    match tokens:
        case [column, "=", value] if column.isidentifier():
            return {column: _parse_value(value)}
    raise ValueError(" ".join(tokens))


def _parse_assignments(tokens: list[str]) -> dict:
    if len(tokens) % 4 != 3 or any(token != "," for token in tokens[3::4]):
        raise ValueError(" ".join(tokens))

    assignments = {}
    for index in range(0, len(tokens), 4):
        assignment = _parse_condition(tokens[index : index + 3])
        if assignments.keys() & assignment.keys():
            raise ValueError(" ".join(tokens))
        assignments.update(assignment)
    return assignments


def parse_command(user_input: str) -> tuple:
    tokens = _tokenize(user_input)
    if not tokens:
        return ("",)

    command, *args = tokens
    command = command.lower()
    match command:
        case "help" | "exit" | "list_tables":
            if not args:
                return (command,)
        case "drop_table" | "info":
            if len(args) == 1:
                return command, args[0]
        case "create_table":
            if len(args) >= 2:
                table, *columns = args
                return command, table, columns
        case "insert":
            match args:
                case [into, table, values_keyword, *values] if (
                    into.lower() == "into" and values_keyword.lower() == "values"
                ):
                    return command, table, _parse_values(values)
        case "select":
            match args:
                case [source, table] if source.lower() == "from":
                    return command, table, None
                case [source, table, where, *condition] if (
                    source.lower() == "from" and where.lower() == "where"
                ):
                    return command, table, _parse_condition(condition)
        case "update":
            match args:
                case [table, keyword, *clauses] if keyword.lower() == "set":
                    for index in range(3, len(clauses), 4):
                        if clauses[index].lower() == "where":
                            assignments = _parse_assignments(clauses[:index])
                            condition = _parse_condition(clauses[index + 1 :])
                            return command, table, assignments, condition
        case "delete":
            match args:
                case [source, table, where, *condition] if (
                    source.lower() == "from" and where.lower() == "where"
                ):
                    return command, table, _parse_condition(condition)
        case _:
            return (tokens[0],)

    raise ValueError(user_input)
