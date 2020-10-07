package com.bbn.serif.util;

import com.bbn.bue.common.files.FileUtils;
import com.bbn.bue.common.parameters.Parameters;
import com.bbn.serif.io.SerifXMLLoader;
import com.bbn.serif.io.SerifXMLWriter;
import com.bbn.serif.theories.*;
import com.bbn.serif.theories.icewseventmentions.ICEWSEventMention;

import com.google.common.base.Optional;
import com.google.common.collect.ImmutableList;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.nio.Buffer;
import java.util.*;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.serif.theories.icewseventmentions.ICEWSEventMentions;

import org.json.simple.JSONArray;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;

public final class EventEventRelationCreator {

  // relation where the arguments are stored by offsets (CausalRelation from json)
  private class RelationByOffset {
    JSONObject relation;
    String docID;
    String arg1Text;
    String arg2Text;
    Symbol semanticClass;
    Optional<String> pattern;
    Optional<Double> confidence;
    Optional<String> model;

    List<Pair<Long, Long>> arg1Offsets;
    List<Pair<Long, Long>> arg2Offsets;

    RelationByOffset(JSONObject relation) {
      this.relation = relation;
      this.docID = (String) relation.get("docid");
      this.arg1Text = (String) relation.get("arg1_text");
      this.arg2Text = (String) relation.get("arg2_text");
      this.semanticClass = Symbol.from( (String) relation.get("semantic_class") );
      this.arg1Offsets = getOffsets((JSONArray) relation.get("arg1_span_list"));
      this.arg2Offsets = getOffsets((JSONArray) relation.get("arg2_span_list"));
      if (relation.get("learnit_pattern") != null)
        this.pattern = Optional.of(getListOfPatterns((JSONArray)relation.get("learnit_pattern")));
      else
        this.pattern = Optional.absent();
      if (relation.get("confidence") != null)
        this.confidence = Optional.of((Double) relation.get("confidence"));
      else
        this.confidence = Optional.absent();
      if (relation.get("model") != null)
        this.model = Optional.of((String) relation.get("model"));
      else
        this.model = Optional.absent();
    }
    RelationByOffset(String docId,EventEventRelationMention eventEventRelationMention){
      this.relation = null;
      this.docID = docId;
      EventMention leftEventMention = ((EventEventRelationMention.EventMentionArgument) eventEventRelationMention.leftEventMention()).eventMention();
      EventMention rightEventMention = ((EventEventRelationMention.EventMentionArgument) eventEventRelationMention.rightEventMention()).eventMention();
      this.arg1Text = leftEventMention.span().tokenizedText().utf16CodeUnits();
      this.arg2Text = rightEventMention.span().tokenizedText().utf16CodeUnits();
      this.semanticClass = eventEventRelationMention.relationType();
      this.pattern = eventEventRelationMention.pattern();
      this.confidence = eventEventRelationMention.confidence();
      this.model = eventEventRelationMention.model();
      this.arg1Offsets = ImmutableList.of(new Pair<>((long)leftEventMention.span().startCharOffset().asInt(), (long)leftEventMention.span().endCharOffset().asInt()));
      this.arg2Offsets = ImmutableList.of(new Pair<>((long)rightEventMention.span().startCharOffset().asInt(), (long)rightEventMention.span().endCharOffset().asInt()));
    }

    @Override
    public String toString() {
      StringBuilder stringBuilder = new StringBuilder();
      stringBuilder.append("docid: " + this.docID + ", ");
      stringBuilder.append("type: " + this.semanticClass + ", ");
      for(Pair<Long, Long> pair : this.arg1Offsets)
        stringBuilder.append("<a1: " + pair.getFirst().toString() + ", " + pair.getSecond().toString() + ">, ");
      for(Pair<Long, Long> pair : this.arg2Offsets)
        stringBuilder.append("<a2: " + pair.getFirst().toString() + ", " + pair.getSecond().toString() + ">, ");
      String ret = stringBuilder.toString().trim();
      if(ret.endsWith(","))
        ret = ret.substring(0, ret.length()-1);
      return ret;
    }

    @Override
    public int hashCode() {
      // note the hashcode does not include tokenSequence in order to avoid an infinite loop with
      // TokenSequence's hashCode!
      // return Objects.hash(this.docID, this.semanticClass, this.arg1Offsets.hashCode(), this.arg2Offsets.hashCode());
      return Objects.hash(this.toString());
    }

    @Override
    public boolean equals(final Object obj) {
      // note that equality does not look at the token sequence object to avoid an infinite loop
      // with TokenSequence's equality
      if (this == obj) {
        return true;
      }
      if (obj == null || getClass() != obj.getClass()) {
        return false;
      }
      final RelationByOffset other = (RelationByOffset) obj;

      if(this.toString().equals(other.toString()))
        return true;
      else
        return false;

      /*
      if(!this.docID.equals(other.docID))
        return false;


      return Objects.equals(this.docID, other.docID)
              && Objects.equals(this.semanticClass, other.semanticClass)
              && isTwoArrayListsWithSameValues(this.arg1Offsets, other.arg1Offsets)
              && isTwoArrayListsWithSameValues(this.arg2Offsets, other.arg2Offsets);
              */
    }

    boolean isTwoArrayListsWithSameValues(List<Pair<Long, Long>> list1, List<Pair<Long, Long>> list2)
    {
      //null checking
      if(list1==null && list2==null)
        return true;
      if((list1 == null && list2 != null) || (list1 != null && list2 == null))
        return false;

      if(list1.size()!=list2.size())
        return false;
      for(Object itemList1: list1)
      {
        if(!list2.contains(itemList1))
          return false;
      }

      return true;
    }

    List<Pair<Long, Long>> getOffsets(JSONArray offsetList) {
      List<Pair<Long, Long>> results = new ArrayList<>();
      Iterator<JSONArray> iterator = offsetList.iterator();
      while (iterator.hasNext()) {
        JSONArray offsetPair = iterator.next();
        Long s = (Long) offsetPair.get(0);
        Long e = (Long) offsetPair.get(1);
        Pair<Long, Long> offsets = new Pair<>(s, e);
        results.add(offsets);
      }
      return results;
    }

    String getListOfPatterns(JSONArray learnPatterns) {
      StringBuilder stringBuilder = new StringBuilder();
      Iterator<Object> iterator = learnPatterns.iterator();
      while (iterator.hasNext()) {
        String learnitPattern = (String) iterator.next();
        stringBuilder.append("\t" + learnitPattern);
      }
      return stringBuilder.toString().trim();
    }

  }

  // Maps docid to list of relations read from json
  private HashMap<String, ArrayList<RelationByOffset>> documentRelations;
  private JSONParser parser;

  EventEventRelationCreator() {
    parser = new JSONParser();
    documentRelations = new HashMap<>();

  }

  // Adds to documentRelations
  public void loadJsonFile(File jsonFile) throws Exception{
    System.out.println("Loading " + jsonFile.getAbsolutePath());
    BufferedReader bufferedReader = null;
    try {
      bufferedReader = new BufferedReader(new FileReader(jsonFile));
      Object obj = this.parser.parse(bufferedReader);
      JSONArray jsonArray = (JSONArray) obj;
      Iterator<JSONObject> iterator = jsonArray.iterator();
      while (iterator.hasNext()) {
        JSONObject relationJson = iterator.next();
        RelationByOffset rbo = new RelationByOffset(relationJson);
        if (!documentRelations.containsKey(rbo.docID))
          documentRelations.put(rbo.docID, new ArrayList<>());
        documentRelations.get(rbo.docID).add(rbo);
      }

    } catch (Exception e) {
      throw e;
    }
    finally {
      try{
        if(bufferedReader!= null)bufferedReader.close();
      }
      catch (Exception e) {
        throw e;
      }
    }
  }

  public static void main(String[] argv) {

    // we wrap the main method in this way to
    // ensure a non-zero return value on failure
    try {
      trueMain(argv);
    } catch (Exception e) {
      e.printStackTrace();
      System.exit(1);
    }
  }

  private static void trueMain(String[] argv) throws Exception {
    EventEventRelationCreator eerc = new EventEventRelationCreator();
    final Parameters params = Parameters.loadSerifStyle(new File(argv[0]));
    final File inputSerifxmlList = params.getExistingFile("input_serifxml_list");
    final File outputDirectory = params.getCreatableDirectory("output_serifxml_directory");

    final SerifXMLLoader loader = SerifXMLLoader.builderWithDynamicTypes().build();
    final SerifXMLWriter writer = SerifXMLWriter.create();

    List<String> jsonInputs =
        params.getStringList("event_event_json_input"); // files or directories
    for (String jsonInput : jsonInputs) {
      File jif = new File(jsonInput);
      if (jif.isFile())
        eerc.loadJsonFile(jif);
      if (jif.isDirectory())
        for (File jsonFile : jif.listFiles()) {
          if (!jsonFile.isFile())
            continue;
          if (!jsonFile.getName().endsWith(".json"))
            continue;
          eerc.loadJsonFile(jsonFile);
        }
    }

    // We've loaded the relations in the json files

    for (final File inputFile : FileUtils.loadFileList(inputSerifxmlList)) {
      final DocTheory dt = loader.loadFrom(inputFile);

      DocTheory newDT = eerc.augmentDocTheoryWithCausalRelations(dt);

      File outputSerifXMLFile = new File(outputDirectory, inputFile.getName());
      writer.saveTo(newDT, outputSerifXMLFile);
    }
  }

  ArrayList<RelationByOffset> deduplicateRelations(ArrayList<RelationByOffset> relations,List<EventEventRelationMention> preExistedEER,String docId) {

    Set<String> preExistedEERStrs = new HashSet<>();
    for(EventEventRelationMention eventEventRelationMention:preExistedEER){
      RelationByOffset r1 = new RelationByOffset(docId,eventEventRelationMention);
      preExistedEERStrs.add(r1.toString());
    }
    Map<String, RelationByOffset> string2relations = new HashMap<String, RelationByOffset>();
    for (RelationByOffset r1 : relations) {
      if(preExistedEERStrs.contains(r1.toString())){
        continue;
      }
      if(!string2relations.containsKey(r1.toString())) {
        string2relations.put(r1.toString(), r1);
      }

      RelationByOffset relationByOffset = string2relations.get(r1.toString());

      if(r1.equals(relationByOffset)) {
        if (r1.confidence.isPresent() && !relationByOffset.confidence.isPresent())
          relationByOffset.confidence = r1.confidence;
        if (r1.pattern.isPresent() && !relationByOffset.pattern.isPresent())
          relationByOffset.pattern = r1.pattern;
      }

      string2relations.put(relationByOffset.toString(), relationByOffset);
    }

    return new ArrayList<RelationByOffset>(string2relations.values());
  }


  /* Requires that documentRelations be filled */
  private DocTheory augmentDocTheoryWithCausalRelations(DocTheory dt) {
    final DocTheory.Builder newDT = dt.modifiedCopyBuilder();

    ImmutableList.Builder<EventEventRelationMention> result = ImmutableList.builder();

    if(!dt.eventEventRelationMentions().isAbsent()){
      for(EventEventRelationMention eventEventRelationMention:dt.eventEventRelationMentions()){
        result.add(eventEventRelationMention);
      }
    }
    if (!documentRelations.containsKey(dt.docid().toString())) {
      newDT.eventEventRelationMentions(EventEventRelationMentions.create(result.build()));
      return newDT.build();
    }

    ArrayList<RelationByOffset> rawRelations = documentRelations.get(dt.docid().toString());

    // deduplicate relations
    ArrayList<RelationByOffset> relations = deduplicateRelations(rawRelations,result.build(),dt.docid().toString());

    for (RelationByOffset relation : relations) {

      // ICEWSEventMention objects
      List<ICEWSEventMention> allArg1sICEWS = new ArrayList<>();
      List<ICEWSEventMention> allArg2sICEWS = new ArrayList<>();

      // EventMention objects
      List<EventMention> allArg1sSerif = new ArrayList<>();
      List<EventMention> allArg2sSerif = new ArrayList<>();

      findExactMatchEventsInRelationArgsIcews(
          relation, dt.icewsEventMentions(), allArg1sICEWS, allArg2sICEWS);

      findExactMatchEventsInRelationArgs(
          relation, dt, allArg1sSerif, allArg2sSerif);

      // These will store either ICEWSEventMentions or EventMentions
      List<Object> allArg1s = new ArrayList<>();
      List<Object> allArg2s = new ArrayList<>();

      if(allArg1sSerif.size()>0){
        allArg1s.addAll(allArg1sSerif);
      }
      else{
        allArg1s.addAll(allArg1sICEWS);
      }

      if(allArg2sSerif.size()>0){
        allArg2s.addAll(allArg2sSerif);
      }
      else{
        allArg2s.addAll(allArg2sICEWS);
      }


      if (allArg1s.size() == 0 || allArg2s.size() == 0)
        continue;

      addEventPairsAsCausal(result, allArg1s, allArg2s, relation);

    }

    newDT.eventEventRelationMentions(EventEventRelationMentions.create(result.build()));
    return newDT.build();
  }

  void addEventPairsAsCausal(
          ImmutableList.Builder<EventEventRelationMention> results,
          List<Object> allArg1s, List<Object> allArg2s, RelationByOffset relation)
  {
    for (Object arg1 : allArg1s) {
      for (Object arg2 : allArg2s) {
        EventEventRelationMention.Argument leftArg = makeArgument(arg1, "arg1");
        EventEventRelationMention.Argument rightArg = makeArgument(arg2, "arg2");
        final EventEventRelationMention eerm = new EventEventRelationMention.Builder()
            .relationType(relation.semanticClass)
            .leftEventMention(leftArg)
            .rightEventMention(rightArg)
            .confidence(relation.confidence)
            .pattern(relation.pattern)
            .model(relation.model)
            .build();
        results.add(eerm);
      }
    }
  }

  EventEventRelationMention.Argument makeArgument(Object objectArg, String role) {
    if (objectArg instanceof ICEWSEventMention) {
      EventEventRelationMention.Argument arg =
          new EventEventRelationMention.ICEWSEventMentionArgument(
              (ICEWSEventMention) objectArg, Symbol.from(role));
      return arg;
    }

    if (objectArg instanceof EventMention) {
      EventEventRelationMention.Argument arg =
          new EventEventRelationMention.EventMentionArgument(
              (EventMention) objectArg, Symbol.from(role));
      return arg;
    }

    return null;
  }

  void findExactMatchEventsInRelationArgs(
      final RelationByOffset relation, final DocTheory dt,
      List<EventMention> allArg1s, List<EventMention> allArg2s)
  {
    for (Pair<Long, Long> offset : relation.arg1Offsets)
      allArg1s.addAll(findExactMatchEventsInSpan(offset, dt));
    for (Pair<Long, Long> offset : relation.arg2Offsets)
      allArg2s.addAll(findExactMatchEventsInSpan(offset, dt));
  }

  Collection<EventMention> findExactMatchEventsInSpan(
      Pair<Long, Long> offset, final DocTheory dt)
  {
    Collection<EventMention> results = new ArrayList<>();
    for (SentenceTheory st : dt.nonEmptySentenceTheories()) {
      for (EventMention em : st.eventMentions()) {
        int event_start = em.anchorNode().span().startCharOffset().asInt();
        int event_end = em.anchorNode().span().endCharOffset().asInt();
        if (offset.getFirst().intValue() == event_start && offset.getSecond().intValue() == event_end)
          results.add(em);
      }
    }
    return results;
  }

  void findExactMatchEventsInRelationArgsIcews(
      final RelationByOffset relation, final ICEWSEventMentions icewsEventMentions,
      List<ICEWSEventMention> allArg1s, List<ICEWSEventMention> allArg2s)
  {
    for (Pair<Long, Long> offset : relation.arg1Offsets)
      allArg1s.addAll(findExactMatchInPropositions(offset, icewsEventMentions));
    for (Pair<Long, Long> offset : relation.arg2Offsets)
      allArg2s.addAll(findExactMatchInPropositions(offset, icewsEventMentions));
  }

  Collection<ICEWSEventMention> findExactMatchInPropositions(
      Pair<Long, Long> offset, ICEWSEventMentions icewsEventMentions)
  {
    Collection<ICEWSEventMention> results = new ArrayList<>();

    for (ICEWSEventMention iem : icewsEventMentions.asList()) {
      if (iem.propositions().size() == 0)
        continue;

      // First prop is typically the "best" one for relation purposes
      Proposition p = iem.propositions().get(0);
      if (!p.predHead().isPresent())
        continue;
      int prop_start = p.predHead().get().span().startCharOffset().asInt();
      int prop_end = p.predHead().get().span().endCharOffset().asInt();
      if (offset.getFirst().intValue() == prop_start && offset.getSecond().intValue() == prop_end)
        results.add(iem);
    }
    return results;
  }

}
