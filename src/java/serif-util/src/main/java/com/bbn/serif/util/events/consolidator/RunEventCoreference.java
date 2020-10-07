package com.bbn.serif.util.events.consolidator;

import com.bbn.bue.common.parameters.Parameters;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.bue.geonames.GeonamesException;
import com.bbn.serif.io.SerifIOUtils;
import com.bbn.serif.io.SerifXMLLoader;
import com.bbn.serif.io.SerifXMLWriter;
import com.bbn.serif.theories.DocTheory;
import com.bbn.serif.theories.Event;
import com.bbn.serif.theories.EventMention;
import com.bbn.serif.theories.Events;
import com.bbn.serif.util.events.consolidator.common.DocumentInfo;
import com.bbn.serif.util.events.consolidator.common.EventCandidate;
import com.bbn.serif.util.events.consolidator.coreference.DocumentSieve;
import com.bbn.serif.util.events.consolidator.coreference.SameSentenceSieve;
import com.bbn.serif.util.events.consolidator.coreference.SieveKnowledge;

import com.google.common.base.Charsets;
import com.google.common.base.Optional;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.io.Files;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

public class RunEventCoreference {
  private static final Logger log = LoggerFactory.getLogger(RunEventCoreference.class);




  private static ImmutableList<ImmutableList<EventCandidate>> getTypedEventCandidatesForEachSentence(final DocTheory doc) {
    final ImmutableList.Builder<ImmutableList<EventCandidate>> ret = ImmutableList.builder();

    for(int i=0; i<doc.numSentences(); i++) {
      final ImmutableList.Builder<EventCandidate> sentenceEvents = ImmutableList.builder();
      for(final EventMention em : doc.sentenceTheory(i).eventMentions()) {
        if(em.type().asString().compareTo("Event")!=0) {
          sentenceEvents.add(new EventCandidate(doc, em.type(), ImmutableList.of(em)));
        }
      }
      ret.add(sentenceEvents.build());
    }

    return ret.build();
  }

  private static ImmutableList<ImmutableList<EventCandidate>> getUntypedEventCandidatesForEachSentence(final DocTheory doc) {
    final ImmutableList.Builder<ImmutableList<EventCandidate>> ret = ImmutableList.builder();

    for(int i=0; i<doc.numSentences(); i++) {
      final ImmutableList.Builder<EventCandidate> sentenceEvents = ImmutableList.builder();
      for(final EventMention em : doc.sentenceTheory(i).eventMentions()) {
        if(em.type().asString().compareTo("Event")==0) {
          sentenceEvents.add(new EventCandidate(doc, em.type(), ImmutableList.of(em)));
        }
      }
      ret.add(sentenceEvents.build());
    }

    return ret.build();
  }

  public static DocTheory sieveEventCoreference(final DocTheory doc, final SameSentenceSieve sameSentenceSieve, final DocumentSieve documentSieve) {

    final ImmutableList<ImmutableList<EventCandidate>> eventCandidatesForEachSentence = getTypedEventCandidatesForEachSentence(doc);
    final ImmutableList<ImmutableList<EventCandidate>> untypedEventCandidatesForEachSentence = getUntypedEventCandidatesForEachSentence(doc);  // Generic events

    final int numberOfSentences = doc.numSentences();
    //assert numberOfSentences == eventCandidatesForEachSentence.size();

    int count1 = 0;
    for(final ImmutableList<EventCandidate> candidates : eventCandidatesForEachSentence) {
      for(final EventCandidate cand : candidates) {
        count1 += cand.eventMentions().size();
      }
    }

    final ImmutableList.Builder<ImmutableList<EventCandidate>> eventsGroupedBySentenceBuilder = ImmutableList.builder();

    for(int sentenceIndex=0; sentenceIndex<numberOfSentences; sentenceIndex++) {
      //final SentenceTheory currentSentenceTheory = doc.sentenceTheory(sentenceIndex);
      final ImmutableList<EventCandidate> newEventCandidates = sameSentenceSieve.runSieve(doc, eventCandidatesForEachSentence.get(sentenceIndex));
      //final SentenceTheory.Builder sentBuilder = currentSentenceTheory.modifiedCopyBuilder();

      //for(final EventCandidate eventCandidate : newEventCandidates) {
      //  events.add(eventCandidate.toEvent());
      //}

      eventsGroupedBySentenceBuilder.add(newEventCandidates.asList());
    }

    int count2 = 0;
    for(final ImmutableList<EventCandidate> candidates : eventsGroupedBySentenceBuilder.build()) {
      for(final EventCandidate cand : candidates) {
        count2 += cand.eventMentions().size();
      }
    }

    //for(final ImmutableSet<EventCandidate> ems : eventCandidatesForEachSentence) {
    //  for(final EventCandidate eventCandidate : ems) {
    //    events.add(eventCandidate.toEvent());
    //  }
    //}

    final ImmutableList<EventCandidate> eventsCandidates = documentSieve.combineEventFramesAcrossSentences(doc, eventsGroupedBySentenceBuilder.build());

    int count3 = 0;
    for(final EventCandidate cand : eventsCandidates) {
      count3 += cand.eventMentions().size();
    }
    System.out.println("COUNTS " + count1 + " " + count2 + " " + count3);

    final ImmutableList.Builder<Event> events = ImmutableList.builder();
    for(final EventCandidate eventCandidate : eventsCandidates) {
      events.add(eventCandidate.toEvent());
    }
    for(final ImmutableList<EventCandidate> cands : untypedEventCandidatesForEachSentence) {
      for(final EventCandidate cand : cands) {
        events.add(cand.toEvent());
      }
    }

    final DocTheory.Builder docBuilder = doc.modifiedCopyBuilder();
    docBuilder.events(new Events(events.build()));
    return docBuilder.build();

    //return doc;
  }

  private static ImmutableList<String> printEventInfo(final DocTheory doc) {
    final ImmutableList.Builder<String> ret = ImmutableList.builder();

    ret.add("==== DOC " + doc.docid().asString() + " ====");
    for(final Event event : doc.events()) {
      ret.add("<Event>");
      for(final EventMention em : event.eventMentions()) {
        final StringBuilder s = new StringBuilder();
        s.append(em.type().asString());
        s.append(":");
        s.append("<" + em.anchorNode().head().span().text().toString() + ">");
        for(final EventMention.Argument arg : em.arguments()) {
          s.append("\t");
          s.append(arg.role().asString());
          s.append(":");
          s.append("[" + arg.span().text().toString() + "]");
        }
        s.append("\n\t");
        s.append(em.sentenceTheory(doc).span().toString());
        ret.add(s.toString());
      }
      ret.add("</Event>\n");
    }

    return ret.build();
  }

  public static Parameters prepareEventCoreferenceParams(final String wordnetDir, final String sieveResourceDir, final String geonamesFile) {
    final ImmutableMap.Builder<String, String> paramsMap = ImmutableMap.builder();

    paramsMap.put("wordnet_dir", wordnetDir);
    paramsMap.put("language", "English");
    paramsMap.put("connective.comparisonContrast", sieveResourceDir + "/connective.comparisonContrast.txt");
    paramsMap.put("connective.temporalSynchronous", sieveResourceDir + "/connective.temporalSynchronous.txt");
    paramsMap.put("connective.cause", sieveResourceDir + "/connective.cause.txt");
    paramsMap.put("connective.prevention", sieveResourceDir + "/connective.prevention.txt");
    paramsMap.put("sieve.uniqueEventRoles", sieveResourceDir + "/uniqueEventRoles.txt");
    paramsMap.put("kbpEvents.sherlock.geonames.dbFile", geonamesFile);
    paramsMap.put("blockHTTP", "true");
    paramsMap.put("blockLongNames", "true");
    paramsMap.put("resolveNamesLocally", "true");
    paramsMap.put("useLocalCASForDescs", "true");

    return Parameters.fromMap(paramsMap.build());
  }

  public static void main (String [] args)
      throws IOException, GeonamesException, ClassNotFoundException {
    final String paramFilename = args[0];

    final Parameters params = Parameters.loadSerifStyle(new File(paramFilename));
    log.info(params.dump());

    List<File> filesToProcess = new ArrayList<File>();
    final ImmutableList<String> serifXmlFilePaths = params.getFileAsStringList("serifxml.list");
    for(String strFile : serifXmlFilePaths)
      filesToProcess.add(new File(strFile));

    final String strOutputDir = params.getCreatableDirectory("serifxml.output_dir").getAbsolutePath();

    SerifXMLWriter serifXMLWriter = SerifXMLWriter.create();
    SerifXMLLoader serifXMLLoader = SerifXMLLoader.builderWithDynamicTypes().build();


    final SieveKnowledge sieveKnowledge = SieveKnowledge.from(params);

    //final SentenceInfoCache sentenceInfoCache = new SentenceInfoCache(language, stemmer);

    //final ConnectiveInfo connectiveInfo = new ConnectiveInfo(Connectives.from(params), sentenceInfoCache);

    final Optional<String> logDir = params.getOptionalString("logdir");
    //final Optional<CharSink> sink = params.isPresent("logfile")? Optional.of(Files.asCharSink(params.getCreatableFile("logfile"), Charsets.UTF_8)) : Optional.absent();

    for (final DocTheory inputDoc : SerifIOUtils.docTheoriesFromFiles(filesToProcess, serifXMLLoader)) {
      final Symbol docId = inputDoc.docid();

      //final PlaceContainmentCache placeContainmentCache = new PlaceContainmentCache(sieveKnowledge.geonames(), sieveKnowledge.cas(), inputDoc);

      final DocumentInfo documentInfo = new DocumentInfo(sieveKnowledge, inputDoc);

      //sieveKnowledge.loadDocument(inputDoc);

      //final SentenceInfoCache sentenceInfoCache = SentenceInfoCache.from(sieveKnowledge, documentInfo);
      //sentenceInfoCache.loadDocument(inputDoc);
      //placeContainmentCache.loadDocument(inputDoc);
      final SameSentenceSieve sameSentenceSieve = new SameSentenceSieve(sieveKnowledge, documentInfo);
      final DocumentSieve documentSieve = new DocumentSieve(sieveKnowledge, documentInfo);

      final DocTheory docTheoryWithNewEvents = sieveEventCoreference(inputDoc, sameSentenceSieve, documentSieve);

      String strOutputSerifXml = strOutputDir + "/" + docId.asString() + ".xml";
      serifXMLWriter.saveTo(docTheoryWithNewEvents, strOutputSerifXml);

      if(logDir.isPresent()) {
        final ImmutableList<String> eventInfoLines = printEventInfo(docTheoryWithNewEvents);
        final String logfile = logDir.get() + "/" + docId.asString() + ".log";
        Files.asCharSink(new File(logfile), Charsets.UTF_8).writeLines(eventInfoLines);
      }

    }


  }

}
