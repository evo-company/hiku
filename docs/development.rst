Development
===========

Tools
~~~~~

We use `lets <https://lets-cli.org/>`_ to run project tests, build docs and so on.


Changelog
~~~~~~~~~

When developing, add notes to `0.x.xrcX` section.

For example if we current version is `0.7.1` and we are woring on `0.7.2`
we should create section `0.7.2rcX`.

After we decided to release new version, we must rename `0.7.2rcX` to `0.7.2`.


Release process
~~~~~~~~~~~~~~~

Hiku supports semver versioning.

#. Update the version number in the `hiku/__init__.py`` file.
#. Update the changelog in the `docs/changelog/changes_0X.rst` file.
#. Merge changes into master.
#. Create annotated tag. This will trigger a new release action on GitHub and publish new package to `pypi`.