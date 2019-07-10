package com.bbn.necd.event.bin;

import com.bbn.bue.common.files.FileUtils;
import com.bbn.bue.common.io.GZIPByteSource;
import com.bbn.necd.event.propositions.PropositionUtils;
import com.bbn.serif.io.SerifXMLLoader;
import com.bbn.serif.theories.DocTheory;
import com.bbn.serif.theories.Mention;
import com.bbn.serif.theories.Proposition;
import com.bbn.serif.theories.SentenceTheory;
import com.bbn.serif.theories.actors.ActorMention;
import com.google.common.base.Charsets;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Iterables;
import com.google.common.collect.Sets;
import com.google.common.io.Files;

import java.io.File;
import java.io.IOException;
import java.util.List;

import static com.bbn.necd.event.TheoryUtils.actorMentionMatchesMentions;
import static com.bbn.necd.event.TheoryUtils.actorMentionMatchesSentence;
import static com.google.common.base.Predicates.in;
import static com.google.common.base.Predicates.not;

/**
 * A simple utility for dumping out proposition structures.
 */
public final class SerifPropsExplorer {

  private static final String STARS = new String(new char[80]).replace("\0", "*");

  public static void main(String[] args) throws IOException {
    if (args.length != 1) {
      System.err.println("A file list of zipped SerifXML documents should be the sole argument");
      System.exit(1);
    }

    // Load
    final List<File> inputFiles = FileUtils.loadFileList(new File(args[0]));
    final SerifXMLLoader loader = SerifXMLLoader.builderFromStandardACETypes().allowSloppyOffsets().build();
    for (final File inputFile : inputFiles) {
      System.out.println(STARS);
      final DocTheory dt = loader.loadFrom(
          GZIPByteSource.fromCompressed(Files.asByteSource(inputFile)).asCharSource(Charsets.UTF_8));
      System.out.println(dt.docid());

      // Get document-level ActorMentions
      final ImmutableList<ActorMention> docActorMentions = ImmutableList.copyOf(dt.actorMentions());

      // Look at the props
      for (final SentenceTheory st : dt.nonEmptySentenceTheories()) {
        // Filter down ActorMentions to the sentence
        final ImmutableList<ActorMention> sentenceActorMentions = ImmutableList.copyOf(
            Iterables.filter(docActorMentions, actorMentionMatchesSentence(dt, st)));

        final ImmutableSet<Proposition> props = ImmutableSet.copyOf(st.propositions());
        // Select verbs
        final ImmutableSet<Proposition> verbs = ImmutableSet.copyOf(
            Sets.filter(props, PropositionUtils.isVerbalProposition()));
        // Filter out ones that are the argument of another verb
        final ImmutableSet<Proposition> propArgs = PropositionUtils.propositionalArguments(props);
        final ImmutableSet<Proposition> rootVerbs =
            ImmutableSet.copyOf(Sets.filter(verbs, not(in(propArgs))));

        // Work on each root verb
        boolean printed = false;
        for (final Proposition prop : rootVerbs) {
          // Get the child mentions of the root
          final ImmutableList<Mention> mentions = PropositionUtils.mentionArguments(prop);
          // Get the actor mentions that intersect with the mentions
          final ImmutableList<ActorMention> actorMentions = ImmutableList.copyOf(
              Iterables.filter(sentenceActorMentions, actorMentionMatchesMentions(mentions)));

          if (!actorMentions.isEmpty()) {
            if (!printed) {
              System.out.println(st.tokenSpan().tokenizedText(dt));
              printed = true;
            }
            System.out.println(prop);
            for (final ActorMention actorMention : actorMentions) {
              System.out.println(actorMention.mention().tokenSpan().tokenizedText(dt));
            }
            System.out.println();
          }
        }
        if (printed) {
          System.out.println();
        }
      }
    }
  }
}
