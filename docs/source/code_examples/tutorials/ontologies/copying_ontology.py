ontology = user_client.get_ontology('<ontology_hash>')
new_ontology = user_client.create_ontology('copy ontology', description='my ontology description', structure=ontology.structure)