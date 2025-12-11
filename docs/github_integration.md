# GitHub Integration

This document outlines the plan for integrating the RPM-EE project with GitHub.

## Repository

The project will be hosted on GitHub, with the following structure:

-   **main**: The main development branch.
-   **releases**: Tags for each versioned release.

## Issues and Roadmap

-   **Issues**: GitHub Issues will be used to track bugs and feature requests, mirroring the `issues.md` file.
-   **Roadmap**: GitHub Projects will be used to visualize the roadmap, mirroring the `roadmap.md` file.

## Automation

A GitHub Action will be created to automatically generate a changelog from commit messages and create a new release when a new tag is pushed.
