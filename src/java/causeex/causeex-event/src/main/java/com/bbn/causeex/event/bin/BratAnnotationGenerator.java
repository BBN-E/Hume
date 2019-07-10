package com.bbn.causeex.event.bin;

import com.bbn.bue.common.files.FileUtils;
import com.bbn.causeex.common.Lemmatizer;
import com.bbn.serif.io.SerifXMLLoader;
import com.bbn.serif.theories.DocTheory;
import com.bbn.serif.theories.SentenceTheory;
import com.bbn.serif.theories.SynNode;

import com.google.common.base.Charsets;
import com.google.common.collect.ImmutableList;
import com.google.common.io.Files;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.nio.charset.Charset;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;


public final class BratAnnotationGenerator {

  public static void main(final String[] argv) throws IOException {
    try {
      trueMain();
    } catch (Exception e) {
      e.printStackTrace();
      System.exit(1);
    }
  }

  private static void trueMain() throws IOException {

    final ImmutableList<File> serifXMLFiles = FileUtils
            .loadFileList(
                    Files.asCharSource(new File("/home/dakodes/cxhome/issue-63/issue-63-rj/ychan-1000.filelist"), Charsets.UTF_8));
    final ImmutableList<File> sourceFiles = FileUtils
            .loadFileList(
                    Files.asCharSource(new File("/nfs/raid87/u14/users/bmin/Expts/annotating_event_event_relations/dataset.filelist"), Charsets.UTF_8));
    Map<File, File> serifXMLToSgmFile = new HashMap<>();
    for (File serifXMLFile : serifXMLFiles) {
      final String docId = serifXMLFile.getName().substring(0, serifXMLFile.getName().lastIndexOf('.'));
      for (File sourceFile : sourceFiles) {
        if (sourceFile.getName().contains(docId)) {
          serifXMLToSgmFile.put(serifXMLFile, sourceFile);
          break;
        }
      }
    }

    final File outputDir = new File("/home/dakodes/cxhome/issue-63/issue-63-rj/1k-for-annotation");
    FileUtils.recursivelyDeleteDirectory(outputDir);
    outputDir.mkdir();

    final Lemmatizer lemmatizer = Lemmatizer.from("lemma.nv");
    final SerifXMLLoader serifXMLLoader =
            SerifXMLLoader.builderFromStandardACETypes().allowSloppyOffsets().makeAllTypesDynamic()
                    .build();
    List<String> stopwords = Files.readLines(new File(
            "/home/dakodes/cxhome/issue-63/issue-63-rj/stopwords.txt"), Charset.forName("utf-8"));

    for (File serifXMLFile : serifXMLToSgmFile.keySet()) {
      int triggerNumber = 1;
      final DocTheory dt = serifXMLLoader.loadFrom(serifXMLFile);
      String docText = dt.document().originalText().get().text();

      final String docId = serifXMLFile.getName().substring(0, serifXMLFile.getName().lastIndexOf('.'));
      BufferedWriter outputAnnFileWriter = new BufferedWriter(new FileWriter(new File(outputDir + "/" + docId + ".ann")));

      String txtFileString = com.google.common.io.Files.toString(serifXMLToSgmFile.get(serifXMLFile), Charset.forName("UTF-8"));
      for (String tag : new String[] {"TEXT", "P"}) {
        String startTag = String.format("<%s>", tag);
        String endTag = String.format("</%s>", tag);
        Matcher textMatcher = Pattern.compile(String.format("%s(.|\n)+?%s", startTag, endTag)).matcher(txtFileString);
        while (textMatcher.find()) {
          int start = textMatcher.start() + startTag.length();
          int end = textMatcher.end() - endTag.length();
          txtFileString =
                  txtFileString.substring(0, start) +
                          txtFileString.substring(start, end).replace('\n', ' ') +
                          txtFileString.substring(end);
        }
        txtFileString = txtFileString.replace(startTag + " ", startTag + "\n");
        txtFileString = txtFileString.replace(" " + startTag, "\n" + startTag);
        txtFileString = txtFileString.replace(endTag + " ", endTag + "\n");
        txtFileString = txtFileString.replace(" " + endTag, "\n" + endTag);
      }

      BufferedWriter outputTxtFileWriter = new BufferedWriter(new FileWriter(new File(outputDir + "/" + docId + ".txt")));
      outputTxtFileWriter.write(txtFileString);
      outputTxtFileWriter.close();

      for (final SentenceTheory st : dt.nonEmptySentenceTheories()) {
        final SynNode parseRoot = st.parse().get().root();
        for (int i = 0; i < parseRoot.numTerminals(); i++) {
          final SynNode node = parseRoot.nthTerminal(i);
          final String posTag = node.headPOS().asString();
          char posTagChar;
          if (posTag.startsWith("VB")) {
            posTagChar = 'v';
          } else if (posTag.matches("NNS?")) {
            posTagChar = 'n';
          } else {
            // ignore non-verbs and non-nouns
            continue;
          }
          final int triggerStartOffset = node.head().tokenSpan().startCharOffset().asInt();
          final int triggerEndOffset = node.head().tokenSpan().endCharOffset().asInt();
          final String triggerText = docText.substring(triggerStartOffset, triggerEndOffset + 1);
          if (!stopwords.contains(lemmatizer.getLemma(triggerText) + "." + posTagChar)) {
            outputAnnFileWriter.write(
                    String.format("T%d\tEvent %d %d\t%s\n",
                            triggerNumber,
                            triggerStartOffset,
                            triggerEndOffset + 1,
                            triggerText
            ));
            outputAnnFileWriter.write(
                    String.format("E%d\tEvent:T%d\n",
                            triggerNumber,
                            triggerNumber
            ));
            triggerNumber++;
          }
        }
      }
      outputAnnFileWriter.close();
    }

    for (String confFile : new String[] {"annotation.conf", "kb_shortcuts.conf", "tools.conf", "visual.conf"}) {
      Files.copy(
              new File("/nfs/raid87/u15/users/dakodes/issue-63/issue-63-rj/" + confFile),
              new File(outputDir.getAbsolutePath() + "/" + confFile)
      );
    }
  }

}