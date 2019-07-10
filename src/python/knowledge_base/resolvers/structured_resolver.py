from __future__ import print_function
from knowledge_base import KnowledgeBase
from kb_resolver import KBResolver
from shared_id_manager.shared_id_manager import SharedIDManager
from elements.structured.structured_documents import StructuredDocument, Worksheet, TabRef
from elements.structured.structured_events import Actor, Event
from elements.structured.structured_time_series import TimeSeries
from elements.structured.structured_property import Property
from elements.structured.structured_reported_value import ReportedValue
from elements.structured.structured_entity import EntityData
from elements.structured.structured_relationship import CausalRelation, Factor, CausalInference
import ntpath
import io
import os
import json
from rdflib import Literal, Graph, XSD, URIRef
import math
from datetime import datetime
from urllib import quote_plus


class StructuredResolver(KBResolver):

    def __init__(self):
        super(StructuredResolver, self).__init__()

        self.id_manager = IDManager()

        # Load city name to entity group id mappings
        self.city_name_to_entity_group_id_mappings = dict()
        with io.open(os.path.dirname(os.path.realpath(__file__)) +
                     "/../data_files/" +
                     "nigerian_cities_entity_group_id_mappings.txt",
                     "r", encoding="utf8") as f:
            lines = [line.rstrip() for line in f.readlines()]
            for line in lines:
                parts = line.split("\t")
                city = parts[0].lower()
                # country = parts[1] # no need to read country, at least for now
                entity_group_id = parts[2]
                self.city_name_to_entity_group_id_mappings[
                    city] = entity_group_id

    def resolve(self, kb, parameter):
        print("Resolving KB with parameter: " + parameter)

        resolved_kb = KnowledgeBase()
        super(StructuredResolver, self).copy_all(resolved_kb, kb)

        # Load document to ID mappings
        # TODO: Need to determine what to do about zips
        # Structured JSON data contains the full name for the zip,
        # i.e. the "rel_path":
        # "World_Bank_Data\API_BEN_DS2_en_csv_v2.zip\API_BEN_DS2_en_csv_v2.csv"
        # but the current ID data file only goes to the zip filename
        # TODO: is this now outdated based on file ids in json to be processed?

        with io.open(os.path.dirname(os.path.realpath(__file__)) +
                     "/../data_files/structured_data_unique_ids.txt",
                     mode="r", encoding="utf-8") as f:
            for line in f:
                (data_id, f_name) = line.split('|')
                data_id = data_id.strip()
                f_name = f_name.strip()
                f_name = ascii_me(ntpath.basename(f_name))
                self.id_manager.structured_document_name_to_id[f_name] = data_id

        resolved_kb.structured_documents = self._resolve_structured_inputs(kb)
        resolved_kb.structured_relationships = \
            self._resolve_structured_relationships(kb)

        return resolved_kb

    # Process the "relationships" section of self.structured_kb
    def _resolve_structured_relationships(self, kb):
        # only want to add relationship data if there are any!
        relationships = kb.structured_kb.get('relationships')

        if not relationships:
            return []

        # TODO rdf in serialization stage ?
        inference_uri = kb.structured_kb.get('schema')
        time_of_inference = datetime.utcnow()

        causal_inference = CausalInference(inference_uri, time_of_inference)

        all_relations = []
        num_relationships = len(relationships)
        for count, relationship in enumerate(relationships):
            if count % 1000 == 0:
                print ("StructuredResolver creating info from " 
                       "StructuredRelationship (" + str(count) + "/" +
                       str(num_relationships) + ")")

            relationship_type = relationship['type']
            cause_ref = relationship['cause']
            effect_ref = relationship['effect']

            unique_relationship_id = self.id_manager.to_id("Relationship",
                                                           str(count))

            cause_file_id = cause_ref['descriptor']['inputId']
            cause_file_id = self.id_manager.get_structured_file_id(
                cause_file_id)

            cause_frame_index = cause_ref['descriptor']['frameIdx']
            cause_entry_index = cause_ref['descriptor']['entryIdx']
            unique_cause_worksheet_id = self.id_manager.to_id(
                "Worksheet", cause_file_id, str(cause_frame_index))
            # trailing -1 is for entity ids
            unique_cause_property_id = self.id_manager.to_id(
                "Property", cause_file_id,
                str(cause_frame_index), str(cause_entry_index), -1)
            unique_cause_factor_id = self.id_manager.to_id(
                'Factor', cause_file_id,
                str(cause_frame_index), str(cause_entry_index))

            # TODO: add location, more specific tab_ref (with row/column info), and a better label
            cause_factor = Factor(
                quote_plus(ascii_me(unique_cause_factor_id)),
                'A factor',
                unique_cause_property_id,
                tab_ref=TabRef(unique_cause_worksheet_id))

            effect_file_id = effect_ref['descriptor']['inputId']
            effect_file_id = self.id_manager.get_structured_file_id(
                effect_file_id)
            effect_frame_index = effect_ref['descriptor']['frameIdx']
            effect_entry_index = effect_ref['descriptor']['entryIdx']
            unique_effect_worksheet_id = self.id_manager.to_id(
                "Worksheet", effect_file_id, str(effect_frame_index))
            unique_effect_property_id = self.id_manager.to_id(
                "Property", effect_file_id,
                str(effect_frame_index), str(effect_entry_index), -1)
            unique_effect_factor_id = self.id_manager.to_id(
                'Factor', effect_file_id,
                str(effect_frame_index), str(effect_entry_index))

            # TODO: add location, more specific tab_ref (with row/column info), and a better label
            effect_factor = Factor(
                quote_plus(ascii_me(unique_effect_factor_id)),
                'A factor',
                unique_effect_property_id,
                tab_ref=TabRef(unique_effect_worksheet_id))

            reliability = 'low'
            if 'confidence' in relationship:
                if 'reliability' in relationship['confidence']:
                    reliability = relationship['confidence']['reliability']

            causal_relation = CausalRelation(unique_relationship_id,
                                             ascii_me(relationship_type),
                                             cause_factor, effect_factor,
                                             reliability, causal_inference)
            all_relations.append(causal_relation)
        return all_relations

    def _resolve_structured_inputs(self, kb):

        inputs_length = len(kb.structured_kb['inputs'])
        document_list = []

        def tabref(t_file_id, worksheet_id, t_rows, t_cols):
            tab_ref_id = self.id_manager.to_id(
                "TableRef",
                t_file_id,
                worksheet_id,
                '_'.join([str(x) for x in t_rows]),
                '_'.join([str(x) for x in t_cols]))
            if t_rows:
                row = t_rows[0]
            else:
                row = None
            if t_cols:
                col = t_cols[0]
            else:
                col = None
            return TabRef(tab_ref_id, col, row)

        # process each input (e.g., an excel file)
        for input_count, input_record in enumerate(kb.structured_kb['inputs']):
            print("StructuredResolver creating info from StructuredInput (" + \
                  str(input_count) + "/" + str(inputs_length) + ")")

            # this is a little hacky. need to test this better.
            # M10 - id was in separate lookup table
            # M11 - id was contained in Two Six's json
            file_id = self.id_manager.get_structured_file_id(input_record['id'])

            file_name = ascii_me(input_record['name'])
            if 'ta5_triples' in input_record:
                file_meta_data = input_record['ta5_triples']
            else:

                # FIXME this issue needs to be repaired!
                # this is a bad hack - doc uri is referenced during doc creation
                # and needs to match here (before it's actually created)
                doc_uri = URIRef('http://graph.causeex.com/bbn#' + file_id)
                source_uri = URIRef('http://ontology.causeex.com/ontology/odps/'
                                    'DataProvenance#original_source')
                source_string = Literal(file_id, datatype=XSD.string)
                md_graph = Graph()
                md_graph.add((doc_uri, source_uri, source_string))
                file_meta_data = md_graph.serialize(format='nt')
                # TODO ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

            print('Creating input object '
                  'id: [{}] file: [{}]'.format(file_id, file_name))
            document = StructuredDocument(file_id, file_meta_data)

            # process each frame (e.g., tab in excel file)
            for frame_index, frame in enumerate(input_record['frames']):
                data_kind = frame.get('_data_kind', '')
                frame_id = frame['_id']

                unique_worksheet_id = self.id_manager.to_id(
                    "Worksheet", file_id, str(frame_index))
                print('  Processing frame [{}]'.format(frame_id) +
                      ' with unique id [{}]'.format(unique_worksheet_id))

                worksheet = Worksheet(unique_worksheet_id)
                document.add_sheet(worksheet)

                if data_kind.lower() == 'time_series':
                    entries = frame['_time_series_list']
                    modulo = 10
                    if len(entries) > 1000:
                        modulo = 100
                    if len(entries) > 10000:
                        modulo = 1000
                    for index, entry in enumerate(entries):
                        if index % modulo == 0:
                            print('    Processing time series '
                                  '[{}]'.format(index))

                        # time series needs property, id, name,
                        # entity=location, tabref (row or column)
                        property_dict, property_name, rows, cols = (
                            self.get_value(entry, '_property'))

                        label_dict, property_label, rows, cols = (
                            self.get_value(property_dict, '_label'))
                        if not property_label:
                            property_label = 'default property name goes here'  #TODO

                        if '_prefix' in label_dict:
                            property_label = (
                                    label_dict['_prefix'] + property_label)
                        if '_suffix' in label_dict:
                            property_label += label_dict['_suffix']

                        tab_ref = tabref(file_id, unique_worksheet_id, rows, cols)
                        worksheet.add_tab_ref(tab_ref)

                        a_dict, property_type, rows, cols = self.get_value(
                            property_dict, '_property_type')
                        if not property_type:
                            property_type = 'default property type goes here'  #TODO

                        # trailing -1 is for entity ids
                        unique_property_id = self.id_manager.to_id(
                            "Property",
                            file_id, str(frame_index), str(index), -1)
                        # TODO rdf in serialization stage
                        ts_property = Property(unique_property_id,
                                               URIRef(property_type),
                                               ascii_me(property_label),
                                               tab_ref)

                        # Add metadata about the properties
                        for property_name in self.get_value_names(property_dict):
                            (property_desc, property_value, property_rows,
                             property_cols) = \
                                self.get_value(property_dict, property_name)
                            #print('        Property metadata: ' + property_name + ' is ' +
                            #      str(property_value) + ' rows: '
                            #      + '_'.join([str(x) for x in property_rows])
                            #      + ' cols: ' + '_'.join([str(x) for x in property_cols]))
                            # TODO rdf in serialization stage
                            ts_property.add_property(URIRef(property_name),
                                                     URIRef(property_value))

                        unique_timeseries_id = self.id_manager.to_id(
                            "TimeSeries",
                            file_id, unique_worksheet_id, str(index))

                        a_dict, name_string, rows, cols = \
                            self.get_value(entry, '_name')
                        tab_ref = None  # TODO
                        location = self.get_location_obj(file_id, entry)
                        ts = TimeSeries(unique_timeseries_id,
                                        ts_property,
                                        ascii_me(name_string),
                                        location,
                                        tab_ref)
                        worksheet.add_time_series(ts)

                        # gravy
                        for property_name in self.get_value_names(entry):
                            (property_desc, property_value, property_rows,
                             property_cols) = \
                                self.get_value(entry, property_name)
                            #print('        property_name: ' + property_name + ' is ' +
                            #      str(property_value) + ' rows: '
                            #      + '_'.join([str(x) for x in property_rows])
                            #      + ' cols: ' + '_'.join([str(x) for x in property_cols]))
                            # TODO rdf in serialization stage
                            ts.add_property(URIRef(property_name),
                                            URIRef(property_value))
                            #for sub_property_name in self.get_value_names(property_desc):
                            #    sub_property_desc, sub_property_value, sub_property_rows, sub_property_cols = self.get_value(property_desc, sub_property_name)
                            #    print('            sub-property_name: ' + sub_property_name + ' is ' +
                            #      str(sub_property_value) + ' rows: '
                            #      + '_'.join([str(x) for x in sub_property_rows])
                            #          + ' cols: ' + '_'.join([str(x) for x in sub_property_cols]))

                        (time_points_times, time_points_values,
                         time_points_rows, time_points_columns) = \
                            self.get_time_points(entry)
                        for tt in range(len(time_points_times)):
                            t = time_points_times[tt]
                            v = time_points_values[tt]
                            r = [time_points_rows[tt]]
                            c = [time_points_columns[tt]]

                            try:
                                v = float(v)
                                if math.isnan(v):
                                    # not necessarily an error. blank cells in spreadsheet get nan
                                    # print('Skipping non-float reported value: ' + str(v))
                                    continue
                            except ValueError:
                                print('Skipping non-float reported value: '
                                      + str(v))
                                continue

                            tab_ref = tabref(
                                file_id, unique_worksheet_id, r, c)
                            worksheet.add_tab_ref(tab_ref)
                            # print('        data point at: ' + str(t) + ' is ' + str(v) + ' row: ' + str(r) + ' col: ' + str(c))
                            reported_value_id = self.id_manager.to_id(
                                "ReportedValue",
                                file_id, unique_timeseries_id, str(tt))

                            value = ReportedValue(
                                reported_value_id, v,
                                start_time=t, end_time=t, tab_ref=tab_ref)
                            ts.add_reported_value(value)
                        # import pdb; pdb.set_trace()

                elif data_kind.lower() == 'entity':
                    entries = frame['_entity_list']
                    modulo = 10
                    if len(entries) > 1000:
                        modulo = 100
                    if len(entries) > 10000:
                        modulo = 1000
                    for entity_index, entry in enumerate(entries):
                        if entity_index % modulo == 0:
                            print('    Processing entity '
                                  '[{}]'.format(entity_index))

                        location_string = self.get_value(entry, '_location')[1]
                        location = self.get_location_obj(file_id, entry)

                        reported_values = self.get_reported_values(entry)
                        for value_idx, reported_value in \
                                enumerate(reported_values):
                            (time_points_times, time_points_values,
                             time_points_rows, time_points_columns) = \
                                self.parse_data_values(reported_value)

                            # TODO: Figure out starting/ending times
                            t = None
                            if isinstance(time_points_times, list):
                                if len(time_points_times) > 0:
                                    t = time_points_times[0]
                                #else:
                                #    print('Expect to have time points in entity series - skipping for now')
                                #    continue
                            else:
                                t = time_points_times

                            # List could be empty
                            if len(time_points_values) < 1:
                                continue

                            v = time_points_values[0]
                            r = [time_points_rows[0]]
                            c = [time_points_columns[0]]

                            try:
                                v = float(v)
                                if math.isnan(v):
                                    print('Skipping non-float reported value: ' + str(v))
                                    continue
                            except ValueError:
                                print('Skipping non-float reported value: ' + str(v))
                                continue

                            property_dict, property_name, rows, cols = \
                                self.get_value(reported_value, '_property')
                            #if not property_name:
                            #    property_name = 'default property name goes here' #TODO

                            label_dict, property_label, rows, cols = \
                                self.get_value(property_dict, '_label')
                            if not property_label:
                                property_label = \
                                    'default property name goes here' #TODO

                            if '_prefix' in label_dict:
                                property_label = \
                                    label_dict['_prefix'] + property_label
                            if '_suffix' in label_dict:
                                property_label += label_dict['_suffix']

                            # TODO Figure out how to handle tab refs to multiple rows/cols
                            tab_ref = tabref(
                                file_id, unique_worksheet_id, rows, cols)
                            worksheet.add_tab_ref(tab_ref)

                            a_dict, property_type, rows, cols = \
                                self.get_value(property_dict, '_property_type')
                            if not property_type:
                                property_type = \
                                    'default property type goes here' #TODO

                            # trailing -1 is for entity ids
                            unique_property_id = \
                                self.id_manager.to_id(
                                    "Property", file_id, str(frame_index),
                                    str(value_idx), str(entity_index))
                            # TODO rdf in serialization stage
                            rv_property = Property(
                                unique_property_id, URIRef(property_type),
                                ascii_me(property_label), tab_ref)

                            for property_name in \
                                    self.get_value_names(property_dict):
                                (property_desc, property_value,
                                 property_rows, property_cols) = \
                                    self.get_value(property_dict, property_name)
                                #print('        property property_name: ' + property_name + ' is ' +
                                #      str(property_value) + ' rows: '
                                #      + '_'.join([str(x) for x in property_rows])
                                #      + ' cols: ' + '_'.join([str(x) for x in property_cols]))
                                # TODO rdf in serialization stage
                                rv_property.add_property(URIRef(property_name),
                                                         URIRef(property_value))

                            unique_reported_value_id = self.id_manager.to_id(
                                "ReportedValue", file_id, unique_worksheet_id,
                                str(entity_index), str(value_idx))

                            tab_ref = tabref(file_id, unique_worksheet_id, r, c)
                            worksheet.add_tab_ref(tab_ref)

                            value = ReportedValue(
                                unique_reported_value_id, v,
                                related_property=rv_property, start_time=t,
                                end_time=t, tab_ref=tab_ref)
                            location.add_reported_value(value)

                            for property_name in self.get_value_names(
                                    reported_value):
                                (property_desc, property_value, property_rows,
                                 property_cols) = self.get_value(
                                    reported_value, property_name)
                                # print('        rv property_name: ' + property_name + ' is ' +
                                #      str(property_value) + ' rows: '
                                #      + '_'.join([str(x) for x in property_rows])
                                #      + ' cols: ' + '_'.join([str(x) for x in property_cols]))
                                # TODO rdf in serialization stage
                                value.add_property(URIRef(property_name),
                                                   URIRef(property_value))

                        worksheet.add_entity(location)

                elif data_kind.lower() == 'event':
                    entries = frame['_event_list']
                    for event_index, entry in enumerate(entries):
                        if event_index % 100 == 0:
                            print('    Processing event '
                                  '[{}]'.format(event_index))

                        location = self.get_location_obj(file_id, entry)
                        _, name, rows, cols = self.get_value(entry, '_name')
                        event_type = self.get_value(entry, '_event_type')[1]
                        _, label, _, _ = self.get_value(entry, '_label')
                        start_time = self.get_value(entry,
                                                    '_start_time_stamp')[1]
                        if not start_time:
                            start_time = None
                        end_time = self.get_value(entry, '_end_time_stamp')[1]
                        if not end_time:
                            end_time = None
                        actors = self.get_actors(entry)
                        unique_event_id = self.id_manager.to_id(
                            "Event",
                            file_id, unique_worksheet_id, str(event_index))

                        tab_ref = tabref(
                            file_id, unique_worksheet_id, rows, cols)
                        worksheet.add_tab_ref(tab_ref)
                        event = Event(
                            unique_event_id, event_type, ascii_me(label),
                            location, start_time, end_time, tab_ref)

                        for actor in actors:
                            actor_names = actor['_vals']
                            if len(actor_names) != 1:
                                raise ValueError('Expecting 1, got: ' +
                                                 str(len(actor_names)))
                            actor_name = actor_names[0]
                            rows = actor['_rows']
                            if isinstance(rows, list) and len(rows) != 1:
                                raise ValueError('Expecting 1, got: ' +
                                                 str(len(rows)))
                            cols = actor['_cols']
                            if isinstance(cols, list) and len(cols) != 1:
                                raise ValueError('Expecting 1, got: ' +
                                                 str(len(cols)))
                            tab_ref = tabref(
                                file_id, unique_worksheet_id, rows, cols)
                            worksheet.add_tab_ref(tab_ref)
                            actor_type = self.get_value(actor, '_type')[1]
                            actor_role = self.get_value(actor, '_role')[1]
                            actor_label = self.get_value(actor, '_label')[1]
                            # TODO: these are missing values
                            if isinstance(actor_name, float):
                                print('Warning - was not expecting '
                                      '{} as an actor name'.format(actor_name))
                                actor_name = 'Unknown'
                            unique_actor_id = self.id_manager.to_id(
                                "Entity", file_id, actor_name)
                            act = Actor(unique_actor_id, actor_type,
                                        ascii_me(actor_label), tab_ref)
                            # TODO rdf in serialization stage
                            event.add_actor(URIRef(actor_role), act)
                        worksheet.add_event(event)
                else:
                    print('TODO: handle frame of type [{}]'.format(data_kind))

            document_list.append(document)
        return document_list

    def get_value(self, thing, value_name):
        if not value_name in thing:
            return {}, '', [], []
        val_dict = thing[value_name]
        # ADD prefix and suffix stuff here
        val_data = val_dict['_vals']
        if isinstance(val_data, list):
            if val_data and isinstance(val_data[0], unicode):
                val_data = '_'.join(val_data)
            elif val_data and isinstance(val_data[0], str):
                val_data = '_'.join(val_data)
            elif val_data and isinstance(val_data[0], float):
                val_data = '_'.join([str(x) for x in val_data])
            else:
                import pdb; pdb.set_trace()
                raise ValueError('huh? ' + str(val_data))
        elif isinstance(val_data, float):
            val_data = str(val_data)
        if '_rows' in val_dict:
            val_rows = val_dict['_rows']
            if not isinstance(val_rows, list):
                val_rows = [val_rows]
        else:
            val_rows = []
        if '_cols' in val_dict:
            val_cols = val_dict['_cols']
            if not isinstance(val_cols, list):
                val_cols = [val_cols]
        else:
            val_cols = []

        return val_dict, val_data, val_rows, val_cols

    def get_actors(self, thing):
        if not '_actors' in thing:
            raise ValueError('Expecting _actors')
        actors = thing['_actors']
        if not isinstance(actors, list):
            actors = [actors]
        return actors

    def get_reported_values(self, thing):
        if not '_reported_values' in thing:
            raise ValueError('Expecting _reported_values')
        points = thing['_reported_values']
        if not isinstance(points, list):
            points = [points]
        return points

    def get_time_points(self, thing):
        if not '_points' in thing:
            raise ValueError('Expecting _points')
        points = thing['_points']
        return self.parse_data_values(points)

    @staticmethod
    def parse_data_values(points):

        if not '_values' in points:
            raise ValueError('Expecting _values')

        if '_time_stamps' in points:
            #raise ValueError('Expecting _time_stamps')
            time_stamps = points['_time_stamps']['_vals']
        else:
            time_stamps = None

        values = points['_values']['_vals']
        values_rows = points['_values']['_rows']
        values_cols = points['_values']['_cols']
        return time_stamps, values, values_rows, values_cols

    def get_value_names(self, thing):
        names = []
        for key in thing.keys():
            if not key.startswith('_'):
                names.append(key)
        return names

    def get_entity_id(self, file_id, entity_name, entity_type):
        entity_id = self.id_manager.to_id("Entity",
                                          file_id, entity_name, entity_type)
        # currently this can never be true
        entity_is_country = entity_id.startswith('CAMEO')
        return entity_id, entity_is_country

    # Given a string representing a location, attempts to return the
    # corresponding CAMEO country code or BBN entity group ID. If this cannot be
    # done, returns an auto-generated "LOCATION" ID.
    def get_location_id(self, file_id, location):
        location = location.lower()
        if location in SharedIDManager.country_name_to_cameo_code_mappings:
            location_id = SharedIDManager.convert_to_cameo_optionally(location)
            kind_of_location = 'country'
        elif location in self.city_name_to_entity_group_id_mappings:
            location_id = self.city_name_to_entity_group_id_mappings[location]
            kind_of_location = 'city'
        else:
            location_id = self.id_manager.to_id("Entity", file_id, location)
            kind_of_location = 'location'
        return location_id, kind_of_location

    def get_location_obj(self, file_id, tag_dict):

        mar_entity_type = None

        # TODO: Handle location levels (e.g. country, state, town)
        if '_location' in tag_dict:
            geo_string = tag_dict['_location']['_vals']
            if isinstance(geo_string, list):
                temp_array = []
                for something in geo_string:
                    if isinstance(something, float):
                        temp_array.append(str(something))
                    else:
                        temp_array.append(ascii_me(something))
                geo_string = "_".join(temp_array)
            label = geo_string.replace('_', ' ')

            # TODO: this is a hack to encode the entity type for MAR data
            # TODO: Need a more general get_entity function which will get/build locations AND entities
            if 'rdf:type' in tag_dict:
                entity_type = tag_dict['rdf:type']['_vals']
                location_id, location_is_country = \
                    self.get_entity_id(file_id, geo_string, entity_type)
                mar_entity_type = entity_type
            else:
                location_id, location_type = \
                    self.get_location_id(file_id, geo_string)
                location_is_country = location_type == 'country'
                entity_type = location_type

        else:
            location_id = 'Unknown'
            location_is_country = False
            label = 'Unknown'
            entity_type = "location"

        return EntityData(location_id,
                          is_country=location_is_country,
                          label=label,
                          mar_entity_type=mar_entity_type,
                          entity_type=entity_type)


def ascii_me(a_string):
    res = ''
    try:
        res = a_string.encode('ascii', 'ignore').decode('ascii')
    except:
        import pdb
        pdb.set_trace()
    return res


# Note: only used for structured data
# Given an object "type" string and a list of identifying attributes, returns a
# unique id string for that object. The string is in the format
# [type string]-[number], where the number iterates for every different set of
# attributes for a given type.
class IDManager:
    def __init__(self):
        self.type_to_attributes_mappings = {}
        self.structured_document_name_to_id = dict()

    def to_id(self, object_type, *object_attributes):
        if not object_attributes:
            raise ValueError('Expecting object_attributes')
        if object_type not in self.type_to_attributes_mappings:
            self.type_to_attributes_mappings[object_type] = {}
        if object_attributes not in self.type_to_attributes_mappings[object_type]:
            # Integration with SharedIDManager is as follows:
            # check whether this is an object type it manages
            # if so, then we assume the zeroth item in object_attributes
            # is the file_id (document_id)
            # otherwise, we just generate an id by incrementing by object type
            # either way, we cache the id here for future use
            if SharedIDManager.is_in_document_type(object_type):
                presumed_document_id = object_attributes[0]
                the_id = SharedIDManager.get_in_document_id(object_type, presumed_document_id)
            else:
                the_id = "%s-%d" % (object_type, len(self.type_to_attributes_mappings[object_type]))
            self.type_to_attributes_mappings[object_type][object_attributes] = the_id
        return self.type_to_attributes_mappings[object_type][object_attributes]

    def get_structured_file_id(self, file_path):
        # if rel_path is in data djict, replace it
        file_id = 'unknownm'
        if file_path in self.structured_document_name_to_id.keys():
            file_id = self.structured_document_name_to_id[file_path]
        elif file_path.find("zip") != -1:
            (dir, zip, filename) = file_path.split('\\')
            file_id = self.structured_document_name_to_id[zip.strip()] + '\\' + filename.strip()
        else:
            fname = ntpath.basename(file_path).encode('ascii', 'ignore').decode('ascii')
            if fname in self.structured_document_name_to_id.keys():
                file_id = self.structured_document_name_to_id[fname]

        if file_id == 'unknown':
            #print "Using file ID directly - : " + file_path
            file_id = file_path.encode('ascii', 'ignore').decode('ascii').replace(" ", "_")

        return file_id
