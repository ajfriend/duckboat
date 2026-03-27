import random
from string import ascii_lowercase


def _random_name():
    return '_t_' + ''.join(random.choices(ascii_lowercase, k=8))


def _process_template(template):
    parts = []
    tables = {}

    for item in template:
        if isinstance(item, str):
            parts.append(item)
        else:
            value = item.value
            if isinstance(value, bool):
                parts.append(str(value).upper())
            elif isinstance(value, (int, float)):
                parts.append(str(value))
            elif isinstance(value, str):
                escaped = value.replace("'", "''")
                parts.append(f"'{escaped}'")
            elif hasattr(value, '__arrow_c_stream__'):
                expr = item.expression
                name = expr if expr.isidentifier() else _random_name()
                tables[name] = value
                parts.append(name)
            else:
                raise TypeError(
                    f'Expected a scalar or tabular object in t-string, '
                    f'got {type(value).__name__}'
                )

    return ''.join(parts), tables
