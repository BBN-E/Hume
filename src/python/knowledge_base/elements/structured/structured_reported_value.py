from rdflib import Literal, RDF, XSD, URIRef
from structured_namespaces import ns_lookup


# Defines event related classes - events can have any number of actors in any number of roles
class ReportedValue:

    def __init__(self, reported_value_id, reported_value, start_time=None, end_time=None,
                 tab_ref=None, related_property=None):
        self.reported_value_id = reported_value_id
        self.reported_value = reported_value
        self.start_time = start_time
        self.end_time = end_time
        self.tab_ref = tab_ref
        self.related_property = related_property
        self.optional_properties = dict()

    def add_property(self, rdf_predicate, rdf_object):
        self.optional_properties[rdf_predicate] = rdf_object

    def serialize(self, graph):
        graph.add((ns_lookup['BBNTA1'][self.reported_value_id],
                   RDF.type, ns_lookup['MEAS']['ReportedValue']))
        graph.add((ns_lookup['BBNTA1'][self.reported_value_id],
                   ns_lookup['MEAS']['numeric_value'],
                   Literal(format(self.reported_value, '0.2f'), datatype=XSD.double)))

        if self.related_property:
            # Adding link to property - when and where it was created it should have been given
            # a matching tab ref (which may or may not be the same as this time series' tab ref)
            graph.add((ns_lookup['BBNTA1'][self.reported_value_id],
                       ns_lookup['MEAS']['defined_by'], ns_lookup['BBNTA1'][self.related_property.property_id]))
            self.related_property.serialize(graph)

        if self.start_time:
            graph.add((ns_lookup['BBNTA1'][self.reported_value_id],
                       ns_lookup['GCONCEPT']['earliest_possible_start_time'],
                       Literal(self.start_time, datatype=XSD.dateTime)))
        if self.end_time:
            graph.add((ns_lookup['BBNTA1'][self.reported_value_id],
                       ns_lookup['GCONCEPT']['earliest_possible_end_time'],
                       Literal(self.end_time, datatype=XSD.dateTime)))

        if self.tab_ref:
            graph.add((ns_lookup['BBNTA1'][self.reported_value_id],
                       ns_lookup['DATAPROV']['sourced_from'],
                       ns_lookup['BBNTA1'][self.tab_ref.tab_ref_id]))

        # Add any "extra" properties (e.g. measurement_unit, multiplier, etc)
        for rdf_predicate, rdf_object in self.optional_properties.items():
            graph.add((ns_lookup['BBNTA1'][self.reported_value_id],
                       rdf_predicate,
                       rdf_object))
