<h1 align="center">
  <p align="center">Encord Python API Client</p>
  <a href="https://encord.com"><img src="./docs/_static/logo.svg" width="100" alt="Cord logo"/></a>
</h1>

[![license](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

***The data engine for computer vision***

## 💻 Features

- Minimal low-level Python client that allows you to interact with Encord's API
- Supports Python: `3.7`, `3.8`, `3.9`, and `3.10`

## ✨ Relevant Links
* [Encord website](https://encord.com)
* [Encord web app](https://app.encord.com)
* [Encord documentation](https://docs.encord.com)

## 💡 Getting Started

For full documentation, please visit [Encord Python SDK](https://python.docs.encord.com/).

First, install Encord Python API Client using the [pip](https://pip.pypa.io/en/stable/installing) package manager:

```bash
pip install encord
```

Then, create an API key for authentication via the [Encord web app](https://app.encord.com). Pass the resource ID and API key as environment variables or pass them explicitly when you initialise the EncordClient object.

```bash
export ENCORD_PROJECT_ID="<project_id>"
export ENCORD_API_KEY="<project_api_key>"
```

Passing the resource ID and API key as environment variables, you can initialise the Encord client directly.

```python
from encord.client import EncordClient

client = EncordClient.initialise()
```

If you want to avoid setting environment variables, you can initialise the Encord client by passing the resource ID and API key as strings.

```python
from encord.client import EncordClient

client = EncordClient.initialise("<resource_id>", "<resource_api_key>")
```

If you wish to instantiate several client objects and avoid passing parameters each time, you can instantiate a EncordConfig object, pass the resource ID and API key as strings, and initialise the client with the config object.

```py
from encord.client import EncordClient
from encord.client import EncordConfig

config = EncordConfig("<resource_id>", "<resource_api_key>")
client = EncordClient.initialise_with_config(config)
```

Once you have instantiated an Encord client, it is easy to fetch information associated with the given resource ID.

```py
from encord.client import EncordClient

client = EncordClient.initialise()
project = client.get_project()
```

## 🐛 Troubleshooting

Please report bugs to [GitHub Issues](https://github.com/encord-team/encord-client-python/issues). Just make sure you read the [Encord documentation](https://docs.encord.com) and search for related issues first.
