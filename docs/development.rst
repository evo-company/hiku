Development
===========

Tools
~~~~~

- ``uv`` package manager - https://docs.astral.sh/uv/
- ``lets`` task runner https://lets-cli.org to run project tests, build docs and so on.

Setup development
~~~~~~~~~~~~~~~~~

1. Install ``uv`` - https://docs.astral.sh/uv/getting-started/installation/
2. Run ``uv sync --group test`` to install the default development environment plus test tools

Run unit tests using uv

.. code-block:: bash

    $ uv run pytest tests

Run integration tests (with real postgres) using uv.
Postgres in this case accessed via localhost.

.. code-block:: bash

    $ docker compose up -d postgres
    $ uv run pytest tests_pg --pg-host=localhost
    $ docker compose down

Or you can use lets task runner to run unit + integration tests (all-on-one) in docker

.. code-block:: bash

    $ lets test

Run linters, formatters and other checks

.. code-block:: bash

    $ uv run flake8
    $ uv run black hiku examples
    $ uv run mypy

Build docs
Docs will be available at ``docs/build``

.. code-block:: bash

    $ uv run sphinx-build -b html docs docs/build


Setup uv with IDE
~~~~~~~~~~~~~~~~~

uv creates a project-local virtual environment in ``.venv``.

Run ``uv sync``. It will create the ``.venv`` directory with the virtual environment.

Point your IDE to this virtual environment and you are good to go.

In PyCharm you can also mark some directories as excluded to speed up indexing and autocompletion, and to make search ignore venv.

#. Open PyCharm Settings -> Project Structure
#. Mark ``.venv`` as Excluded
#. Mark ``.venv/lib/<python_version>/site-packages`` both as `Excluded` (to exclude files from search) and `Sources` (to enable autocompletion)

Integrate with ``pyright``
~~~~~~~~~~~~~~~~~~~~~~~~~~

Pyright is a static type checker for Python and is used many in ``VSCode`` and `` integrate it with your IDE.
Changelog
~~~~~~~~~

When developing, add notes to `0.x.xrcX` section.

For example if we current version is `0.7.1` and we are woring on `0.7.2`
we should create section `0.7.2rcX`.

After we decided to release new version, we must rename `0.7.2rcX` to `0.7.2`.


Release process
~~~~~~~~~~~~~~~

Hiku supports semver versioning.

#. Update the changelog in the `docs/changelog/changes_0X.rst` file.
#. Merge changes into master.
#. Run `lets release <version> -m 'your release message'`. This updates version in ``pyproject.toml``, creates and pushes an annotated tag. When the new tag is pushed, the release action on GitHub publishes the package to `pypi`.

.. note::

    ``lets release`` command will bump version automatically if you pass ``rc`` as a version.
    For example ``lets release rc -m 'your release message'`` will bump version to ``0.x.xrcX``.

Documentation release
~~~~~~~~~~~~~~~~~~~~~

Documentation released on new commits in master.
