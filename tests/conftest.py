import sys

collect_ignore = []

if sys.version_info < (3, 14):
    collect_ignore.append('test_tstrings.py')
