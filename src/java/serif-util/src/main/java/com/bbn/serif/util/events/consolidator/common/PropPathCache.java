package com.bbn.serif.util.events.consolidator.common;

import com.bbn.nlp.languages.Language;
import com.bbn.serif.util.events.consolidator.proputil.PropositionPath;
import com.bbn.serif.util.events.consolidator.proputil.PropositionUtils;
import com.bbn.serif.util.events.consolidator.proputil.PropositionUtils.PathNode;
import com.bbn.serif.util.events.consolidator.proputil.Stemmer;
import com.bbn.serif.theories.DocTheory;
import com.bbn.serif.theories.EventMention;
import com.bbn.serif.theories.SentenceTheory;
import com.bbn.serif.theories.SynNode;

import com.google.common.base.Optional;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableSet;

import java.io.IOException;

public final class PropPathCache {

  private final Language language;
  private final Stemmer stemmer;

  private ImmutableMap<Integer, ImmutableMap<SynNode, PathNode>> propPathMap;

  /*
  private final LoadingCache<SherlockDocument, ImmutableMap<Integer, ImmutableMap<SynNode, PathNode>>>
      propPathMap = CacheBuilder.newBuilder().maximumSize(5).build(
      new CacheLoader<SherlockDocument, ImmutableMap<Integer, ImmutableMap<SynNode, PathNode>>>() {
        @Override
        public ImmutableMap<Integer, ImmutableMap<SynNode, PathNode>> load(final SherlockDocument doc) {
          return propositionPathKnowledge(doc);
        }
      });
  */

  public PropPathCache(final Language language, final Stemmer stemmer, final DocTheory doc) throws IOException {
    this.language = language;
    this.stemmer = stemmer;
    this.propPathMap = propositionPathKnowledge(doc);
  }

  //public static PropPathCache from(final Parameters params) throws IOException {
  //  final Language language = English.getInstance();
  //  final Stemmer stemmer = EnglishWordnetStemmer.from(params);
  //  return new PropPathCache(language, stemmer);
  //}

  //public void loadDocument(final DocTheory doc) {
  //  this.propPathMap = propositionPathKnowledge(doc);
  //}



  // proposition path knowledge for each sentence
  private static ImmutableMap<Integer, ImmutableMap<SynNode, PathNode>> propositionPathKnowledge(
      final DocTheory doc) {

    final ImmutableMap.Builder<Integer, ImmutableMap<SynNode, PathNode>> ret = ImmutableMap.builder();
    for (final SentenceTheory st : doc.nonEmptySentenceTheories()) {
      final ImmutableList<PathNode> graph = PropositionUtils.constructPropositionGraph(st);
      final ImmutableMap<SynNode, PathNode> synToPathNodes = PropositionUtils.mapSynNodeToPathNode(graph);
      ret.put(st.sentenceNumber(), synToPathNodes);
    }
    return ret.build();
  }

  private Optional<ImmutableMap<SynNode, PathNode>> getPropPathKnowledgeForSentence(
      final DocTheory doc, final int sentenceNumber) {
      return Optional.fromNullable(propPathMap.get(sentenceNumber));
  }

  private Optional<Integer> propPathLength(final DocTheory doc, final SynNode anchorNode, final EventMention.Argument arg) {
    final SentenceTheory st = anchorNode.sentenceTheory(doc);
    assert anchorNode.span().sentenceTheory(doc).sentenceNumber() == arg.span().sentenceTheory(doc).sentenceNumber();

      final int sentenceNumber = st.sentenceNumber();
      final Optional<ImmutableMap<SynNode, PathNode>> sentenceProps = getPropPathKnowledgeForSentence(doc, sentenceNumber);
      final SynNode anchorHead = PropositionUtils.getTerminalHead(anchorNode);

      Optional<SynNode> argHead = Optional.absent();
      if (arg instanceof EventMention.ValueMentionArgument) {
        argHead = Optional.of(PropositionUtils.getTerminalHead(st.parse().root().get().nthTerminal(((EventMention.ValueMentionArgument) arg).valueMention().span().endIndex()).head()));
      } else if (arg instanceof EventMention.MentionArgument) {
        argHead = Optional.of(PropositionUtils.getTerminalHead(((EventMention.MentionArgument) arg).mention().head()));
      }

      if (argHead.isPresent()) {
        final PropositionPath propPath = PropositionPath.getPropPath(argHead.get(), anchorHead,
            language, stemmer, sentenceProps.get());
        final Optional<Integer> propPathLength = propPath.pathLength();
        if (propPathLength.isPresent()) {
          return propPathLength;
        } else {
          return Optional.of(-1);
        }
      } else {
        return Optional.absent();
      }
  }

  public ImmutableSet<EventMention.Argument> discardNonlocalArguments(DocTheory doc, final SynNode anchorNode, final ImmutableSet<EventMention.Argument> arguments) {
    final ImmutableSet.Builder<EventMention.Argument> ret = ImmutableSet.builder();

    for (final EventMention.Argument arg : arguments) {
      final Optional<Integer> pathLen = propPathLength(doc, anchorNode, arg);
      // discard if pathLen is present and (pathLen.get()=-1 or pathLen.get()>2) else add arg to ret
      if (!(pathLen.isPresent() && (pathLen.get() == -1 || pathLen.get() > 2))) {
        ret.add(arg);
      }
    }
    return ret.build();
  }

}
