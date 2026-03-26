import sys

collect_ignore = []

if sys.version_info < (3, 14):  # pragma: no cover
    collect_ignore.append('test_tstrings.py')  # pragma: no cover
