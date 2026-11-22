"""The generated notebooks stay in sync with notebooks/src and their code cells are valid Python."""
import json
import os
import re
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import build_notebooks  # noqa: E402

IPYTHON_LINE = re.compile(r"^(\s*)(?:\w+\s*=\s*)?!")  # `!cmd` and `x = !cmd` are IPython, not Python
NOTEBOOKS = sorted(build_notebooks.outputs().items())
IDS = [os.path.basename(path) for path, _ in NOTEBOOKS]


def python_source(cell):
    lines = "".join(cell["source"]).splitlines()
    return "\n".join(IPYTHON_LINE.sub(r"\1pass  # ", line) for line in lines)


def test_generated_notebooks_are_up_to_date():
    assert build_notebooks.main(["--check"]) == 0


def test_student_version_replaces_solution_with_todo():
    lines = ["x = 1", "    # BEGIN SOLUTION: add one", "    y = x + 1", "    # END SOLUTION", "z = 2"]
    student = build_notebooks.render_code(lines, solution=False)
    assert student == ["x = 1", "    # TODO: add one", '    raise NotImplementedError("TODO: add one")', "z = 2"]
    assert build_notebooks.render_code(lines, solution=True) == ["x = 1", "    y = x + 1", "z = 2"]


def test_unbalanced_markers_are_rejected():
    with pytest.raises(ValueError):
        build_notebooks.render_code(["# BEGIN SOLUTION", "x = 1"], solution=True)
    with pytest.raises(ValueError):
        build_notebooks.render_code(["# END SOLUTION"], solution=True)


@pytest.mark.parametrize("path,text", NOTEBOOKS, ids=IDS)
def test_code_cells_compile(path, text):
    for number, cell in enumerate(json.loads(text)["cells"], 1):
        if cell["cell_type"] == "code":
            compile(python_source(cell), "{} cell {}".format(os.path.basename(path), number), "exec")


@pytest.mark.parametrize("path,text", NOTEBOOKS, ids=IDS)
def test_solutions_only_in_solution_notebooks(path, text):
    assert "BEGIN SOLUTION" not in text and "END SOLUTION" not in text
    if path.endswith("_solution.ipynb"):
        assert "raise NotImplementedError" not in text
    else:
        assert "raise NotImplementedError" in text  # every module has at least one exercise
