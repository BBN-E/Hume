from rdflib import URIRef, Literal, RDF, RDFS, XSD
from structured_namespaces import ns_lookup


# Defines event related classes - events can have any number of actors in any number of roles
class Property:

    def __init__(self, property_id, property_type, property_label, tab_ref=None):
        self.property_id = property_id
        self.property_type = property_type
        self.property_label = property_label
        self.tab_ref = tab_ref
        self.optional_properties = dict()
        # self.internal_ontology_class = None  # points to OntologyClass
        self.external_ontology_sources = []
        self.event_hierarchy_grounding = []

    def add_property(self, rdf_predicate, rdf_object):
        self.optional_properties[rdf_predicate] = rdf_object

    def serialize(self, graph):

        if self.external_ontology_sources:
            print('---')
            print(self.property_id, "with label `", self.property_label, \
                "` was provided with type", self.property_type)
            for (_, source), similarity in self.external_ontology_sources:
                print(similarity, ':', source)
            print('---')
            best_source = self.external_ontology_sources[0][0][1]
            graph.add((ns_lookup['BBNTA1'][self.property_id],
                       RDF.type, URIRef(best_source)))
        else:
            graph.add((ns_lookup['BBNTA1'][self.property_id],
                       RDF.type, URIRef(self.property_type)))

        # TODO: Fix this hack
        if self.property_label == "nan" or self.property_label == "NaN":
            self.property_label = "unspecified"

        graph.add((ns_lookup['BBNTA1'][self.property_id],
                   RDFS.label, Literal(self.property_label, datatype=XSD.string)))

        if self.tab_ref:
            graph.add((ns_lookup['BBNTA1'][self.property_id],
                       ns_lookup['DATAPROV']['sourced_from'],
                       ns_lookup['BBNTA1'][self.tab_ref.tab_ref_id]))

        # Add any "extra" properties (e.g. has_property_type, is_about, etc.)
        for rdf_predicate, rdf_object in self.optional_properties.items():
            graph.add((ns_lookup['BBNTA1'][self.property_id],
                       rdf_predicate,
                       rdf_object))
