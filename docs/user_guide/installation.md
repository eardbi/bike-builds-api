If you want to use this library, add this package to your `pyproject.toml` file:

```toml
[tool.poetry.dependencies]
bike-builds-api = "<replace with your version requirement>"

[[tool.poetry.source]]
name = "nexus"
url = "http://10.1.5.124/repository/pypi-axe/simple"
priority = "supplemental"
```

When you use `pip` to install this package, you need to add the following option:

```bash
pip install bike-builds-api --extra-index-url http://10.1.5.124/repository/pypi-axe/simple --trusted-host 10.1.5.124
```

