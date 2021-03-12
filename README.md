<h1 align="center">
  <p align="center">Cord Python API Client</p>
  <a href="https://cord.tech"><img src="https://app.cord.tech/CordLogo.svg" width="150" alt="Cord logo"/></a>
</h1>

[![license](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

***Where the world creates and manages training data***

## 💻 Features

- Minimal low-level Python client that allows you to interact with Cord's API
- Supports Python: `3.6`, `3.7`, and `3.8`

## ✨ Relevant Links
* [Cord website](https://cord.tech)
* [Cord web app](https://app.cord.tech)
* [Cord documentation](https://docs.cord.tech)

## 💡 Getting Started

For full documentation, visit [Cord Python API Client](https://docs.cord.tech/docs/client/).

First, install Cord Python API Client using the [pip](https://pip.pypa.io/en/stable/installing) package manager:

```bash
pip install cord-client-python
```

Then, create an API key for authentication via the [Cord web app](https://app.cord.tech). Pass the project ID and API key as environment variables or pass them explicitly when you initialise the CordClient object.

```bash
export CORD_PROJECT_ID="<project_id>"
export CORD_API_KEY="<project_api_key>"
```

Passing the project ID and API key as environment variables, you can initialise the Cord client directly.

```python
from cord.client import CordClient

client = CordClient.initialise()
```

If you want to avoid setting environment variables, you can initialise the Cord client by passing the project ID and API key as strings.

```python
from cord.client import CordClient

client = CordClient.initialise("<project_id>", "<project_api_key>")
```

If you wish to instantiate several client objects and avoid passing parameters each time, you can instantiate a CordConfig object, pass the project ID and API key as strings, and initialise the client with the config object.

```py
from cord.client import CordClient
from cord.client import CordConfig

config = CordConfig("<project_id>", "<project_api_key>")
client = CordClient.initialise_with_config(config)
```

Once you have instantiated a Cord client, it is easy to fetch information associated with the given project ID.

```py
from cord.client import CordClient

client = CordClient.initialise()
project = client.get_project()
```

## 🐛 Troubleshooting

Please report bugs to [GitHub Issues](https://github.com/cord-team/cord-client-python/issues). Just make sure you read the [Cord documentation](https://docs.cord.tech) and search for related issues first.
