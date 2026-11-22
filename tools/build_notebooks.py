"""Build the student and solution notebooks from one source per module.

Source: notebooks/src/NN_name.py in "percent" format:

    # %% [markdown]
    # ## Heading
    # %% [setup]                 <- replaced by the standard repo-path cell
    # %%
    x = 1
    # BEGIN SOLUTION: hint shown to students
    answer = 42
    # END SOLUTION

Students get each solution block replaced by the hint and a NotImplementedError;
solutions keep the code and drop the markers. Run from the repo root:

    python3 tools/build_notebooks.py           # write both sets
    python3 tools/build_notebooks.py --check   # exit 1 if the .ipynb files are out of date
"""
import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(ROOT, "notebooks", "src")
STUDENT_DIR = os.path.join(ROOT, "notebooks")
SOLUTION_DIR = os.path.join(ROOT, "notebooks", "solutions")

SETUP_CELL = """\
# หา folder ของ repo แล้วเพิ่มเข้า path เพื่อ import jetbot_nstru ได้ ไม่ว่าจะเปิด notebook จาก folder ไหน
import os, sys
root = os.path.abspath(".")
while not os.path.isdir(os.path.join(root, "jetbot_nstru")):
    if os.path.dirname(root) == root:
        raise RuntimeError("หา folder jetbot_nstru ไม่เจอ: เปิด notebook จากใน repo jetbot-mini-bootcamp-nstru")
    root = os.path.dirname(root)
if root not in sys.path:
    sys.path.insert(0, root)
print("repo:", root)"""

CELL_MARK = re.compile(r"^# %%(?: \[(markdown|setup)\])?\s*$")
BEGIN = re.compile(r"^(\s*)# BEGIN SOLUTION(?::\s*(.*))?$")
END = re.compile(r"^\s*# END SOLUTION\s*$")


def split_cells(text):
    """[(kind, lines)] where kind is 'markdown', 'setup' or 'code'."""
    cells = []
    for line in text.splitlines():
        mark = CELL_MARK.match(line)
        if mark:
            cells.append((mark.group(1) or "code", []))
        elif cells:
            cells[-1][1].append(line)
        elif line.strip():
            raise ValueError("text before the first '# %%' marker: {!r}".format(line))
    return cells


def render_code(lines, solution):
    out = []
    inside = False
    for number, line in enumerate(lines, 1):
        begin = BEGIN.match(line)
        if begin:
            if inside:
                raise ValueError("nested BEGIN SOLUTION at cell line {}".format(number))
            inside = True
            if not solution:
                indent, hint = begin.group(1), begin.group(2) or "เขียนโค้ดส่วนนี้"
                out.append("{}# TODO: {}".format(indent, hint))
                out.append('{}raise NotImplementedError("TODO: {}")'.format(indent, hint.replace('"', "'")))
        elif END.match(line):
            if not inside:
                raise ValueError("END SOLUTION without BEGIN at cell line {}".format(number))
            inside = False
        elif solution or not inside:
            out.append(line)
    if inside:
        raise ValueError("BEGIN SOLUTION without END")
    return out


def render_markdown(lines):
    return [line[2:] if line.startswith("# ") else line.lstrip("#") for line in lines]


def trim(lines):
    while lines and not lines[0].strip():
        lines = lines[1:]
    while lines and not lines[-1].strip():
        lines = lines[:-1]
    return lines


def to_source(lines):
    return [line + "\n" for line in lines[:-1]] + lines[-1:]


def build(text, solution):
    cells = []
    for kind, lines in split_cells(text):
        if kind == "markdown":
            body, cell_type = render_markdown(lines), "markdown"
        elif kind == "setup":
            body, cell_type = SETUP_CELL.splitlines(), "code"
        else:
            body, cell_type = render_code(lines, solution), "code"
        cell = {"cell_type": cell_type, "metadata": {}, "source": to_source(trim(body))}
        if cell_type == "code":
            cell.update(execution_count=None, outputs=[])
        cells.append(cell)
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def outputs():
    """{path: notebook json text} for every source file."""
    result = {}
    for name in sorted(os.listdir(SRC_DIR)):
        if not name.endswith(".py"):
            continue
        stem = name[:-3]
        with open(os.path.join(SRC_DIR, name), encoding="utf-8") as handle:
            text = handle.read()
        for directory, filename, solution in (
            (STUDENT_DIR, stem + ".ipynb", False),
            (SOLUTION_DIR, stem + "_solution.ipynb", True),
        ):
            notebook = build(text, solution)
            result[os.path.join(directory, filename)] = json.dumps(notebook, ensure_ascii=False, indent=1) + "\n"
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="fail if generated notebooks are stale")
    args = parser.parse_args(argv)
    stale = []
    for path, text in outputs().items():
        current = open(path, encoding="utf-8").read() if os.path.exists(path) else None
        if current != text:
            stale.append(os.path.relpath(path, ROOT))
            if not args.check:
                with open(path, "w", encoding="utf-8") as handle:
                    handle.write(text)
    if args.check and stale:
        print("stale notebooks, run python3 tools/build_notebooks.py:\n  " + "\n  ".join(stale))
        return 1
    print("{} notebook(s) {}".format(len(stale), "stale" if args.check else "written"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
