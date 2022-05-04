# Instructions around using Sphinx
Simply build with
* `make html` from within the `docs` directory.
* You can open the `_build/html/index.html` page to inspect your changes.

If you are adding a new module which should be documented, follow the examples within `api.rst` to add this new module.

Whenever you add a new public class or function, this documentation should be rebuild and uploaded to the server.

## Common Doc-writing-patterns
1. To keep terminology consistent, we have defined multiple substitutes for common entities in `source/substitutes.rst`. 
    You should familiarise your self with them.
    For example, instead of writing "Encord SDK" repeatedly, we have defined the substitute `|product|` which will be substituted for "Encord SDK" at build time.
2. To avoid having hardcoded links all over the place, we keep links in the `source/links.json` file. To insert a link, use ``:xref:`link_key` ``. 
   For example, in the `links.json` file, the following entry exists:
    ```json
    "create_project_on_platform": {
        "user_text": "Create Project on Platform",
        "url": "https://docs.encord.com/docs/projects/new-project"
    }
    ```
    Using ``:xref:`create_project_on_platform` `` will be transformed into [Create Project on Platform](https://docs.encord.com/docs/projects/new-project) at built time.  
    __NB:__ There is a script that allows you to easily add a link to the json form the
    commandline. Simply run `./add_link` and it will query the necessary information and
    (naively) check for duplicates.
3. We have included the `sphinx_tabs` [module](https://github.com/executablebooks/sphinx-tabs), which, e.g., allows you to have both a code tab and an output tab. See, e.g., `source/quickstart.rst`.
4. As demonstrated in the `source/quickstart.rst`, you can include code from files. 
    With python files (in `source/code_examples`), we try to keep them "blacked" with an enforced 60 column linewidth (to avoid horizontally scrolling code examples).
    To black all code examples, you can run `> black source/code_examples/**/*.py --line-length 60`.
5. We use the [sphinx-codeautolink](https://sphinx-codeautolink.readthedocs.io/en/latest/index.html)
    extension to allow clicking directly in code examples to get to the auto-generated doc.
    If you want to make the extension recognize instances across code blocks on a page, you can use the `autolink-concat` feature.
    You can also use the `autolink-preface` feature to "invisibly" instantiate objects in a preface.
    For an example, have a look at `source/tutorials/datasets/adding_data_to_datasets.rst`.

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
