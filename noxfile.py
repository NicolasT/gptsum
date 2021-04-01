"""
Nox sessions for the `gptsum`_ project.

.. _gptsum: https://github.com/NicolasT/gptsum
"""

import shutil
import sys
import tempfile
from pathlib import Path

import nox
from nox_poetry import SDIST, Session, session

PACKAGE = "gptsum"

PYTHON_VERSIONS = [
    # Note: keep these sorted
    "3.6",
    "3.7",
    "3.8",
    "3.9",
]

SOURCES = [
    "src/",
    "tests/",
    "noxfile.py",
    "docs/conf.py",
]

# Versions of various packages as found in CentOS 8 + EPEL
# Retrieved by running the Nox session, running `pip freeze` in its virtualenv,
# then looking up package versions using `dnf info ...`.
CENTOS8_CONSTRAINTS = b"""
attrs==17.4.0
coverage==4.5.1
dataclasses==0.8
importlib-metadata==0.23
packaging==16.8
pip==9.0.3
pluggy==0.6.0
py==1.5.3
py-cpuinfo==5.0.0
pytest==3.4.2
pytest-benchmark==3.1.1
pytest-mock==1.10.4
setuptools==39.2.0
six==1.11.0
typing-extensions==3.7.4.2
zipp==0.5.1
"""


@session(python=PYTHON_VERSIONS[-1])
def flake8(session: Session) -> None:
    """Lint using flake8."""
    args = session.posargs or SOURCES
    session.install(
        "darglint",
        "flake8",
        "flake8-bandit",
        "flake8-black",
        "flake8-bugbear",
        "flake8-builtins",
        "flake8-docstrings",
        "flake8-expression-complexity",
        "flake8-isort",
        "flake8-pytest",
        "flake8-pytest-style",
        "flake8-return",
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
    session.install(
        "mypy",
        "packaging",
        "py",
        "pytest",
        "pytest-benchmark",
        "pytest-mock",
    )
    session.run("mypy", *args)
    if not session.posargs:
        session.run("mypy", f"--python-executable={sys.executable}", "noxfile.py")


@session(python=PYTHON_VERSIONS)
def tests(session: Session) -> None:
    """Run the test suite."""
    session.install(".")
    session.install(
        "coverage[toml]",
        "packaging",
        "py",
        "pygments",
        "pytest",
        "pytest-benchmark",
        "pytest-mock",
    )
    try:
        session.run("coverage", "run", "--parallel", "-m", "pytest", *session.posargs)
    finally:
        if session.interactive:
            session.notify("coverage")


@nox.session(python=["3.6"])
def tests_centos8(session: nox.Session) -> None:
    """Run the tests using (pinned) dependency versions as shipped with CentOS 8."""
    with tempfile.NamedTemporaryFile() as fd:
        fd.write(CENTOS8_CONSTRAINTS)
        fd.flush()

        poetry_session = Session(session)
        package = poetry_session.poetry.build_package(distribution_format=SDIST)
        # Version of 'coverage' must be consistent with other sessions
        poetry_session.install(
            "coverage[toml]",
        )
        session.install(f"--constraint={fd.name}", package)
        session.install(
            f"--constraint={fd.name}",
            "packaging",
            "py",
            "pytest",
            "pytest-benchmark",
            "pytest-mock",
        )

    try:
        session.run("coverage", "run", "--parallel", "-m", "pytest", *session.posargs)
    finally:
        if session.interactive:
            session.notify("coverage")


@session
def coverage(session: Session) -> None:
    """Produce the coverage report."""
    # Do not use session.posargs unless this is the only session.
    nsessions = len(session._runner.manifest)  # type: ignore[attr-defined]
    has_args = session.posargs and nsessions == 1
    args = session.posargs if has_args else ["report"]

    session.install(
        "coverage[toml]",
    )

    if not has_args and any(Path().glob(".coverage.*")):
        session.run("coverage", "combine")

    session.run("coverage", *args)


@session(python=PYTHON_VERSIONS)
def typeguard(session: Session) -> None:
    """Runtime type checking using Typeguard."""
    session.install(".")
    session.install(
        "packaging",
        "py",
        "pygments",
        "pytest",
        "pytest-benchmark",
        "pytest-mock",
        "typeguard",
    )
    session.run("pytest", f"--typeguard-packages={PACKAGE}", *session.posargs)


@session(python=PYTHON_VERSIONS)
def xdoctest(session: Session) -> None:
    """Run examples with xdoctest."""
    args = session.posargs or ["all"]
    session.install(".")
    session.install(
        "xdoctest[colors]",
    )
    session.run("python", "-m", "xdoctest", PACKAGE, *args)


@session(python=PYTHON_VERSIONS[-1])
def docs(session: Session) -> None:
    """Build the documentation."""
    args = session.posargs or ["docs", "docs/_build"]
    session.install(".")
    session.install(
        "Sphinx",
        "furo",
        "sphinx-argparse",
    )

    build_dir = Path("docs", "_build")
    if build_dir.exists():
        shutil.rmtree(build_dir)

    session.run("sphinx-build", *args)
