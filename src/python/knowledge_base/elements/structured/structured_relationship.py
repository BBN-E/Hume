from rdflib import URIRef, Literal, RDF, RDFS, XSD
from structured_namespaces import ns_lookup


# Defines event related classes - events can have any number of actors in any number of roles
class CausalRelation:

    def __init__(self, causal_id, causal_label, cause, effect, confidence,
                 causal_inference):
        self.causal_id = causal_id
        self.causal_label = causal_label
        self.cause = cause
        self.effect = effect
        self.confidence = confidence
        self.causal_inference = causal_inference

    def serialize(self, graph):

        if self.causal_label == "Similar":
            assertion = 'SimilarAssertion'
            cause = 'is_similar'
            effect = 'is_similar'
        elif self.causal_label == "Predictive":
            assertion = 'CausalAssertion'
            cause = 'has_cause'
            effect = 'has_effect'
        else:
            raise ValueError('Unexpected relationship type ' + self.causal_label)

        graph.add((ns_lookup['BBNTA1'][self.causal_id],
                   RDF.type, ns_lookup['CX'][assertion]))

        graph.add((ns_lookup['BBNTA1'][self.causal_id],
                   ns_lookup['CX'][cause],
                   ns_lookup['BBNTA1'][self.cause.factor_id]))
        self.cause.serialize(graph)

        graph.add((ns_lookup['BBNTA1'][self.causal_id],
                   ns_lookup['CX'][effect],
                   ns_lookup['BBNTA1'][self.effect.factor_id]))
        self.effect.serialize(graph)

        graph.add((ns_lookup['BBNTA1'][self.causal_id],
                   RDFS.label, Literal(self.causal_label, datatype=XSD.string)))

        graph.add((ns_lookup['BBNTA1'][self.causal_id],
                   ns_lookup['GCONCEPT']['numeric_confidence'],
                   get_likelihood_uri(self.confidence)))

        graph.add((ns_lookup['BBNTA1'][self.causal_id],
                   ns_lookup['DATAPROV']['generated_by'],
                   URIRef(self.causal_inference.inference_uri)))
        self.causal_inference.serialize(graph)


# Defines the factor in a causal relationship
class Factor:

    def __init__(self, factor_id, factor_label,
                 factor_property_id=None, factor_location=None, tab_ref=None):
        self.factor_id = factor_id
        self.factor_label = factor_label
        self.factor_property_id = factor_property_id
        self.factor_location = factor_location
        self.tab_ref = tab_ref

    def serialize(self, graph):
        graph.add((ns_lookup['BBNTA1'][self.factor_id],
                   RDF.type, ns_lookup['EVENT']['MeasurementFactor']))
        graph.add((ns_lookup['BBNTA1'][self.factor_id],
                   RDFS.label, Literal(self.factor_label, datatype=XSD.string)))

        if self.factor_property_id:
            graph.add((ns_lookup['BBNTA1'][self.factor_id],
                       ns_lookup['EVENT']['involves_reported_property'],
                       ns_lookup['BBNTA1'][self.factor_property_id]))

        if self.tab_ref:
            graph.add((ns_lookup['BBNTA1'][self.factor_id],
                       ns_lookup['DATAPROV']['sourced_from'],
                       ns_lookup['BBNTA1'][self.tab_ref.tab_ref_id]))

        if self.factor_location:
            graph.add((ns_lookup['BBNTA1'][self.factor_id],
                       ns_lookup['GCONCEPT']['located_at'],
                       self.factor_location))


# The provenance information about who extracted the event
class CausalInference:

    def __init__(self, inference_uri, time_completed):
        self.inference_uri = inference_uri
        self.time_completed = time_completed

    def serialize(self, graph):
        uri = URIRef(self.inference_uri)
        graph.add((uri, RDF.type, ns_lookup['DATAPROV']['InferenceActivity']))
        graph.add((uri, ns_lookup['DATAPROV']['time_completed'], Literal(self.time_completed, datatype=XSD.dateTime)))
        graph.add((uri, ns_lookup['DATAPROV']['performed_by'], ns_lookup['DATAPROV']['BBN']))


# Translates a human-readable likelihood value string into an XSD.decimal value
# likelihood_value (string): one of these possible values, all other values
# return 0.0:
#    "low" (returns 0.3), "medium" (returns 0.5), "high" (returns 0.7),
#    "certain" (returns 1.0)
# (per ODP changes in July 2018, intermediate ranks added and "high" lowered
# from 0.8)
def get_likelihood_uri(likelihood_value):
    categories = {'very low': 0.1, 'very low to low': 0.2, 'low': 0.3,
                  'low to medium': 0.4, 'medium': 0.5, 'medium to high': 0.6,
                  'high': 0.7, 'high to very high': 0.8, 'very high': 0.9,
                  'certain': 1.0}
    if likelihood_value in categories:
        likelihood_uri = Literal(categories[likelihood_value],
                                 datatype=XSD.decimal)
    else:
        likelihood_uri = Literal(0.0, datatype=XSD.decimal)

    return likelihood_uri
