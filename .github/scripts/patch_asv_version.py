#!/usr/bin/env python3
"""Patch asv.util to make version comparison robust for CI.

ASV's config uses a 'version' field that can be a string like '0.5'.
Instead of forcing an int() conversion (which fails for '0.5'),
parse the version more flexibly to a numeric value for comparison.

This script is a temporary CI-time workaround.
"""
import importlib
import sys
import re


def _parse_version_to_number(v):
    """Return a numeric approximation for version strings.

    Tries float() then int(); if that fails extracts a numeric prefix
    like '0.5.1' -> '0.5' and returns float of first two components.
    Falls back to 0 on failure.
    """
    try:
        return float(v)
    except Exception:
        pass
    try:
        return int(v)
    except Exception:
        pass
    s = str(v)
    import re

    m = re.match(r"(\d+(?:\.\d+)*)", s)
    if not m:
        return 0
    parts = m.group(1).split('.')
    try:
        return float('.'.join(parts[:2]))
    except Exception:
        return 0


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

    # Find the 'if data["version"] < api_version:' line capturing indentation
    pattern = re.compile(r"(?m)^([ \t]*)if data\['version'\] < api_version:")
    m = pattern.search(src)
    if not m:
        print('No version-compare pattern found')
        return 0

    indent = m.group(1)
    replacement = (
        f"{indent}vnum = _parse_version_to_number(data.get('version', 0))\n"
        f"{indent}if vnum < api_version:"
    )

    # Insert the helper at the top if missing
    if '_parse_version_to_number' not in src:
        new_src = _generate_helper_src() + "\n" + src[: m.start()] + replacement + src[m.end() :]
    else:
        new_src = src[: m.start()] + replacement + src[m.end() :]

    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_src)
        print('Patched asv.util')
        return 0
    except Exception as e:
        print('Failed to write patch:', e, file=sys.stderr)
        return 1


def _generate_helper_src():
    return (
        "def _parse_version_to_number(v):\n"
        "    try:\n"
        "        return float(v)\n"
        "    except Exception:\n"
        "        pass\n"
        "    try:\n"
        "        return int(v)\n"
        "    except Exception:\n"
        "        pass\n"
        "    import re\n"
        "    m = re.match(r\"(\\d+(?:\\.\\d+)*)\", str(v))\n"
        "    if not m:\n"
        "        return 0\n"
        "    parts = m.group(1).split('.')\n"
        "    try:\n"
        "        return float('.'.join(parts[:2]))\n"
        "    except Exception:\n"
        "        return 0\n"
    )


if __name__ == '__main__':
    sys.exit(main())
