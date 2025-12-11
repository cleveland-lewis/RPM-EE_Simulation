# Contributing to RPM-EE

First off, thank you for considering contributing to RPM-EE. It's people like you that make RPM-EE such a great tool.

## Where do I go from here?

If you've noticed a bug or have a feature request, make one! It's generally best if you get a feel for the codebase before contributing your first pull request.

## Fork & create a branch

If this is something you think you can fix, then fork RPM-EE and create a branch with a descriptive name.

A good branch name would be (where issue #38 is the ticket you're working on):

```bash
git checkout -b 38-add-feature-x
```

## Get the test suite running

Make sure you're running the test suite locally before you start making changes.

```bash
pytest
```

## Implement your fix or feature

At this point, you're ready to make your changes! Feel free to ask for help; everyone is a beginner at first 😸

## Make a Pull Request

At this point, you should switch back to your main branch and make sure it's up to date with RPM-EE's main branch.

```bash
git remote add upstream git@github.com:RPM-EE/RPM-EE.git
git checkout main
git pull upstream main
```

Then update your feature branch from your local copy of main, and push it!

```bash
git checkout 38-add-feature-x
git rebase main
git push --force-with-lease origin 38-add-feature-x
```

Finally, go to GitHub and make a Pull Request.
