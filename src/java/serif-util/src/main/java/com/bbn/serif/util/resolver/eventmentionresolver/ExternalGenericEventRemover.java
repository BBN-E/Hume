package com.bbn.serif.util.resolver.eventmentionresolver;

import com.bbn.serif.theories.EventMention;
import com.bbn.serif.util.InternalOntologyNode;
import com.bbn.serif.util.resolver.Resolver;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;

import java.io.File;
import java.io.IOException;
import java.util.*;

public class ExternalGenericEventRemover implements EventMentionResolver, Resolver {

    static void DFSOntologyTreeVisitor(InternalOntologyNode root, Map<String,Set<String>> internalTypeToExternalTypes){
        Set<String> buf = internalTypeToExternalTypes.getOrDefault(root.originalKey,new HashSet<>());
        for(String source: root._source){
            if(source.startsWith("WM:")){
                String ontologyEnding = source.split(":")[1].trim();
                buf.add(ontologyEnding);
            }
        }
        internalTypeToExternalTypes.put(root.originalKey,buf);
        for(InternalOntologyNode child: root.children){
            DFSOntologyTreeVisitor(child,internalTypeToExternalTypes);
        }
    }

    private Map<String,Set<String>> parseOntologyYamlFile(final String filepath, final String rootString) throws IOException {
        ObjectMapper objectMapper = new ObjectMapper(new YAMLFactory());
        List<Map> parseRoot = objectMapper.readValue(new File(filepath),List.class);
        List<Map> yamlRoot = (List<Map>)parseRoot.get(0).get(rootString);
        InternalOntologyNode ontologyRoot = InternalOntologyNode.buildInternalOntologyHierachy(yamlRoot, rootString);
         Map<String,Set<String>> ret = new HashMap<>();
        DFSOntologyTreeVisitor(ontologyRoot,ret);
        return ret;
    }

    final Set<String> genericEventTypes = new HashSet<>();

    public ExternalGenericEventRemover(List<String> internalOntologyYAMLPaths) throws IOException {
        for(String path: internalOntologyYAMLPaths){
            Map<String,Set<String>> containedNodeNames = parseOntologyYamlFile(path,"Event");
            genericEventTypes.addAll(containedNodeNames.getOrDefault("Event",new HashSet<>()));
        }
    }

    @Override
    public Optional<EventMention> resolve(EventMention em) {
        for(EventMention.EventType eventType:em.factorTypes()){
            if(!this.genericEventTypes.contains(eventType.eventType().asString())){
                return Optional.of(em);
            }
        }
        return Optional.empty();
    }

}
