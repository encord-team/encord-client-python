# Instructions around using Sphinx
Simply build with
* `make html` from within the `docs` directory.
* You can open the `_build/html/index.html` page to inspect your changes.

If you are adding a new module which should be documented, follow the examples within `api.rst` to add this new module.

Whenever you add a new public class or function, this documentation should be rebuild and uploaded to the server.

## Hosting
Bake this delicious recipe and share the docs publicly with your friends with these easy steps.

### Ingredients
* Make sure you have the `firebase` CLI installed and have run `firebase login` before.
* Make sure you have access to the [firebase cord-docs](https://console.firebase.google.com/u/0/project/cord-docs/overview). If you don't, Rad can help you.

### Cooking instructions
1) Pre-heat the oven and build your project with `make html` from the `docs` directory
2) Run `firebase deploy --only hosting:python-docs` to publish them online.
3) Visit the [firebase hosting site](https://console.firebase.google.com/u/0/project/cord-docs/hosting/sites/python-docs), check out the public docs domain and double check if everything is to your taste.
4) Share the docs with your friends who are most hungry for knowledge! 
