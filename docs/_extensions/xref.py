# A modification of code from https://github.com/michaeljones/sphinx-xref
from docutils import nodes
from sphinx.util import caption_ref_re


def xref(typ, rawtext, text, lineno, inliner, options={}, content=[]):
    title = target = text
    brace = text.find("<")
    if brace != -1:
        m = caption_ref_re.match(text)
        if m:
            target = m.group(2)
            title = m.group(1)
        else:
            # fallback: everything after '<' is the target
            target = text[brace + 1 :]
            title = text[:brace]

    link = xref.links[target]
    if brace != -1:
        pnode = nodes.reference(target, title, refuri=link["url"])
    else:
        pnode = nodes.reference(target, link["user_text"], refuri=link["url"])

    return [pnode], []


def get_refs(app):
    xref.links = app.config.xref_links


def setup(app):
    app.add_config_value("xref_links", {}, True)
    app.add_role("xref", xref)
    app.connect("builder-inited", get_refs)
