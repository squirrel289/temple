#!/usr/bin/env python3
"""Patch asv.util to ensure data['version'] is cast to int before compare.

This is a temporary workaround applied in CI when running `asv`.
"""
import importlib
import sys


def main():
    try:
        m = importlib.import_module('asv.util')
    except Exception as e:
        print('Could not import asv.util:', e, file=sys.stderr)
        return 1
    path = getattr(m, '__file__', None)
    if not path:
        print('asv.util module has no __file__', file=sys.stderr)
        return 1
    print('Patching', path)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            src = f.read()
    except Exception as e:
        print('Failed to read file:', e, file=sys.stderr)
        return 1

    old = "if data['version'] < api_version:"
    new = "if int(data.get('version', 0)) < api_version:"
    if old in src:
        new_src = src.replace(old, new)
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_src)
            print('Patched asv.util')
            return 0
        except Exception as e:
            print('Failed to write patch:', e, file=sys.stderr)
            return 1
    else:
        print('No patch needed')
        return 0


if __name__ == '__main__':
    sys.exit(main())
