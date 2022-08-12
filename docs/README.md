# Instructions around using Sphinx

To build the documentation, follow these steps:

1. Navigate to the root of the repo and run 
```shell
> poetry install
```
2. Activate the poetry environment
```shell
> poetry shell
```
3. Navigate back to this directory (`docs`) and run
```shell
> make html
```
4. You can open the `_build/html/index.html` page to inspect your changes.

### For those writing docs:
Instead of `make html`, you can run
```shell
> ./build_docs
```
This will run `black`, `isort`, and `make html` with appropriate configurations. 


If you are adding a new module which should be documented, follow the examples within `api.rst` to add this new module.

Whenever you add a new public class or function, this documentation should be rebuild and uploaded to the server.

## Common Doc-writing-patterns
1. To keep terminology consistent, we have defined multiple substitutes for common entities in `source/substitutes.rst`. 
    You should familiarise your self with them.
    For example, instead of writing "Encord SDK" repeatedly, we have defined the substitute `|sdk|` which will be substituted for "Encord SDK" at build time.
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

## Other tricks
1. To be able to run a spell checker like Grammarly on the docs, you can build a `txt` version of the documentation by running the command
   ```shell
   > sphinx-build -b text source _text
   ```
   This will build the docs in a separate `_text` directory from which you can copy the content of text files to, e.g., Grammarly.
   

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

# TODOs / potential improvements
- [ ] For "Pardon our dust"-sections, we could add links to (to-be-removed) docs from the web-app documentation until they are updated.
- [ ] Datasets, Projects, Label rows, etc. are not written consistently (caps or not) across the documentation. Consider using substitutes for this.
- [ ] There may be some remaining `resource_id` examples left, which are confusing because in most contexts, the `resource_id` can only be one of, e.g., a `project_hash` or `dataset_hash`. We should be specific when possible.
- [ ] As we use Black which generally uses `line-length` 88 (88 columns code), the code in the auto-docs sometimes looks ugly. 
      See, e.g., [the docs for `get_datasets`](python.docs.encord.com/user_client.html#EncordUserClient.get_datasets).
      It seems like there is a [css fix](https://github.com/sphinx-doc/sphinx/issues/3092#issuecomment-258922773) to this issue.
      A fix is commented out in the `_static/css/custom.css` file because it seems that black currently still allows longer lines than, e.g., 88 columns.
- [ ] We should have one complete code example for each tutorial subsection where all the stuff possible is done in one example. 
      That way, developers can just copy this file instead of stitching all the tiny examples. 

# Inconsistencies/potential confusions in our code
I (FHV) have tried to take notes of inconsistencies in the code base that may be sources of confusion:

1. `EncordUserClient.get_or_create_dataset_api_key` returns an `encord.orm.dataset.DatasetAPIKey` but `EncordUserClient.get_or_create_project_api_key` just returns the key as a string. 
2. Access scopes for API keys are defined in different places for projects and datasets.
   The project api keys have access scopes defined in `encord.utilities.client_utilities.APIKeyScopes` but dataset api keys have scopes defined in `encord.orm.dataset.DatasetScope` this makes no sense. 
3. The `encord.orm.dataset.DatasetInfo` has the attribute `type` which is an int, but one uses the `encord.orm.dataset.StorageLocation` when creating a dataset. I see no reason why the DatasetInfo wouldn't present the type as a `StorageLocation` such that users don't need to guess what, e.g.,  type `0` means.
4. FHV: It seems weird to me that the logic for converting ontology classifications and ontology objects to dictionaries is located in the `encord.project_ontology.ontology.py` file and not in the `encord.project_ontology.ontology_classification.py` class.  
   Also, there is a lot of custom logic for doing so, when the `dataclasses.asdict` with a custom factory could do the same thing with much less code.
   Note, I have a local `fhv/ontology_parsing` branch which does it with `asdict` but probably not perfectly structured either.
5. FHV: Why is the `ObjectShape` definitions in the file `encord.project_ontology.object_type`? It makes no sense that both are not called either `object_type` or `object_shape`.
   For classifications, they are both called `ClassificationType`.
6. FHV: When fetching projects through the `EncordUserClient`, the return type is a list of dictionaries with key `project` and value `encord.orm.project.Project` value.
   The `Project` orm has properties apart from properties like `title`, `description`, and `project_hash`, which work fine for the particular call, the `Project` definition also has properties `label_rows` and `editor_ontology`, which are not populated in the mentioned call.
   Even worse, when calling `project.label_rows`, a `KeyError` is thrown.
7. We are super inconsistent with the use of `uid`, `project_hash`, etc. 
   I think that we should be as specific as possible. 
   There is no point in abstracting away the distinction. We just make everything more confusing that way.
   For example, `encord.orm.dataset.DataRow` uses `data_hash`  under the name `uid` which makes no sense.
8. Why does `project_client.get_label_row('<label_hash>')` not have a `data_hash` attribute in the response, similar to `project_client.get_project().label_rows[0]`?
   When wanting to run OCR stuff, you need the `data_hash` but can only obtain it from that one place.
9. There is no way to be 100% sure that the results from the `dataset_client.run_ocr` corresponds to specific data_units in the label row.


# Known issues
1. The scrollspy (right-side toc) highlights the previous item when clicking a link. This is apparently a [bootstrap issue](https://github.com/twbs/bootstrap/issues/32496). 
