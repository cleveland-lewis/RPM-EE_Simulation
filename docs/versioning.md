# Versioning

This document defines the versioning scheme and process for the RPM-EE model.

## Scheme

We use [Semantic Versioning (SemVer)](https://semver.org/).

-   **MAJOR** version when you make incompatible API changes.
-   **MINOR** version when you add functionality in a backward-compatible manner.
-   **PATCH** version when you make backward-compatible bug fixes.

## Process

1.  A new version is created when a set of features or bug fixes is complete.
2.  The version number is updated in the `__init__.py` file.
3.  A git tag is created for the new version.
4.  A changelog entry is added to `CHANGELOG.md`.
