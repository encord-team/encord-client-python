from encord.http.querier import Querier


class LabelRowMetadata:
    pass


class LabelRowMetadataWithClientMetadataSignedUrl(LabelRowMetadata):
    pass


def test_route_defaults_to_response_type_class_name():
    assert Querier._route(LabelRowMetadata) == "labelrowmetadata"


def test_route_override_takes_precedence():
    # Parse into the subclass, but route to the base handler.
    assert Querier._route(LabelRowMetadataWithClientMetadataSignedUrl, LabelRowMetadata) == "labelrowmetadata"


def test_route_without_override_uses_subclass_name():
    assert Querier._route(LabelRowMetadataWithClientMetadataSignedUrl) == "labelrowmetadatawithclientmetadatasignedurl"


def test_route_override_can_be_an_unrelated_class():
    class SomethingElse:
        pass

    assert Querier._route(LabelRowMetadata, SomethingElse) == "somethingelse"
