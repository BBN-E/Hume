package com.bbn.serif.util;

import com.bbn.bue.common.files.FileUtils;
import com.bbn.bue.common.parameters.Parameters;
import com.bbn.bue.common.parameters.ParametersModule;
import com.bbn.serif.SerifEnvironmentM;
import com.bbn.serif.io.SerifXMLLoader;
import com.bbn.serif.io.SerifXMLWriter;
import com.bbn.serif.theories.DocTheory;
import com.bbn.serif.theories.EventMention;
import com.bbn.serif.theories.EventMentions;
import com.bbn.serif.theories.Events;
import com.bbn.serif.theories.SentenceTheory;
import com.bbn.serif.types.Genericity;
import com.bbn.serif.types.Modality;

import com.google.common.base.Charsets;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.Lists;
import com.google.common.io.Files;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;
import java.util.List;

import static com.google.common.base.Preconditions.checkArgument;
import static com.google.common.base.Preconditions.checkNotNull;

/**
 * Removes EventMentions and document-level Events from SerifXML files.
 */
public final class StripEvents2 {

  private static final Logger log = LoggerFactory.getLogger(StripEvents.class);

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

  private static void trueMain(String[] argv) throws IOException {
    final Parameters params = Parameters.loadSerifStyle(new File(argv[0]));
    final File inputFileList = params.getExistingFile("inputFileList");
    final File outputDirectory = params.getAndMakeDirectory("outputDirectory");
    final File strippedFileList = params.getCreatableFile("strippedFileList");
    final boolean keepTriggers = params.getBoolean("keepTriggers");
    final boolean keepArguments = params.getBoolean("keepArguments");

    final SerifXMLLoader loader = SerifXMLLoader.builderWithDynamicTypes().build();
    final SerifXMLWriter writer = SerifXMLWriter.create();

    checkArgument(!keepArguments || keepTriggers,
        "If keepArguments is true, keepTriggers must be also");

    log.info(
        "Stripping events from files in list {}; writing results to directory {} with output manifest {}",
        inputFileList, outputDirectory, strippedFileList);

    final List<String> outputPaths = Lists.newArrayList();

    for (final File inputFile : FileUtils.loadFileList(inputFileList)) {
      final DocTheory dt = loader.loadFrom(inputFile);
      final DocTheory.Builder newDT = dt.modifiedCopyBuilder();
      newDT.events(Events.absent());
      for (int sentIdx = 0; sentIdx < dt.numSentences(); ++sentIdx) {
        final SentenceTheory initialSent = dt.sentenceTheory(sentIdx);
        newDT.replacePrimarySentenceTheory(initialSent,
            stripEvents(initialSent, keepTriggers, keepArguments));
      }

      String outFilename = dt.docid().toString();
      if(dt.docid().toString().lastIndexOf("/")!=-1) {
        outFilename = dt.docid().toString().substring( dt.docid().toString().lastIndexOf("/")+1 );
      }
      if(!outFilename.endsWith(".xml")) {
        outFilename = outFilename.concat(".xml");
      }

      final File outputFile = new File(outputDirectory, outFilename);
      log.info("Stripping events from {}, writing to {}", inputFile, outputFile);
      writer.saveTo(newDT.build(), outputFile);
      outputPaths.add(outputFile.getAbsolutePath());
    }
    log.info("Writing list of {} stripped files to {}", outputPaths.size(), strippedFileList);
    Files.asCharSink(strippedFileList, Charsets.UTF_8).writeLines(outputPaths);
  }

  private static SentenceTheory stripEvents(SentenceTheory st, boolean keepTriggers,
      boolean keepArguments) {
    if (st.eventMentions().asList().isEmpty()) {
      return st;
    }
    final SentenceTheory.Builder builder = st.modifiedCopyBuilder();
    final ImmutableList.Builder<EventMention> eventMentions = ImmutableList.builder();

    if (keepTriggers) {
      for (final EventMention em : st.eventMentions()) {
        eventMentions.add(em.modifiedCopyBuilder()
            .setArguments(
                keepArguments ? em.arguments() : ImmutableList.<EventMention.Argument>of())
            .setGenericity(Genericity.SPECIFIC, 1.0)
            .setModality(Modality.ASSERTED, 1.0)
            .build());
      }
    }
    //noinspection OptionalGetWithoutIsPresent
    // we know the parse is present because it will only be absent if the eventMentions
    // are absent
    builder.eventMentions(EventMentions.create(st.eventMentions().parse().get(),
        eventMentions.build()));
    return builder.build();
  }
}
