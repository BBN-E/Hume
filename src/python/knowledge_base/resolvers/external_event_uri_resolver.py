# Copyright 2019 Raytheon BBN Technologies

import sys
import os
import re

from kb_resolver import KBResolver
from knowledge_base import KnowledgeBase
try:
    from internal_ontology.internal_ontology import InternalOntology
except ImportError:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.realpath(__file__),
                                                    '..')))
    try:
        from internal_ontology.internal_ontology import InternalOntology
    except ImportError as e:
        raise e


class ExternalEventURIResolver(KBResolver):

    def __init__(self):
        super(ExternalEventURIResolver, self).__init__()
        self.old_id_re = re.compile(r'\b(.+?)(_\d+)?\b')

    @staticmethod
    def get_ontology_uri(event_type,ontology_flag,ontology,graph,backup_namespace,go_up_instead_of_using_backup_namespace=False):
        external_uri = InternalOntology.get_external_source(event_type,ontology_flag,graph,backup_namespace)
        if go_up_instead_of_using_backup_namespace is False:
            if backup_namespace == "DO_NOT_USE_BACKUP_NAMESPACE" and external_uri == u"{}#{}".format(backup_namespace, event_type):
                return None
            return external_uri
        elif go_up_instead_of_using_backup_namespace is True and backup_namespace in external_uri:
            parent_node = ontology.get_internal_class_from_type(event_type).parent
            return ExternalEventURIResolver.get_ontology_uri(parent_node.class_name,ontology_flag,ontology,graph,backup_namespace,go_up_instead_of_using_backup_namespace)
        else:
            if backup_namespace == "DO_NOT_USE_BACKUP_NAMESPACE" and external_uri == u"{}#{}".format(backup_namespace, event_type):
                return None
            return external_uri

    def resolve(self, kb, yaml, ontology_flags,should_go_up_instead_of_using_backup_namespaces, backup_namespaces):
        print "ExternalEventURIResolver RESOLVE"

        resolved_kb = KnowledgeBase()
        super(ExternalEventURIResolver, self).copy_all(resolved_kb, kb)
        ontology = InternalOntology(yaml)
        graph = ontology.rdf
        ontology_flags = ontology_flags.split(",")
        ontology_flags = [i.strip() for i in ontology_flags]
        should_go_up_instead_of_using_backup_namespaces = should_go_up_instead_of_using_backup_namespaces.split(",")
        should_go_up_instead_of_using_backup_namespaces = [True if i.lower() in {'true'} else False for i in should_go_up_instead_of_using_backup_namespaces]
        backup_namespaces = backup_namespaces.split(",")
        backup_namespaces = [i.strip() for i in backup_namespaces]
        assert len(ontology_flags) == len(should_go_up_instead_of_using_backup_namespaces)
        assert len(ontology_flags) == len(backup_namespaces)
        assert len(should_go_up_instead_of_using_backup_namespaces) == len(backup_namespaces)
        # resolve events and event mentions
        for event_id, kb_event in resolved_kb.evid_to_kb_event.iteritems():
            assert len(kb_event.event_type_to_confidence.keys()) == 1
            best_event_type, best_confidence = sorted(
                kb_event.event_type_to_confidence.items(),
                key=lambda x: x[1],
                reverse=True)[0]
            if ontology.get_internal_class_from_type(best_event_type) is None:
                raise IOError("Invalid KBEvent.event_type_to_confidence key '{}'".format(best_event_type))

            kb_event.event_type_to_confidence = dict()
            for idx in range(len(ontology_flags)):
                ontology_flag = ontology_flags[idx]
                should_go_up_instead_of_using_backup_namespace = should_go_up_instead_of_using_backup_namespaces[idx]
                backup_namespace = backup_namespaces[idx]
                external_uri = ExternalEventURIResolver.get_ontology_uri(best_event_type,ontology_flag,ontology,graph,backup_namespace,should_go_up_instead_of_using_backup_namespace)
                if external_uri is None:
                    if backup_namespace == "DO_NOT_USE_BACKUP_NAMESPACE":
                        continue

                kb_event.event_type_to_confidence[external_uri] = best_confidence

            for kb_event_mention in kb_event.event_mentions:
                kb_event_mention.external_ontology_sources = list()
                for idx in range(len(ontology_flags)):
                    ontology_flag = ontology_flags[idx]
                    should_go_up_instead_of_using_backup_namespace = should_go_up_instead_of_using_backup_namespaces[idx]
                    backup_namespace = backup_namespaces[idx]
                    external_uri = ExternalEventURIResolver.get_ontology_uri(kb_event_mention.event_type,ontology_flag,ontology,graph,backup_namespace,should_go_up_instead_of_using_backup_namespace)
                    if external_uri is None:
                        if backup_namespace == "DO_NOT_USE_BACKUP_NAMESPACE":
                            continue
                    kb_event_mention.external_ontology_sources.append([external_uri,kb_event_mention.confidence])
        return resolved_kb
