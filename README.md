<h1 align="center">
  <p align="center">Encord Python API Client</p>
  <a href="https://encord.com">
    <img src="./docs/_static/logo.svg" width="100" alt="Cord logo"/>
  </a>
</h1>

[![license](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

# The data engine for computer vision

## 💻 Features

- Minimal low-level Python client that allows you to interact with Encord's API
- Supports Python: `3.8`, `3.9`, `3.10` and `3.11`

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

Then, generate an public-private key pair, and upload the public key to [Encord website](https://www.encord.com/).
Detailed guide can be found in the [dedicated manual](https://docs.encord.com/docs/annotate-public-keys).

Passing the private key to the factory, you can initialise the Encord client directly.

```python
from encord import EncordUserClient

user_client = EncordUserClient.create_with_ssh_private_key(
    "<your_private_key_content>",
    password="<your_private_key_password_if_set_on_key_generation>",
)
```

Once you have instantiated an Encord client, it is easy to fetch a project information and start
working with the platform.

```py
project = user_client.get_project("<project_hash>")
label_rows = project.list_label_rows_v2()
```

For detailed examples and API reference please refer to [Encord SDK documentation](https://python.docs.encord.com/)

## 🐛 Troubleshooting

Please report bugs to the [GitHub Issues](https://github.com/encord-team/encord-client-python/issues).
Just make sure you read the [Encord documentation](https://docs.encord.com) and search for related issues first.
