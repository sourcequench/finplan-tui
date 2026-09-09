# Contributing

Keep this project provider-neutral. Do not add personal accounts, real
financial exports, credentials, private database adapters, or household
defaults. Use synthetic fixtures for examples and tests.

Run the checks before submitting a change:

```sh
python -m py_compile app.py core_adapter.py models.py repository.py
ruff format --check .
ruff check .
pytest -q
```

Changes to the repository protocol or public models should include an update
to the README and a test covering the compatibility impact.
