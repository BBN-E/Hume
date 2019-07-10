from rdflib import Literal, RDF, RDFS, XSD, URIRef
from structured_namespaces import ns_lookup
from structured_events import Event


# Document related classes:
# Document/spreadsheet -> worksheet -> tabref
# Children require pointers back up tabref -> worksheet -> spreadsheet
class StructuredDocument:

    def __init__(self, file_id, triple_metadata=None):
        self.file_id = file_id
        self.meta_data = triple_metadata
        self.sheets = []

    def add_sheet(self, worksheet):
        worksheet.structured_document = self
        self.sheets.append(worksheet)

    def serialize(self, graph):


        print 'serializing', self.file_id




        doc_uri = URIRef('http://graph.causeex.com/bbn#' + self.file_id)

        graph.add((doc_uri,
                   RDF.type, ns_lookup['DATAPROV']['Document']))

        if self.meta_data:
            graph.parse(data=self.meta_data, format='nt')

        for sheet in self.sheets:
            graph.add((doc_uri,
                       ns_lookup['DATAPROV']['contains'],
                       ns_lookup['BBNTA1'][sheet.sheet_id]))
            sheet.serialize(graph)


# Worksheets contain the information we extract
# TabRefs will be serialized as they are sourced by individual events/entities
class Worksheet:

    def __init__(self, sheet_id):
        self.sheet_id = sheet_id
        self.tab_refs = []
        self.events = []  # type: [Event]
        self.time_series = []
        self.entities = []
        self.relations = []

    def add_tab_ref(self, tab_ref):
        tab_ref.worksheet = self
        self.tab_refs.append(tab_ref)

    def add_event(self, event):
        """
        :type event: Event
        """
        self.events.append(event)

    def add_entity(self, entity):
        self.entities.append(entity)

    def add_time_series(self, time_series):
        self.time_series.append(time_series)

    def add_relation(self, relation):
        self.relations.append(relation)

    def serialize(self, graph):


        print 'serializing', self.sheet_id
        print 'with {} tabs, '.format(len(self.tab_refs)) + \
              '{} timeseries, '.format(len(self.time_series)) +  \
              '{} events, '.format(len(self.events)) +  \
              '{} entities, '.format(len(self.entities)) +  \
              '{} relations'.format(len(self.relations))



        graph.add((ns_lookup['BBNTA1'][self.sheet_id],
                   RDF.type, ns_lookup['DATAPROV']['Worksheet']))
        for tab_ref in self.tab_refs:
            graph.add((ns_lookup['BBNTA1'][self.sheet_id],
                       ns_lookup['DATAPROV']['contains'], ns_lookup['BBNTA1'][tab_ref.tab_ref_id]))
            tab_ref.serialize(graph)
        for event in self.events:
            event.serialize(graph)
        for time_series in self.time_series:
            time_series.serialize(graph)
        for entity in self.entities:
            entity.serialize(graph)
        for relation in self.relations:
            relation.serialize(graph)


class TabRef:

    def __init__(self, tab_ref_id, col_num=None, row_num=None):
        self.tab_ref_id = tab_ref_id
        self.col_num = col_num
        self.row_num = row_num

    def serialize(self, graph):
        graph.add((ns_lookup['BBNTA1'][self.tab_ref_id],
                   RDF.type, ns_lookup['DATAPROV']['TabularReference']))

        # Want to output values that are 0
        if isinstance(self.col_num, int):
            graph.add((ns_lookup['BBNTA1'][self.tab_ref_id],
                       ns_lookup['DATAPROV']['line_number'], Literal(self.row_num, datatype=XSD.int)))
        if isinstance(self.row_num, int):
            graph.add((ns_lookup['BBNTA1'][self.tab_ref_id],
                       ns_lookup['DATAPROV']['column_ref'], Literal(self.col_num, datatype=XSD.int)))
