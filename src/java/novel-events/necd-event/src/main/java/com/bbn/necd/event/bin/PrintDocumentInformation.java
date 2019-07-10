package com.bbn.necd.event.bin;

import com.bbn.bue.common.io.GZIPByteSource;
import com.bbn.bue.common.parameters.Parameters;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.common.theory.DocumentInformation;
import com.bbn.necd.common.theory.SentenceInformation;
import com.bbn.necd.event.io.CompressedFileUtils;
import com.bbn.necd.event.io.LabelWriter;
import com.bbn.nlp.WordAndPOS;
import com.bbn.serif.io.SerifXMLLoader;
import com.bbn.serif.theories.DocTheory;
import com.bbn.serif.theories.Parse;
import com.bbn.serif.theories.SentenceTheory;
import com.bbn.serif.theories.Token;

import com.google.common.base.Charsets;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableSet;
import com.google.common.io.Files;

import org.apache.commons.csv.CSVParser;
import org.apache.commons.csv.CSVRecord;
import org.apache.commons.io.FileUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;
import java.util.List;

public final class PrintDocumentInformation {
  private static final Logger log = LoggerFactory.getLogger(PrintDocumentInformation.class);

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

  public static void trueMain(final String[] argv) throws IOException {
    if (argv.length != 1) {
      System.err.println("Usage: printDocumentInformation params");
      System.exit(1);
    }
    final Parameters params = Parameters.loadSerifStyle(new File(argv[0]));
    log.info("{} run on parameters:\n{}", PrintDocumentInformation.class, params.dump());



    final ImmutableSet<Symbol> docIds = getTargetDocIds(params);


    final SerifXMLLoader loader = SerifXMLLoader.builderFromStandardACETypes().allowSloppyOffsets().build();

    final List<File> inputFiles = com.bbn.bue.common.files.FileUtils.loadFileList(params.getExistingFile("serifXmlFileList"));
    log.info("Extracting document information from {} SerifXML files", inputFiles.size());

    final ImmutableList.Builder<DocumentInformation> docsInfoBuilder = ImmutableList.builder();
    for (final File input : inputFiles) {
      final DocTheory dt = loader.loadFrom(
          GZIPByteSource.fromCompressed(Files.asByteSource(input)).asCharSource(Charsets.UTF_8));

      if(docIds.contains(dt.docid())) {
        final DocumentInformation.Builder docInfoBuilder = DocumentInformation.builder(dt.docid());
        for (final SentenceTheory st : dt.nonEmptySentenceTheories()) {
          if (st.parse().isPresent()) {
            SentenceInformation.Builder sentenceInformationBuilder =
                SentenceInformation.builder(st.sentenceNumber());
            sentenceInformationBuilder.withWordAndPOSes(toWordAndPOS(st));
            docInfoBuilder
                .withSentenceInformation(st.sentenceNumber(), sentenceInformationBuilder.build());
          }
        }
        docsInfoBuilder.add(docInfoBuilder.build());
      }
    }

    final File outputFile = params.getCreatableFile("docInfo.output");
    log.info("Writing to {}", outputFile);
    final ImmutableList<DocumentInformation> docsInfo = docsInfoBuilder.build();
    CompressedFileUtils.writeAsJson(docsInfo, outputFile);



    /*
    // following is to test that the serialization works
    final ImmutableList<DocumentInformation> deserializedDocsInfo = CompressedFileUtils.readAsJsonList(outputFile, DocumentInformation.class);

    log.info("docsInfo size={}, deserializedDocsInfo size={}", docsInfo.size(), deserializedDocsInfo.size());
    final Set<DocumentInformation> set1 = Sets.newHashSet(docsInfo);
    final Set<DocumentInformation> set2 = Sets.newHashSet(deserializedDocsInfo);
    log.info("intersection size = {}", Sets.intersection(set1, set2).size());
    log.info("symmetricDifference is empty {}", Sets
        .symmetricDifference(Sets.newHashSet(docsInfo), Sets.newHashSet(deserializedDocsInfo)).isEmpty());
    */
  }

  public static ImmutableList<WordAndPOS> toWordAndPOS(final SentenceTheory st) {
    final ImmutableList.Builder<WordAndPOS> ret = ImmutableList.builder();

    if(st.parse().isPresent()) {
      final Parse parse = st.parse().get();
      for(final Token token : parse.tokenSequence()) {
        WordAndPOS wordAndPOS = parse.toWordAndPOS(token);
        ret.add(wordAndPOS);
      }
    }

    return ret.build();
  }

  private static ImmutableSet<Symbol> getTargetDocIds(final Parameters params) throws IOException {
    final ImmutableSet.Builder<Symbol> ret = ImmutableSet.builder();

    final String labelSuffixId = params.getString("labelSuffix.id");
    final String labelSuffixPair = params.getString("labelSuffix.pair");

    final File baseDir = params.getExistingDirectory("basedir");

    for(final File file : FileUtils.listFiles(baseDir, new String[]{labelSuffixId}, true)) {
      ret.addAll(readDocIdsFromLabels(file));
    }
    for(final File file : FileUtils.listFiles(baseDir, new String[]{labelSuffixPair}, true)) {
      ret.addAll(readDocIdsFromPairLabels(file));
    }

    return ret.build();
  }


  // instanceId -> event label
  public static ImmutableSet<Symbol> readDocIdsFromPairLabels(final File infile) throws IOException {
    final ImmutableSet.Builder<Symbol> ret = ImmutableSet.builder();

    final CSVParser parser = LabelWriter.getParser(infile);
    for (CSVRecord row : parser) {
      ret.add( Symbol.from(instanceIdToDocId(row.get(0))) );
      ret.add( Symbol.from(instanceIdToDocId(row.get(1))) );
    }

    return ret.build();
  }


  public static ImmutableSet<Symbol> readDocIdsFromLabels(final File infile) throws IOException {
    final ImmutableSet.Builder<Symbol> ret = ImmutableSet.builder();

    final CSVParser parser = LabelWriter.getParser(infile);
    for (CSVRecord row : parser) {
       ret.add( Symbol.from(instanceIdToDocId(row.get(0))) );
    }

    return ret.build();
  }

  public static String instanceIdToDocId(final String id) {
    return id.substring(0, id.indexOf("["));
  }

}
