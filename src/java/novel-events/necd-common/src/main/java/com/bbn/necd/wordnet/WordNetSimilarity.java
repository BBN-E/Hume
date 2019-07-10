package com.bbn.necd.wordnet;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.nlp.banks.wordnet.IWordNet;
import com.bbn.nlp.banks.wordnet.WordNetPOS;
import com.bbn.nlp.banks.wordnet.WordNetSynset;
import com.google.common.annotations.Beta;
import com.google.common.base.Optional;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Queues;
import com.google.common.collect.Sets;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Deque;
import java.util.Set;

import static com.google.common.base.Preconditions.checkNotNull;
import static com.google.common.base.Preconditions.checkState;

/**
 * Computes similarity metrics over WordNet.
 */
@Beta
public final class WordNetSimilarity {

  private static final Logger log = LoggerFactory.getLogger(WordNetSimilarity.class);

  private final IWordNet wn;
  private final WordNetPOS pos;
  private final WordNetGraph graph;

  private WordNetSimilarity(final IWordNet wordNet, final WordNetPOS pos, final WordNetGraph graph) {
    this.wn = wordNet;
    this.pos = pos;
    this.graph = graph;
  }

  /**
   * Create a similarity object from WordNet. Creation of this object requires building a graph over all of WordNet and
   * computing many graph distances, so creation will take a substantial amount of time (minutes).
   *
   * @param wordNet the WordNet
   * @param pos     the part of speech
   * @return the similarity
   */
  public static WordNetSimilarity fromWordNet(final IWordNet wordNet, final WordNetPOS pos) {
    final WordNetGraph graph = WordNetGraph.fromWordNet(checkNotNull(wordNet), checkNotNull(pos));
    return new WordNetSimilarity(wordNet, pos, graph);
  }

  /**
   * Returns the greatest distance from a synset to the root of the hypernym graph.
   */
  public int graphHeight() {
    return graph.height();
  }

  /**
   * Returns the least common subsumer of two words. The least common subsumer is defined as the synset furthest from
   * the root that dominates synsets of both stems.
   *
   * @param stem1 the first stem
   * @param stem2 the second stem
   * @return the least common subsumer of the stems or {@link Optional#absent()} if there is none
   */
  public Optional<WordNetSynset> leastCommonSubsumer(final Symbol stem1, final Symbol stem2) {
    // Find the intersection of all possible hypernyms
    final Set<WordNetSynset> common = commonHypernyms(stem1, stem2);
    // Find the common hypernym with the furthest distance from the root
    int maxDistance = 0;
    WordNetSynset leastCommon = null;
    for (WordNetSynset synset : common) {
      final Optional<Integer> optDistance = graph.shortestDistanceToRoot(synset);
      if (optDistance.isPresent()) {
        if (optDistance.get() > maxDistance) {
          maxDistance = optDistance.get();
          leastCommon = synset;
        }
      } else {
        // If this occurs, the graph has not been created correctly
        throw new WordNetSimilarityException(String.format("No path between synset '%s' and root", synset));
      }
    }

    if (leastCommon == null) {
      return Optional.absent();
    } else {
      return Optional.of(leastCommon);
    }
  }

  /**
   * Returns the shortest distance between a stem and a synset. In order to be comparable with standard metrics which
   * record distance as synset-to-synset (not stem to synset), the stem-synset distance is treated as zero-length. As
   * a result, the distance between a stem and a synset it is a member of will be zero.
   *
   * @param stem   the stem
   * @param synset the synset
   * @return the distance between them, which may be a positive number, zero, or {@link Optional#absent()}
   */
  public Optional<Integer> shortestDistance(final Symbol stem, final WordNetSynset synset) {
    Optional<Integer> result = graph.shortestDistance(stem, synset);
    // We remove one from the shortest distance to offset the fact that the stem -> synset edge should be zero-weight
    if (result.isPresent()) {
      result = Optional.of(result.get() - 1);
    }
    return result;
  }

  /**
   * Returns the distance between a stem and the root. As the distance between a stem and a synset it is a member of is
   * zero (see {@link #shortestDistance(Symbol, WordNetSynset)}), this is effectively the distance between the synset
   * of the stem closest to the root and the root.
   *
   * @param stem the stem
   * @return the distance between the stem and root, which may be a positive number or {@link Optional#absent()}
   * @see #distanceToRoot(WordNetSynset)
   */
  public Optional<Integer> distanceToRoot(final Symbol stem) {
    Optional<Integer> result = graph.shortestDistanceToRoot(stem);
    // We remove one from the shortest distance to offset the fact that the stem -> synset edge should be zero-weight
    if (result.isPresent()) {
      result = Optional.of(result.get() - 1);
    }
    return result;
  }

  /**
   * Returns the distance between a synset and the root.
   *
   * @param synset the synset
   * @return the distance between the synset and the root, which may be a positive number or {@link Optional#absent()}
   * @see #distanceToRoot(Symbol)
   */
  public Optional<Integer> distanceToRoot(final WordNetSynset synset) {
    return graph.shortestDistanceToRoot(synset);
  }

  /**
   * Returns the set of hypernyms common to two words.
   *
   * @param stem1 the first stem
   * @param stem2 the second stem
   * @return the set of common hypernyms, which may be empty
   */
  public Set<WordNetSynset> commonHypernyms(final Symbol stem1, final Symbol stem2) {
    Set<WordNetSynset> hypernyms1 = allStemHypernyms(stem1, pos);
    Set<WordNetSynset> hypernyms2 = allStemHypernyms(stem2, pos);
    return Sets.intersection(hypernyms1, hypernyms2);
  }

  /**
   * Returns the set of synsets common to two words.
   *
   * @param stem1 the first stem
   * @param stem2 the second stem
   * @return the set of common synsets, which may be empty
   */
  public ImmutableSet<WordNetSynset> sharedSynsets(final Symbol stem1, final Symbol stem2) {
    final ImmutableSet<WordNetSynset> stem1Synsets = ImmutableSet.copyOf(wn.getAllSynsetsOfStem(stem1, pos));
    final ImmutableSet<WordNetSynset> stem2Synsets = ImmutableSet.copyOf(wn.getAllSynsetsOfStem(stem2, pos));
    return Sets.intersection(stem1Synsets, stem2Synsets).immutableCopy();
  }

  /**
   * Return the Wu and Palmer ConSim (conceptual similarity) measure for two stems in WordNet. This measure is defined
   * for nouns and verbs. If the measure is undefined for a word pair, consider using {@link #wuPalmerMinConSim()} to
   * get a default value for the minimum similarity possible.
   * <p/>
   * The similarity measure is computed for words (C1, C2) as:
   * (2 * N3) / (N1 + N2 + 2 * N3),
   * where for a least common subsumer C3, N1 is the shortest path for (C1, C3), N2 for (C2, C3), and N3 for (C3, root).
   * Since not all verbs have a least common subsumer, it is assumed there is a node just below the root that is
   * a subsumer to all verbs.
   *
   * The measure is given in the paper:
   * Wu, Zhibiao, and Martha Palmer. "Verbs semantics and lexical selection."
   * In Proceedings of the 32nd annual meeting on Association for Computational Linguistics, pp. 133-138. 1994.
   *
   * @param stem1 the first stem
   * @param stem2 the second stem
   * @return the similarity, if defined, {@link Optional#absent()} otherwise
   * @see #wuPalmerMinConSim()
   */
  public Optional<Double> wuPalmerConSim(final Symbol stem1, final Symbol stem2) {
    checkState(pos.equals(WordNetPOS.NOUN) || pos.equals(WordNetPOS.VERB),
        "ConSim can only be computed on nouns and verbs");
    if (wn.getAllSynsetsOfStem(stem1, pos).isEmpty() || wn.getAllSynsetsOfStem(stem2, pos).isEmpty()) {
      return Optional.absent();
    }
    final Optional<WordNetSynset> optSubsumer = leastCommonSubsumer(stem1, stem2);
    switch(pos) {
      case NOUN: {
        // For nouns this can only happen if one of the words isn't in WordNet
        if (!optSubsumer.isPresent()) {
          log.error("No common subsumer for {} and {}: one of them is not a stem of pos {}",
              stem1, stem2, pos);
          return Optional.absent();
        }
        final WordNetSynset subsumer = optSubsumer.get();
        final Optional<Integer> n1 = shortestDistance(stem1, subsumer);
        final Optional<Integer> n2 = shortestDistance(stem2, subsumer);
        final Optional<Integer> n3 = distanceToRoot(subsumer);
        if (!n1.isPresent() || !n2.isPresent() || !n3.isPresent()) {
          throw new WordNetSimilarityException(
              "WordNet hypernym graph has been improperly constructed: bad connectivity between stems, subsumer, and root");
        }
        return Optional.of(computeWuPalmerConsim(n1.get(), n2.get(), n3.get()));
      }
      case VERB: {
        // In the case of verbs, we may need to hallucinate a common subsumer.
        final Optional<Integer> n1;
        final Optional<Integer> n2;
        final Optional<Integer> n3;
        if (optSubsumer.isPresent()) {
          final WordNetSynset subsumer = optSubsumer.get();
          n1 = shortestDistance(stem1, subsumer);
          n2 = shortestDistance(stem2, subsumer);
          n3 = distanceToRoot(subsumer);
        } else {
          // Hallucinate a common subsumer.
          n1 = distanceToRoot(stem1);
          n2 = distanceToRoot(stem2);
          n3 = Optional.of(0);
        }
        if (!n1.isPresent() || !n2.isPresent() || !n3.isPresent()) {
          throw new WordNetSimilarityException(
              "WordNet hypernym graph has been improperly constructed: bad connectivity between stems, subsumer, and root");
        }
        // To account for the fake subsumer, we add one to the distance to root.
        return Optional.of(computeWuPalmerConsim(n1.get(), n2.get(), n3.get() + 1));
      }
      default: {
        throw new IllegalArgumentException("Unhandled case: " + pos);
      }
    }
  }

  /**
   * Returns the minimum value for similarity between two words estimated by the current graph.
   *
   * To compute this, it is assumed that the subsumer node is just below root and the two stems are the furthest
   * distance possible in this graph from that subsumer node. This effectively gives a distance between the words and
   * root of one more than could be observed in the graph, so this returns a similarity guaranteed to be lower than that
   * of any two words actually present in the graph. Mathematically, the minimum similarity assumes
   * (c1 = c2 = height, c3 = 1), so the equation reduces to:
   * 2 / (2 * height + 2)
   *
   * For verbs, the height is computed as one more than the actual height of the graph, because we pretend there is a
   * common subsumer for all verbs that is just below the root.
   *
   * @return the minimum similarity for this similarity graph
   */
  public double wuPalmerMinConSim() {
    checkState(pos.equals(WordNetPOS.NOUN) || pos.equals(WordNetPOS.VERB),
        "ConSim can only be computed on nouns and verbs");
    int height = graphHeight();
    if (pos.equals(WordNetPOS.VERB)) {
        // For verbs, since we have a fake subsumer, the maximum effective height is one greater than the actual height
        height++;
    }
    return computeWuPalmerConsim(height, height, 1);
  }

  private static double computeWuPalmerConsim(final int n1, final int n2, final int n3) {
    // Equation: (2 * N3) / (N1 + N2 + 2 * N3)
    return (2.0 * n3) / (n1 + n2 + 2 * n3);
  }


  private ImmutableSet<WordNetSynset> allStemHypernyms(final Symbol stem, final WordNetPOS pos) {
    final ImmutableSet.Builder<WordNetSynset> hypernyms = ImmutableSet.builder();
    // Create a queue of synsets to explore
    final Deque<WordNetSynset> synsetQueue = Queues.newArrayDeque(wn.getAllSynsetsOfStem(stem, pos));
    while (!synsetQueue.isEmpty()) {
      final WordNetSynset synset = synsetQueue.pop();
      hypernyms.add(synset);
      synsetQueue.addAll(wn.getHypernymsOfSynset(synset));
    }
    return hypernyms.build();
  }

  public static class WordNetSimilarityException extends RuntimeException {
    public WordNetSimilarityException(final String msg) {
      super(msg);
    }
  }
}
