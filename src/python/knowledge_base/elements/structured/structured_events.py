from collections import defaultdict
from structured_namespaces import ns_lookup
from rdflib import Literal, RDF, RDFS, XSD, URIRef
from structured_entity import EntityData


# Defines event related classes - events can have any number of actors in any number of roles
class Event:

    def __init__(self, event_id, event_type, event_label, event_location=None,
                 start_time=None, end_time=None, tab_ref=None):
        self.event_id = event_id
        self.event_type = event_type
        self.event_label = event_label
        self.event_location = event_location  # type: EntityData
        self.start_time = start_time
        self.end_time = end_time
        self.tab_ref = tab_ref
        self.actors = defaultdict(list)

    def add_actor(self, role, actor):
        self.actors[role].append(actor)

    def serialize(self, graph):
        graph.add((ns_lookup['BBNTA1'][self.event_id],
                   RDF.type, URIRef(self.event_type)))
        graph.add((ns_lookup['BBNTA1'][self.event_id],
                   RDFS.label, Literal(self.event_label, datatype=XSD.string)))

        if self.event_location:  # now an EntityData
            # Adding reference to existing location - when/where identified it should have been given
            # a matching tab ref (which may or may not be the same as this extracted event)
            graph.add((ns_lookup['BBNTA1'][self.event_id],
                       ns_lookup['GCONCEPT']['located_at'],
                       self.event_location.get_uri()))

            # todo self.event_location.serialize(graph)?

        if self.tab_ref:
            graph.add((ns_lookup['BBNTA1'][self.event_id],
                       ns_lookup['DATAPROV']['sourced_from'],
                       ns_lookup['BBNTA1'][self.tab_ref.tab_ref_id]))
        if self.start_time:
            graph.add((ns_lookup['BBNTA1'][self.event_id],
                       ns_lookup['GCONCEPT']['earliest_possible_start_time'],
                       Literal(self.start_time, datatype=XSD.dateTime)))
        if self.end_time:
            graph.add((ns_lookup['BBNTA1'][self.event_id],
                       ns_lookup['GCONCEPT']['earliest_possible_end_time'],
                       Literal(self.end_time, datatype=XSD.dateTime)))

        #serialize actors
        for actor_role, actor_list in self.actors.items():
            for actor in actor_list:
                graph.add((ns_lookup['BBNTA1'][self.event_id],
                           URIRef(actor_role),
                           ns_lookup['BBNTA1'][actor.actor_id]))
                actor.serialize(graph)


class Actor:

    def __init__(self, actor_id, actor_type, label, tab_ref=None):
        self.actor_id = actor_id
        self.actor_type = actor_type
        self.label = label
        self.tab_ref = tab_ref

    def serialize(self, graph):
        graph.add((ns_lookup['BBNTA1'][self.actor_id],
                   RDF.type, URIRef(self.actor_type)))
        graph.add((ns_lookup['BBNTA1'][self.actor_id],
                   RDFS.label, Literal(self.label, datatype=XSD.string)))

        if self.tab_ref:
            graph.add((ns_lookup['BBNTA1'][self.actor_id],
                       ns_lookup['DATAPROV']['sourced_from'], ns_lookup['BBNTA1'][self.tab_ref.tab_ref_id]))
            # Note - not serializing tab ref here (since it was done as part of document serialization)
