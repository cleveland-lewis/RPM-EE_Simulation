# Slow Tests and Workarounds

This document provides guidance on managing slow tests in the RPM-EE test suite.

## Marking Slow Tests

Slow tests should be marked with the `@pytest.mark.slow` decorator.

```python
import pytest

@pytest.mark.slow
def test_that_is_slow():
    # ...
```

## Running Tests

To run all tests except the slow ones:

```bash
pytest -m "not slow"
```

To run only the slow tests:

```bash
pytest -m slow
```

## CI Configuration

The CI should be configured to run only the fast tests by default. Slow tests should be run on a separate, less frequent schedule (e.g., nightly).
