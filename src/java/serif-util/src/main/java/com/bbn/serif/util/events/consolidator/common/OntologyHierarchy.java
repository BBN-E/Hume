package com.bbn.serif.util.events.consolidator.common;

import com.bbn.serif.util.InternalOntology;
import com.bbn.serif.util.InternalOntologyNode;
import com.bbn.serif.util.Pair;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;
import com.google.common.base.Charsets;
import com.google.common.base.Optional;
import com.google.common.collect.ArrayListMultimap;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableMultimap;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.ImmutableSetMultimap;
import com.google.common.collect.Lists;
import com.google.common.collect.Maps;
import com.google.common.collect.Multimap;
import com.google.common.io.Files;

import java.io.File;
import java.io.IOException;
import java.util.List;
import java.util.Map;
import java.util.Stack;
import java.util.regex.Pattern;

public class OntologyHierarchy{
  final private String ontologyName;
  final private ImmutableMultimap<String, String> roleLeafToHierarchy;
  final private ImmutableMultimap<String, String> leafToHierarchy;
  //final private ImmutableSetMultimap<String, String> compatibleEventTypes;
  final private ImmutableSetMultimap<String, String> eventTypeRoleEntityTypeConstraints;
  final private ImmutableSetMultimap<String, String> keywordToEventType;
  final private ImmutableMap<String, String> wordToLemma;
  final private ImmutableSetMultimap<String, String> blacklistKeywordToEventType;

  public OntologyHierarchy(final String ontologyName, final String roleOntologyFile, final String yamlOntologyFile,
      final String argumentRoleEntityTypeFile,
      final String keywordFile, final String lemmaFile, final String blacklistFile)
      throws IOException {
    this.ontologyName = ontologyName;

    final String rootNodeString = ontologyName.equals(OntologyHierarchy.INTERNAL_ONTOLOGY) ? "Event" : "Factor";

    this.leafToHierarchy = parseOntologyYamlFile(yamlOntologyFile, rootNodeString);
    this.roleLeafToHierarchy = parseOntologyYamlFile(roleOntologyFile, "Role");

    //this.compatibleEventTypes = extractCompatibleEventTypes(Files.asCharSource(new File(compatibleFile), Charsets.UTF_8).readLines());

    // some (eventType, eventRole) can only take on certain entity types
    this.eventTypeRoleEntityTypeConstraints = extractEventTypeRoleEntityTypeConstraints(Files.asCharSource(new File(argumentRoleEntityTypeFile), Charsets.UTF_8).readLines());

    this.keywordToEventType = extractKeywordToEventType(Files.asCharSource(new File(keywordFile), Charsets.UTF_8).readLines());

    this.wordToLemma = extractWordToLemma(Files.asCharSource(new File(lemmaFile), Charsets.UTF_8).readLines());
    this.blacklistKeywordToEventType = extractKeywordToEventType(Files.asCharSource(new File(blacklistFile), Charsets.UTF_8).readLines());

    this.printHierarchy();
  }

  // +1
  private ImmutableMultimap<String, String> parseOntologyYamlFile(final String filepath, final String rootString) throws IOException {
    ObjectMapper objectMapper = new ObjectMapper(new YAMLFactory());
    List<Map> parseRoot = objectMapper.readValue(new File(filepath),List.class);
    List<Map> yamlRoot = (List<Map>)parseRoot.get(0).get(rootString);
    InternalOntologyNode ontologyRoot = InternalOntologyNode.buildInternalOntologyHierachy(yamlRoot, rootString);
    Multimap<String,String> resultMap = ArrayListMultimap.create();
    InternalOntology.DFSDotIdBasedPathParsing(ontologyRoot,new Stack<>(),resultMap);
    return ImmutableMultimap.copyOf(resultMap);
  }

  // +1
  public boolean isInBlackList(final String eventType, final String keyword) {
    return this.blacklistKeywordToEventType.containsEntry(keyword.toLowerCase(), eventType);
  }

  // +1
  private static ImmutableMap<String, String> extractWordToLemma(final ImmutableList<String> lines) {
    final ImmutableMap.Builder<String, String> ret = ImmutableMap.builder();
    for(final String line : lines) {
      final String[] tokens = line.split(" ");
      ret.put(tokens[0], tokens[1]);
    }
    return ret.build();
  }

  // +1
  public String getLemmaForWord(final String word) {
    final String w = word.toLowerCase();
    if(this.wordToLemma.containsKey(w)) {
      return this.wordToLemma.get(w);
    } else {
      return w;
    }
  }

  // +1
  private ImmutableSetMultimap<String, String> extractKeywordToEventType(final ImmutableList<String> lines) {
    final ImmutableSetMultimap.Builder<String, String> ret = ImmutableSetMultimap.builder();
    for(final String line : lines) {
      final String[] tokens = line.split("\t");

      final String eventType = tokens[0];
      if(!eventType.equals("NO_EVENT")) {
        assertEventTypeIsInOntology(eventType, "extractKeywordToEventType");
      }

      for(int i=1; i<tokens.length; i++) {
        final String keyword = tokens[i].toLowerCase();
        ret.put(keyword, eventType);
      }
    }
    return ret.build();
  }

  // +1
  private ImmutableSetMultimap<String, String> extractEventTypeRoleEntityTypeConstraints(final ImmutableList<String> lines) {
    final ImmutableSetMultimap.Builder<String, String> ret = ImmutableSetMultimap.builder();
    for(final String line : lines) {
      final String[] tokens = line.split("\t");

      final String eventType = tokens[0];
      assertEventTypeIsInOntology(eventType, "extractEventTypeRoleEntityTypeConstraints");

      final String eventRole = tokens[1];
      assertEventRoleIsInOntology(eventRole, "extractEventTypeRoleEntityTypeConstraints");

      final String entityType = tokens[2];
      final String id = eventType + ":" + eventRole;
      ret.put(id, entityType);
    }
    return ret.build();
  }

//  private static ImmutableSetMultimap<String, String> extractCompatibleEventTypes(final ImmutableList<String> lines) {
//    final ImmutableSetMultimap.Builder<String, String> ret = ImmutableSetMultimap.builder();
//    for(final String line : lines) {
//      final String[] tokens = line.split(" ");
//      for(final String token : tokens) {
//        ret.putAll(token, Sets.newHashSet(tokens));
//      }
//    }
//    return ret.build();
//  }

  @Deprecated
  // @hqiu: We use yaml parser directly now
  private static ImmutableMap<String, String> extractLeafToHierarchy(final ImmutableList<String> lines) {
    Map<String, String> currentMap = Maps.newHashMap();

    for(final String line: lines) {
      String[] tokens;
      if(line.contains(".")) {
        tokens = line.split(Pattern.quote("."));
      } else {
        tokens = new String[1];
        tokens[0] = line;
      }
      String leaf_node = tokens[tokens.length - 1];

      if(!currentMap.containsKey(leaf_node)) {
        currentMap.put(leaf_node, line);
      } else {
        final int currentPathLength = currentMap.get(leaf_node).split(Pattern.quote(".")).length;
        final int newPathLength = tokens.length;
        if(newPathLength < currentPathLength) {
          currentMap.put(leaf_node, line);
        }
      }

    }

    return ImmutableMap.copyOf(currentMap);
  }

  // +2
  public boolean satisfyEventTypeRoleEntityTypeConstraints(final String eventType, final String eventRole, final String entityType) {
    final String et = eventType;

    final String id = et + ":" + eventRole;
    if(this.eventTypeRoleEntityTypeConstraints.containsKey(id)) {
      return this.eventTypeRoleEntityTypeConstraints.get(id).contains(entityType);
    } else {
      return true;
    }
  }

//  public boolean isEventTypesCompatible(final String type1, final String type2) {
//    final String et1 = type1;
//    final String et2 = type2;
//
//    if( this.compatibleEventTypes.containsKey(et1) && this.compatibleEventTypes.get(et1).contains(et2) ||
//        this.compatibleEventTypes.containsKey(et2) && this.compatibleEventTypes.get(et2).contains(et1) ) {
//      return true;
//    } else {
//      return false;
//    }
//  }

  public String getOntologyName() {
    return this.ontologyName;
  }

  // +1
  public Optional<ImmutableList<String>> getHierarchy(final String leaf) {
    final String et = leaf;

    if(this.leafToHierarchy.containsKey(et)) {
      return Optional.of(this.leafToHierarchy.get(et).asList());
    } else {
      return Optional.absent();
    }
  }

  // +1
  public boolean onSameHierarchyPath(final String path1, final String path2) {
    return path1.contains(path2) || path2.contains(path1);
  }

  // +1
  public Optional<Pair<String, String>> getSameHierarchyPath(final ImmutableList<String> paths1, final ImmutableList<String> paths2) {
    List<Pair<String, String>> ret = Lists.newArrayList();
    for(final String path1 : paths1) {
      for(final String path2 : paths2) {
        if(onSameHierarchyPath(path1, path2)) {
          ret.add(new Pair<String, String>(path1, path2));
          //return Optional.of(new Pair<String, String>(path1, path2));
        }
      }
    }
    if(ret.size() > 1) {
      String s = "WARNING: getSameHierarchyPath found > 1 same hierarchy path pairs, returning the first pair:";
      for(final Pair<String, String> p : ret) {
        s += " " + p.getFirst() + ":" + p.getSecond();
      }
      System.out.println(s);
      return Optional.of(ret.get(0));
    } else if(ret.size() == 1) {
      return Optional.of(ret.get(0));
    }
    return Optional.absent();
  }

//  public boolean sharePathPrefix(final String path1, final String path2, final int numberOfPrefix) {
//    final String[] path1Tokens = path1.split(Pattern.quote("."));
//    final String[] path2Tokens = path2.split(Pattern.quote("."));
//    if(path1Tokens.length >= numberOfPrefix && path2Tokens.length >= numberOfPrefix) {
//      boolean same = true;
//      for(int i=0; i<numberOfPrefix; i++) {
//        if(!path1Tokens[i].equalsIgnoreCase(path2Tokens[i])) {
//          same = false;
//          break;
//        }
//      }
//      return same;
//    }
//    return false;
//  }
//
//  public Optional<Pair<String, String>> getPathsSharingPrefix(final ImmutableList<String> paths1, final ImmutableList<String> paths2, final int numberOfPrefix) {
//    for(final String path1 : paths1) {
//      for(final String path2 : paths2) {
//        if(sharePathPrefix(path1, path2, numberOfPrefix)) {
//          return Optional.of(new Pair<String, String>(path1, path2));
//        }
//      }
//    }
//    return Optional.absent();
//  }

  // +1
  public String getShorterPath(final String path1, final String path2) {
    final String[] path1Tokens = path1.split(Pattern.quote("."));
    final String[] path2Tokens = path2.split(Pattern.quote("."));
    if(path1Tokens.length <= path2Tokens.length) {
      return path1;
    } else {
      return path2;
    }
  }

  // +1
  public String getLongerPath(final String path1, final String path2) {
    final String[] path1Tokens = path1.split(Pattern.quote("."));
    final String[] path2Tokens = path2.split(Pattern.quote("."));
    if(path1Tokens.length <= path2Tokens.length) {
      return path2;
    } else {
      return path1;
    }
  }

  // +1
  public boolean isValidEventType(final String s) {
    return this.leafToHierarchy.keySet().contains(s);
  }

  // +1
  public boolean isValidRole(final String s) {
    return this.roleLeafToHierarchy.keySet().contains(s) && !s.equals("Role");
  }

  public void printHierarchy() {
    for(final String leaf : this.leafToHierarchy.keySet()) {
      for(final String hierarchy : this.leafToHierarchy.get(leaf)) {
        System.out.println("Event: " + leaf + " => " + hierarchy);
      }
    }
    for(final String leaf : this.roleLeafToHierarchy.keySet()) {
      for(final String hierarchy : this.roleLeafToHierarchy.get(leaf)) {
        System.out.println("Role: " + leaf + " => " + hierarchy);
      }
    }
  }

  // +1
  public ImmutableSet<String> getEventTypesUsingKeyword(final String keyword) {
    return this.keywordToEventType.get(keyword.toLowerCase());
  }

  public void assertEventTypeIsInOntology(final String eventType, final String callerContext) {
    if(!this.isValidEventType(eventType)) {
      System.out.println("ERROR: " + callerContext + ": eventType=" + eventType + " is not in event ontology");
      System.exit(1);
    }
  }

  public void assertEventRoleIsInOntology(final String eventRole, final String callerContext) {
    if(!this.isValidRole(eventRole)) {
      System.out.println("ERROR: " + callerContext + ": eventRole=" + eventRole + " is not in event ontology");
      System.exit(1);
    }
  }

  public static String INTERNAL_ONTOLOGY = "INTERNAL_ONTOLOGY";
  public static String CAUSAL_FACTOR_ONTOLOGY = "CAUSAL_FACTOR_ONTOLOGY";
}

