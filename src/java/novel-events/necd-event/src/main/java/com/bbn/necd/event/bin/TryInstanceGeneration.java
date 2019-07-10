package com.bbn.necd.event.bin;

import com.bbn.bue.common.files.FileUtils;
import com.bbn.bue.common.io.GZIPByteSource;
import com.bbn.bue.common.parameters.Parameters;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.common.PropositionUtils;
import com.bbn.necd.event.propositions.PropositionPathEventInstance;
import com.bbn.necd.event.propositions.PropositionPathEventInstanceGenerator;
import com.bbn.nlp.banks.wordnet.WordNet;
import com.bbn.serif.io.SerifXMLLoader;
import com.bbn.serif.theories.DocTheory;
import com.bbn.serif.theories.SynNode;
import com.google.common.base.Charsets;
import com.google.common.collect.HashMultiset;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.Multiset;
import com.google.common.io.CharSink;
import com.google.common.io.Files;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;
import java.util.List;
import java.util.concurrent.TimeUnit;

public final class TryInstanceGeneration {

 private static final Logger log = LoggerFactory.getLogger(TryInstanceGeneration.class);

  public static void main(final String[] argv) throws IOException {
    final String paramFilename = argv[0];

    final Parameters params = Parameters.loadSerifStyle(new File(paramFilename));
    log.info(params.dump());

    final List<File> inputFiles = FileUtils.loadFileList(params.getExistingFile("serifXmlFileList"));

    final PropositionPathEventInstanceGenerator generator = PropositionPathEventInstanceGenerator.from(params);

    final SerifXMLLoader loader = SerifXMLLoader.builderFromStandardACETypes().allowSloppyOffsets().build();

    final WordNet wordNet = WordNet.fromParameters(params);

    final ImmutableList.Builder<PropositionPathEventInstance> eventInstancesBuilder = ImmutableList.builder();

    log.info("Extracting event instances from {} files", inputFiles.size());
    final long startTime = System.nanoTime();
    int fileCounter = 0;
    for (final File input : inputFiles) {
      final DocTheory dt = loader.loadFrom(GZIPByteSource.fromCompressed(Files.asByteSource(input)).asCharSource(Charsets.UTF_8));
      generator.process(dt);

      fileCounter += 1;
      if((fileCounter % 100)==0) {
        log.info("Processed {} files", fileCounter);
      }
    }
    final long endTime = System.nanoTime();
    final long elapsed = endTime - startTime;
    log.info("Extraction took {} seconds ({} milliseconds per document)",
        TimeUnit.NANOSECONDS.toSeconds(elapsed),
        TimeUnit.NANOSECONDS.toMillis(elapsed) / (float) inputFiles.size());

    generator.logStatistics();

    final ImmutableList<String> missRecords = generator.getMissRecords();
    CharSink sink = Files.asCharSink(params.getCreatableFile("instanceGeneration.misses"), Charsets.UTF_8);
    sink.writeLines(missRecords, "\n");

    final ImmutableList<String> multiRecords = generator.getMultiRecords();
    CharSink multiSink = Files.asCharSink(params.getCreatableFile("instanceGeneration.multi"), Charsets.UTF_8);
    multiSink.writeLines(multiRecords, "\n");

    Multiset<Integer> pathLengths = HashMultiset.create();
    final ImmutableList.Builder<String> exampleStrings = ImmutableList.builder();

    final ImmutableList<PropositionPathEventInstance> eventInstances = generator.getGeneratedEvents();
    int egId = 1;
    for(final PropositionPathEventInstance e : eventInstances) {
      final int pathLength = e.getPropositionPath().length();
      pathLengths.add(pathLength);

      final Symbol label = e.getICEWSEventMentionInfo().get().getCode();
      final String path = e.getPropositionPath().pathAsLemmaString(wordNet).get();

      final SynNode m1Head = PropositionUtils.getTerminalHead(e.getArguments().get(0));
      final SynNode m2Head = PropositionUtils.getTerminalHead(e.getArguments().get(1));

      final String m1Hw = m1Head.headWord().asString();
      final int m1Start = m1Head.span().startIndex();
      final int m1End = m1Head.span().endIndex();

      final String m2Hw = m2Head.headWord().asString();
      final int m2Start = m2Head.span().startIndex();
      final int m2End = m2Head.span().endIndex();

      // CEL: Disabled because it depends on participants which are not serializable
      /*
      final ImmutableList<ICEWSEventMention.ICEWSEventParticipant> participants = e.getICEWSEventMentionInfo().get().getParticipants();
      final String a1Role = participants.get(0).role().asString();
      final String a2Role = participants.get(1).role().asString();
      */

      // CEL: Removed a1Role and a2Role from this because they aren't available right now
      exampleStrings.add(egId + " " + label.asString() + " " + m1Start+":"+m1End+":"+m1Hw + " " + m2Start+":"+m2End+":"+m2Hw + " " + path);

      egId += 1;
    }
    for(final Integer pathLength : pathLengths.elementSet()) {
      log.info("Path length {} has count {}", pathLength, pathLengths.count(pathLength));
    }

    CharSink exampleSink = Files.asCharSink(params.getCreatableFile("instanceGeneration.examples"), Charsets.UTF_8);
    exampleSink.writeLines(exampleStrings.build(), "\n");

  }


}
