Contributor Guide
=================
Thank you for your interest in improving this project. This project is
open-source under the `Apache-2.0 license`_ and welcomes contributions in the
form of bug reports, feature requests, and pull requests.

Here is a list of important resources for contributors:

- `Source Code`_
- `Documentation`_
- `Issue Tracker`_

.. _Apache-2.0 license: https://opensource.org/licenses/Apache-2.0
.. _Source Code: https://github.com/NicolasT/gptsum
.. _Documentation: https://nicolast.github.io/gptsum
.. _Issue Tracker: https://github.com/NicolasT/gptsum/issues

How to report a bug
-------------------
Report bugs on the `Issue Tracker`_. When filing an issue, make sure to answer
the following questions:

- Which operating system and Python version are you using?
- Which version of this project are you using?
- What did you do?
- What did you expect to see?
- What did you see instead?

The best way to get your bug fixed is to provide a test case, and/or steps to
reproduce the issue.

How to request a feature
------------------------
Request features on the `Issue Tracker`_.

How to set up your development environment
------------------------------------------
You need Python 3.9+ and the following tools:

- Poetry_
- Nox_
- nox-poetry_

Install the package with development requirements:

.. code:: console

   $ poetry install

You can now run an interactive Python session,
or the command-line interface:

.. code:: console

   $ poetry run python
   $ poetry run gptsum

.. _Poetry: https://python-poetry.org/
.. _Nox: https://nox.thea.codes/
.. _nox-poetry: https://nox-poetry.readthedocs.io/

How to test the project
-----------------------
Run the full test suite:

.. code:: console

   $ nox

List the available Nox sessions:

.. code:: console

   $ nox --list-sessions

You can also run a specific Nox session.
For example, invoke the unit test suite like this:

.. code:: console

   $ nox --session=tests

Unit tests are located in the ``tests`` directory, and are written using the
pytest_ testing framework.

.. _pytest: https://pytest.readthedocs.io/

How to submit changes
---------------------
Open a `pull request`_ to submit changes to this project. Your pull request
needs to meet the following guidelines for acceptance:

- The Nox test suite must pass without errors and warnings.
- Include unit tests. This project maintains 100% code coverage.
- If your changes add functionality, update the documentation accordingly.

Feel free to submit early, though—we can always iterate on this.

To run linting and code formatting checks before commiting your change, you can
run ``flake8``:

.. code:: console

   $ poetry run flake8 src/ tests/

It is recommended to open an issue before starting work on anything. This will
allow a chance to talk it over and validate your approach.

.. _pull request: https://github.com/NicolasT/gptsum/pulls
