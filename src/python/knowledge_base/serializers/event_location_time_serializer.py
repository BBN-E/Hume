# A class for quickly viewing event mentions sorted by document

import codecs, json, os
from collections import defaultdict

from elements.kb_mention import KBMention
from elements.kb_value_mention import KBValueMention

class EventLocationTimeSerializer:

    location_roles = {"has_location", "has_origin_location", "has_destination_location", "Place", "Origin", "Destination"}
    time_roles = {"Time", "has_time", "Time-Within"}

    location_properties = {"state", "best_location_method"}
    time_properties = {"best_month", "best_month_method"}

    def __init__(self):
        self.stats = defaultdict(int)

    def serialize(self, kb, output_file):
        print("EventLocationTimeSerializer SERIALIZE")

        o = codecs.open(output_file, 'w', encoding='utf8')
        # o1 = codecs.open(os.path.join(output_dir, 'all_events.txt'), 'w', encoding='utf8')
        # o2 = codecs.open(os.path.join(output_dir, 'best_location_method_is_sentence_events.txt'), 'w', encoding='utf8')
        # o3 = codecs.open(os.path.join(output_dir, 'best_location_method_is_argument_events.txt'), 'w', encoding='utf8')

        all_event_strings = []
        best_location_method_is_sentence_strings = []
        best_location_method_is_sentence_seen = set()
        best_location_method_is_argument_strings = []
        best_location_method_is_argument_seen = set()
        for evid, event in kb.get_events():
            event_string = ""

            # o.write("\n=============================================")
            event_string += "\n============================================="
            # o.write("\nevent id: {}".format(evid))
            event_string += "\nevent id: {}".format(evid)
            self.stats["num_kb_events"] += 1

            for event_mention in event.event_mentions:

                self.stats["num_kb_event_mentions"] += 1

                # o.write("\nevent mention id: {}".format(event_mention.id))
                event_string += "\nevent mention id: {}".format(event_mention.id)
                # o.write("\ntrigger: \"{}\"".format(event_mention.trigger))
                event_string += "\ntrigger: \"{}\"".format(event_mention.trigger)
                # o.write("\nsentence: \"{}\"".format(event_mention.sentence.text))
                event_string += "\nsentence: \"{}\"".format(event_mention.sentence.text)

                # o.write("\n\tARGUMENTS------------------------------------")
                event_string += "\n\tARGUMENTS------------------------------------"
                for role,args in event_mention.arguments.items():
                    if role in self.location_roles or role in self.time_roles:
                        self.stats["num_\"{}\"_role".format(role)] += 1
                        arg_type_text = []
                        for mention, confidence in args:
                            if isinstance(mention, KBMention):
                                arg_type_text.append((mention.entity_type, mention.mention_text))
                            elif isinstance(mention, KBValueMention):
                                arg_type_text.append((mention.value_type, mention.value_mention_text))
                        # o.write("\n\t{}\t{}".format(role, arg_type_text))
                        event_string += "\n\t{}\t{}".format(role, arg_type_text)

                best_location_method_is_sentence = False
                best_location_method_is_argument = False
                # o.write("\n\tPROPERTIES-----------------------------------")
                event_string += "\n\tPROPERTIES-----------------------------------"
                for k,v in event_mention.properties.items():
                    if k == 'best_location_method' and v == 'sentence':
                        best_location_method_is_sentence = True
                    elif k == 'best_location_method' and v == 'argument':
                        best_location_method_is_argument = True
                    if k in self.location_properties or k in self.time_properties:
                        self.stats["num_\"{}\"".format(k)] += 1
                        if isinstance(v, list):
                            v = "|".join(list(set(v)))  # there will only be one best_location_method per event mention, even if several states
                        # o.write("\n\t{}\t{}".format(k, v))
                        event_string += "\n\t{}\t{}".format(k, v)

                if best_location_method_is_sentence and event_mention.sentence.text not in best_location_method_is_sentence_seen:
                    best_location_method_is_sentence_strings.append(event_string)
                    best_location_method_is_sentence_seen.add(event_mention.sentence.text)
                elif best_location_method_is_argument and event_mention.sentence.text not in best_location_method_is_sentence_seen:
                    best_location_method_is_argument_strings.append(event_string)
                    best_location_method_is_argument_seen.add(event_mention.sentence.text)
                all_event_strings.append(event_string)

        o.write("\n".join(all_event_strings))

        # o1.write("\n".join(all_event_strings))
        # o2.write("\n".join(best_location_method_is_sentence_strings))
        # o3.write("\n".join(best_location_method_is_argument_strings))
        # o1.close()
        # o2.close()
        # o3.close()
        # print(json.dumps(self.stats))
