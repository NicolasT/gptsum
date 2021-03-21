"""
Nox sessions for the `gptsum`_ project.

.. _gptsum: https://github.com/NicolasT/gptsum
"""

import sys
from pathlib import Path
import shutil

from nox_poetry import Session, session

PYTHON_VERSIONS = [
    # Note: keep these sorted
    "3.6",
    "3.7",
    "3.8",
    "3.9",
]

SOURCES = [
    "src/",
    "noxfile.py",
    "docs/conf.py",
]


@session(python=PYTHON_VERSIONS[-1])
def flake8(session: Session) -> None:
    """Lint using flake8."""
    args = session.posargs or SOURCES
    session.install(
        "darglint",
        "flake8",
        "flake8-bandit",
        "flake8-bugbear",
        "flake8-docstrings",
        "flake8-rst-docstrings",
        "pep8-naming",
    )
    session.run("flake8", *args)


@session(python=PYTHON_VERSIONS[-1])
def safety(session: Session) -> None:
    """Scan dependencies for insecure packages."""
    requirements = session.poetry.export_requirements()
    session.install("safety")
    session.run("safety", "check", f"--file={requirements}", "--bare")


@session(python=PYTHON_VERSIONS)
def mypy(session: Session) -> None:
    """Type-check using mypy."""
    args = session.posargs or [src for src in SOURCES if src != "noxfile.py"]
    session.install(".")
    session.install("mypy")
    session.run("mypy", *args)
    if not session.posargs:
        session.run("mypy", f"--python-executable={sys.executable}", "noxfile.py")


@session(python=PYTHON_VERSIONS[-1])
def docs(session: Session) -> None:
    """Build the documentation."""
    args = session.posargs or ["docs", "docs/_build"]
    session.install(".")
    session.install(
        "Sphinx",
        "furo",
    )

    build_dir = Path("docs", "_build")
    if build_dir.exists():
        shutil.rmtree(build_dir)

    session.run("sphinx-build", *args)
