package com.bbn.necd.common.theory;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.common.theory.PropositionGraph.PathSynNode;
import com.bbn.nlp.banks.wordnet.WordNet;
import com.bbn.nlp.banks.wordnet.WordNetPOS;
import com.bbn.serif.events.utilities.Stemmer;
import com.bbn.serif.theories.SentenceTheory;
import com.bbn.serif.theories.SynNode;
import com.google.common.base.Optional;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableSet;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Set;

public class PropositionPath {
  private static final Logger log = LoggerFactory.getLogger(PropositionPath.class);

  final ImmutableList<PathSynNode> path;
  final SentenceTheory sentenceTheory;

  private PropositionPath(final ImmutableList<PathSynNode> path, final SentenceTheory sentenceTheory) {
    this.path = path;
    this.sentenceTheory =sentenceTheory;
  }

  public static PropositionPath from(final ImmutableList<PathSynNode> path, final SentenceTheory sentenceTheory) {
    return new PropositionPath(path, sentenceTheory);
  }

  public PathSynNode getNodeByIndex(final int index) {
    return path.get(index);
  }

  public int length() {
    return path.size() - 1;
  }

  public Optional<String> pathAsString() {
    if (path.size() == 0) {
      return Optional.absent();
    }

    StringBuffer s = new StringBuffer(path.get(length()).getNode().headWord().toString());
    for (int i = (path.size() - 2); i >= 0; i--) {
      s.append("_");
      s.append(path.get(i).getRole().toString());
      s.append("_");
      s.append(path.get(i).getNode().headWord().toString());
    }

    return Optional.of(s.toString());
  }

  // returns the proposition path with intervening (role, lemmatized-word), and the headword of both arguments are the two ends
  public Optional<String> pathAsLemmaString(final WordNet wordNet) {
    if (path.size() == 0) {
      return Optional.absent();
    }

    StringBuffer s = new StringBuffer(path.get(length()).getNode().headWord().toString());
    for (int i = (path.size() - 2); i >= 0; i--) {
      s.append("_");
      s.append(path.get(i).getRole().toString());
      s.append("_");

      if(i > 0) {
        final SynNode node = path.get(i).getNode();

        final Optional<WordNetPOS> wnPos = wordNet.language().wordnetPOS(node.headPOS());
        if(wnPos.isPresent() && node.headWord().asString().indexOf("_")==-1) {
          final Optional<Symbol> stem = wordNet.getFirstStem(node.headWord(), wnPos.get());
          if(stem.isPresent()) {
            //log.info("stemming {} into {}", node.headWord().toString(), stem.get().toString());
            s.append(stem.get().toString());
          } else {
            s.append(node.headWord().toString());
          }
        } else {
          s.append(node.headWord().toString());
        }
      } else {
        s.append(path.get(i).getNode().headWord().toString());
      }
    }

    return Optional.of(s.toString());
  }

  public Optional<String> argRoleOnPath() {
    if (path.size() == 0) {
      return Optional.absent();
    }

    return Optional.of(path.get(0).getRole().toString());
  }

  public Optional<String> pathAsRolePostagString() {
    if (path.size() == 0) {
      return Optional.absent();
    }

    StringBuffer s = new StringBuffer("");
    boolean addedToPath = false;
    for (int i = (path.size() - 2); i >= 0; i--) {
      if (addedToPath) {
        s.append("_");
      }
      s.append(path.get(i).getRole().toString());
      if (i > 0) {
        s.append("_");
        final SynNode node = path.get(i).getNode();
        s.append(node.headPOS().toString());
      }
      addedToPath = true;
    }

    return Optional.of(s.toString());
  }

  public Optional<String> pathAsRoleWordString(final Stemmer stemmer) {
    if (path.size() == 0) {
      return Optional.absent();
    }

    StringBuffer s = new StringBuffer("");
    boolean addedToPath = false;
    for (int i = (path.size() - 2); i >= 0; i--) {
      if (addedToPath) {
        s.append("_");
      }
      s.append(path.get(i).getRole().toString());
      if (i > 0) {
        s.append("_");
        final SynNode node = path.get(i).getNode();
        s.append(stemmer.stem(node.headWord(), node.headPOS()).toString());
      }
      addedToPath = true;
    }

    return Optional.of(s.toString());
  }

  public Optional<Set<Symbol>> pathWords(final Stemmer stemmer) {
    final ImmutableSet.Builder<Symbol> ret = ImmutableSet.builder();

    if (path.size() > 0) {
      for (int i = (path.size() - 2); i >= 0; i--) {
        if (i > 0) {
          final SynNode node = path.get(i).getNode();
          ret.add(stemmer.stem(node.headWord(), node.headPOS()));
        }
      }
      return Optional.<Set<Symbol>>of(ret.build());
    } else {
      return Optional.absent();
    }
  }

  public Optional<String> pathAsRoleString() {
    if (path.size() == 0) {
      return Optional.absent();
    }

    StringBuffer s = new StringBuffer("");
    boolean addedToPath = false;
    for (int i = (path.size() - 2); i >= 0; i--) {
      if (addedToPath) {
        s.append("_");
      }
      s.append(path.get(i).getRole().toString());
      addedToPath = true;
    }

    return Optional.of(s.toString());
  }

  public Optional<Set<Symbol>> pathRoles() {
    final ImmutableSet.Builder<Symbol> ret = new ImmutableSet.Builder<Symbol>();

    if (path.size() > 0) {
      for (int i = (path.size() - 2); i >= 0; i--) {
        ret.add(path.get(i).getRole());
      }
      return Optional.<Set<Symbol>>of(ret.build());
    } else {
      return Optional.absent();
    }
  }

  public SentenceTheory getSentenceTheory() {
    return sentenceTheory;
  }
}
