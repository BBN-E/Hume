package com.bbn.serif.util.resolver.eventmentionresolver;

import com.bbn.serif.theories.EventMention;
import com.bbn.serif.util.InternalOntologyNode;
import com.bbn.serif.util.resolver.Resolver;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;

import java.io.File;
import java.io.IOException;
import java.util.*;

public class EventTypeOntologyComplianceResolver implements EventMentionResolver, Resolver {

    static void DFSOntologyTreeVisitor(InternalOntologyNode root, Set<String> eventTypes){
        eventTypes.add(root.originalKey);
        for(InternalOntologyNode child: root.children){
            DFSOntologyTreeVisitor(child,eventTypes);
        }
    }

    private Set<String> parseOntologyYamlFile(final String filepath, final String rootString) throws IOException {
        ObjectMapper objectMapper = new ObjectMapper(new YAMLFactory());
        List<Map> parseRoot = objectMapper.readValue(new File(filepath),List.class);
        List<Map> yamlRoot = (List<Map>)parseRoot.get(0).get(rootString);
        InternalOntologyNode ontologyRoot = InternalOntologyNode.buildInternalOntologyHierachy(yamlRoot, rootString);
        Set<String> ret = new HashSet<>();
        DFSOntologyTreeVisitor(ontologyRoot,ret);
        return ret;
    }

    Set<String> whiteListedEventTypes;
    public EventTypeOntologyComplianceResolver(List<String> internalOntologyYAMLPaths) throws IOException {
        this.whiteListedEventTypes = new HashSet<>();
        for(String path: internalOntologyYAMLPaths){
            Set<String> containedNodeNames = parseOntologyYamlFile(path,"Event");
            this.whiteListedEventTypes.addAll(containedNodeNames);
        }
        this.whiteListedEventTypes.remove("Event");
    }
    @Override
    public Optional<EventMention> resolve(EventMention em) {
        EventMention.Builder modifiedEventMention = em.modifiedCopyBuilder();
        List<EventMention.EventType> cleanEventType = new ArrayList<>();
        for(EventMention.EventType eventType: em.eventTypes()){
            if(this.whiteListedEventTypes.contains(eventType.eventType().asString())){
                cleanEventType.add(eventType);
            }
        }
        List<EventMention.EventType> cleanFactorType = new ArrayList<>();
        for(EventMention.EventType factorType:em.factorTypes()){
            if(this.whiteListedEventTypes.contains(factorType.eventType().asString())){
                cleanFactorType.add(factorType);
            }
        }
        if(this.whiteListedEventTypes.contains(em.type().asString()) || cleanEventType.size() > 0 || cleanFactorType.size() > 0){
            modifiedEventMention.setEventTypes(cleanEventType);
            modifiedEventMention.setFactorTypes(cleanFactorType);
            return Optional.of(modifiedEventMention.build());
        }
        return Optional.empty();
    }
}
