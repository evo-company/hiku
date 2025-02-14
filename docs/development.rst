Development
===========

Tools
~~~~~

- ``pdm`` package manager - https://pdm.fming.dev/
- ``lets`` task runner https://lets-cli.org to run project tests, build docs and so on.

Setup development
~~~~~~~~~~~~~~~~~

1. Install ``pdm`` package manager - https://pdm.fming.dev/
2. Run ``pdm sync`` to install dependencies

Run unit tests using pdm

.. code-block:: bash

    $ pdm run test

Run integration tests (with real postgress) using pdm.
Postgres in this case accessed via localhost.

.. code-block:: bash

    $ docker compose up -d postgres
    $ pdm run test-pg-local
    $ docker compose down

Or you can use lets task runner to run unit + integration tests (all-on-one) in docker

.. code-block:: bash

    $ lets test

Run linters, formatters and other checks

.. code-block:: bash

    $ pdm run flake
    $ pdm run black
    $ pdm run mypy

Or you can run ``pdm check`` - it will reformat code, run linters and test in one command.

Build docs
Docs will be available at ``docs/build``

.. code-block:: bash

    $ pdm run docs


Setup PDM with IDE
~~~~~~~~~~~~~~~~~~

PDM supports ``venv`` so in order to setup PDM with IDE you need to create a new virtual environment and point your IDE to it.

Run ``pdm sync``. It will create ``.venv`` directory with virtual environment.

Point your IDE to this virtual environment and you are good to go.

In PyCharm you can also mark some directories as excluded to speed up indexing and autocompletion, and to make search ignore venv.

#. Open PyCharm Settings -> Project Structure
#. Mark ``.venv`` as Excluded
#. Mark ``.venv/lib/<python_version>/site-packages`` both as `Excluded` (to exclude files from search) and `Sources` (to enable autocompletion)

Pdm also provides how-to guides on how to configure other IDE/editors https://pdm-project.org/latest/usage/venv/

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

#. Update the version number in the ``hiku/__init__.py`` file.
#. Update the changelog in the `docs/changelog/changes_0X.rst` file.
#. Merge changes into master.
#. Run `lets release <version> -m 'your release message'`. This will create and push annotated tag. When new tag pushed, new release action on GitHub will publish new package to `pypi`.

Documentation release
~~~~~~~~~~~~~~~~~~~~~

Documentation released on new commits in master.