from rdflib import Literal, RDF, RDFS, XSD, URIRef
from structured_namespaces import ns_lookup


# Defines time series class that contains a series of reported values
class EntityData:

    def __init__(self, entity_id, is_country=False, label=None,
                 mar_entity_type=None, entity_type=None):
        self.entity_id = entity_id
        self.reported_values = []
        self.is_country = is_country
        self.label = label
        self.entity_type = entity_type
        # TODO remove this hack of a hack
        self.mar_entity_type = mar_entity_type
        # todo populate with e.g. entity's country for use in grounder
        self.properties = {}
        # self.internal_ontology_class = None
        self.external_ontology_sources = []
        self.grounded_individuals = {}  # keys are internal types' names from external_ontology_sources

    def get_uri(self):
        if self.is_country:
            return ns_lookup["CAMEOCC"][self.entity_id]
        else:
            return ns_lookup["BBNTA1"][self.entity_id]

    def add_reported_value(self, reported_value):
        self.reported_values.append(reported_value)

    def serialize(self, graph):

        # Serialize references to reported values
        for reported_value in self.reported_values:
            graph.add((self.get_uri(),
                       ns_lookup['MEAS']['has_reported_value'],
                       ns_lookup['BBNTA1'][reported_value.reported_value_id]))
            # Serialize the reported value
            reported_value.serialize(graph)

        if self.external_ontology_sources:
            print('---')
            print(self.entity_id, "with label `", self.label, \
                "` was provided with type", self.entity_type)
            for (_, source), similarity in self.external_ontology_sources:
                print(similarity, ':', source)
            print('---')
            best_source = self.external_ontology_sources[0][0][1]
            graph.add((self.get_uri(),
                       RDF.type,
                       URIRef(best_source)))
