from elements.kb_event import KBEvent
from elements.kb_event_mention import KBEventMention
from internal_ontology import OntologyMapper
from resolvers.kb_resolver import KBResolver
from knowledge_base import KnowledgeBase
from shared_id_manager.shared_id_manager import SharedIDManager


# take direction_of_change property on KBEventMention and
# create new event for it

class EventDirectionResolver(KBResolver):

    def __init__(self):
        pass

    def resolve(self, kb, event_ontology_yaml, ontology_flags):
        print("EventDirectionResolver RESOLVE")

        ontology_mapper = OntologyMapper()
        ontology_mapper.load_ontology(event_ontology_yaml)
        event_type_to_grounded_types = {}
        valid_directions = ["Increase", "Decrease"]
        for direction in valid_directions:
            for flag in ontology_flags.split(','):
                grounded_types = ontology_mapper.look_up_external_types(
                    direction, flag)
                event_type_to_grounded_types.setdefault(direction, []).extend(
                    grounded_types)

        resolved_kb = KnowledgeBase()
        super(EventDirectionResolver, self).copy_all(resolved_kb, kb)

        new_kb_events = []
        for kb_event in resolved_kb.evid_to_kb_event.values():
            kb_event_mentions = []
            directions = set()
            for kb_event_mention in kb_event.event_mentions:
                groundings = [type for type, score
                              in kb_event_mention.external_ontology_sources]
                # Avoid redundancy
                if any(event_type_to_grounded_types[direction] in groundings
                       for direction in valid_directions):
                    continue
                
                if not kb_event_mention.trigger:
                    continue

                if not "direction_of_change" in kb_event_mention.properties:
                    continue
                
                direction = kb_event_mention.properties["direction_of_change"]
                if direction not in valid_directions:
                    continue
                directions.add(direction)

                event_mention_id = SharedIDManager.get_in_document_id("EventMention", kb_event_mention.document.id)
                new_kb_event_mention = KBEventMention(
                    event_mention_id,
                    kb_event_mention.document,
                    kb_event_mention.trigger,
                    kb_event_mention.trigger_start,
                    kb_event_mention.trigger_end,
                    kb_event_mention.snippet,
                    [],
                    [],
                    kb_event_mention.sentence,
                    [],
                    None,
                    kb_event_mention.model,
                    kb_event_mention.event_confidence,
                    kb_event_mention.trigger_original_text
                )
                for grounding in event_type_to_grounded_types[direction]:
                    new_kb_event_mention.add_or_change_grounding(
                        grounding, kb_event_mention.get_max_grounding_confidence())
                new_kb_event_mention.has_topic = kb_event_mention
                kb_event_mentions.append(new_kb_event_mention)
            if len(directions) != 1:
                continue
            event_id = SharedIDManager.get_in_document_id("Event", new_kb_event_mention.document.id)
            new_kb_event = KBEvent(
                event_id,
                event_type_to_grounded_types[directions.pop()][0])

            for kb_event_mention in kb_event_mentions:
                new_kb_event.add_event_mention(kb_event_mention)
            new_kb_events.append(new_kb_event)

        for new_kb_event in new_kb_events:
            resolved_kb.add_event(new_kb_event)

        return resolved_kb
