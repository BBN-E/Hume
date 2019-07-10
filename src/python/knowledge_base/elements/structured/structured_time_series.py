from rdflib import Literal, RDF, RDFS, XSD, URIRef
from structured_namespaces import ns_lookup
from structured_reported_value import ReportedValue


# Defines time series class that contains a series of reported values
class TimeSeries:

    def __init__(self, time_series_id, time_series_property, time_series_label, location=None,
                 tab_ref=None):
        self.time_series_id = time_series_id
        self.time_series_property = time_series_property
        self.time_series_label = time_series_label
        self.location = location
        self.tab_ref = tab_ref
        self.optional_properties = dict()
        self.reported_values = []  # type: [ReportedValue]

    def add_property(self, rdf_predicate, rdf_object):
        self.optional_properties[rdf_predicate] = rdf_object

    def add_reported_value(self, reported_value):
        self.reported_values.append(reported_value)

    def serialize(self, graph):
        graph.add((ns_lookup['BBNTA1'][self.time_series_id],
                   RDF.type, ns_lookup['MEAS']['TimeSeries']))
        graph.add((ns_lookup['BBNTA1'][self.time_series_id],
                   RDFS.label, Literal(self.time_series_label, datatype=XSD.string)))
        # Adding link to property - when and where it was created it should have been given
        # a matching tab ref (which may or may not be the same as this time series' tab ref)
        graph.add((ns_lookup['BBNTA1'][self.time_series_id],
                   ns_lookup['MEAS']['defined_by'], ns_lookup['BBNTA1'][self.time_series_property.property_id]))

        self.time_series_property.serialize(graph)

        if self.location:  # now an EntityData
            # Adding reference to existing location - when/where identified/created it should have been given
            # a matching tab ref (which may or may not be the same as this time series' tab ref)
            graph.add((self.location.get_uri(),
                       ns_lookup['MEAS']['has_time_series'],
                       ns_lookup['BBNTA1'][self.time_series_id]))
        if self.tab_ref:
            graph.add((ns_lookup['BBNTA1'][self.time_series_id],
                       ns_lookup['DATAPROV']['sourced_from'],
                       ns_lookup['BBNTA1'][self.tab_ref.tab_ref_id]))

        # Add any "extra" properties (e.g. measurement_unit, multiplier, etc)
        for rdf_predicate, rdf_object in self.optional_properties.items():
            graph.add((ns_lookup['BBNTA1'][self.time_series_id],
                       rdf_predicate,
                       rdf_object))

        # Serialize references to reported values
        for reported_value in self.reported_values:
            graph.add((ns_lookup['BBNTA1'][self.time_series_id],
                       ns_lookup['MEAS']['has_reported_value'],
                       ns_lookup['BBNTA1'][reported_value.reported_value_id]))
            # Serialize the reported value
            reported_value.serialize(graph)
