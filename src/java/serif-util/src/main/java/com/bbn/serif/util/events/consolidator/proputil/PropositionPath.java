package com.bbn.serif.util.events.consolidator.proputil;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.nlp.languages.Language;
import com.bbn.nlp.languages.LanguageSpecific;
import com.bbn.serif.common.SerifException;
import com.bbn.serif.util.events.consolidator.proputil.Stemmer;
import com.bbn.serif.theories.EventMention;
import com.bbn.serif.theories.Mention;
import com.bbn.serif.theories.Parse;
import com.bbn.serif.theories.Proposition;
import com.bbn.serif.theories.SentenceTheory;
import com.bbn.serif.theories.SynNode;
import com.bbn.serif.theories.ValueMention;

import com.fasterxml.jackson.annotation.JacksonInject;
import com.fasterxml.jackson.annotation.JsonAutoDetect;
import com.fasterxml.jackson.annotation.JsonCreator;
import com.google.common.base.Optional;
import com.google.common.cache.CacheBuilder;
import com.google.common.cache.CacheLoader;
import com.google.common.cache.LoadingCache;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableMultimap;
import com.google.common.collect.Multimap;

import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ExecutionException;

import javax.inject.Inject;

import static com.google.common.base.Preconditions.checkArgument;
import static com.google.common.base.Preconditions.checkNotNull;

/**
 * Captures the proposition path between two SynNodes in the same sentence
 *
 * @author ychan
 */
@SuppressWarnings("OptionalUsedAsFieldOrParameterType")
public class PropositionPath {

  private PropositionPath(final Optional<SynNode> argNode,
      final Map<SynNode, PropositionUtils.PathNode> synToPathNodes,
      final Optional<Integer> pathLength,
      final Optional<Symbol> rolePath, final Optional<Symbol> roleWordPath,
      final Optional<Symbol> argRoleOnPath,
      final Optional<Set<Symbol>> pathRoles, final Optional<Set<Symbol>> pathWords,
      final Multimap<Symbol, Symbol> directPropRolePredicate,
      final Set<Symbol> propRolesInContainingPropositions) {
    this.argNode = argNode;
    this.synToPathNodes = synToPathNodes;
    this.pathLength = pathLength;
    this.rolePath = rolePath;
    this.roleWordPath = roleWordPath;
    this.argRoleOnPath = argRoleOnPath;
    this.pathRoles = pathRoles;
    this.pathWords = pathWords;

    this.directPropRolePredicate = directPropRolePredicate;
    this.propRolesInContainingPropositions = propRolesInContainingPropositions;
  }

  public static Optional<Integer> getPathLengthBetweenSynNodes(final SynNode source,
      final SynNode target, final Map<SynNode, PropositionUtils.PathNode> synToPathNodes) {

    if (synToPathNodes.containsKey(source) && synToPathNodes.containsKey(target)) {
      final PropositionUtils.PathNode pathNode1 = synToPathNodes.get(source);
      final PropositionUtils.PathNode pathNode2 = synToPathNodes.get(target);

      final Optional<List<PropositionUtils.PathSynNode>> path =
          PropositionUtils.findPropPath(pathNode1, pathNode2);

      if (path.isPresent()) {
        return Optional.of(new Integer(path.get().size() - 1));
      }
    }

    return Optional.absent();
  }

  public static PropositionPath getPropPath(final SynNode source, final SynNode target,
      final Language language, final Stemmer stemmer,
      final Map<SynNode, PropositionUtils.PathNode> synToPathNodes) {

    //final List<PropositionUtils.PathNode> graph = PropositionUtils.constructPropositionGraph(sentenceTheory);

    //final Map<SynNode, PropositionUtils.PathNode> synToPathNodes = PropositionUtils.mapSynNodeToPathNode(graph);

    Optional<Integer> pathLength = Optional.absent();
    Optional<Symbol> rolePath = Optional.absent();
    Optional<Symbol> roleWordPath = Optional.absent();
    Optional<Symbol> argRoleOnPath = Optional.absent();
    Optional<Set<Symbol>> pathRoles = Optional.absent();
    Optional<Set<Symbol>> pathWords = Optional.absent();

    if (synToPathNodes.containsKey(source) && synToPathNodes.containsKey(target)) {
      final PropositionUtils.PathNode anchorPathNode = synToPathNodes.get(source);
      final PropositionUtils.PathNode argPathNode = synToPathNodes.get(target);

      final Optional<List<PropositionUtils.PathSynNode>> path = PropositionUtils.findPropPath(anchorPathNode, argPathNode);

      if (path.isPresent()) {
        pathLength = Optional.of(path.get().size() - 1);

        final String pathRoleString = PropositionUtils.pathAsRoleString(path.get());
        if (pathRoleString.compareTo("") != 0) {
          rolePath = Optional.of(Symbol.from(pathRoleString));
        }

        final String pathRoleWordString = PropositionUtils.pathAsRoleWordString(path.get(), stemmer);
        if (pathRoleWordString.compareTo("") != 0) {
          roleWordPath = Optional.of(Symbol.from(pathRoleWordString));
        }

        final String argRoleOnPathString = PropositionUtils.argRoleOnPath(path.get());
        if (argRoleOnPathString.compareTo("") != 0) {
          argRoleOnPath = Optional.of(Symbol.from(argRoleOnPathString));
        }

        pathRoles = PropositionUtils.pathRoles(path.get());
        pathWords = PropositionUtils.pathWords(path.get(), stemmer);
      }
    }


    final Multimap<Symbol, Symbol> directPropRolePredicate = null;

    final Set<Symbol> propRolesInContainingPropositions = null;

    return new PropositionPath(Optional.of(target), synToPathNodes, pathLength, rolePath, roleWordPath,
        argRoleOnPath, pathRoles, pathWords, directPropRolePredicate, propRolesInContainingPropositions);
  }


  public static PropositionPath getPropPath(final Optional<Mention> candidateArgument,
      final ValueMention candidateValue,
      final SentenceTheory sentenceTheory,
      final Language language, final Stemmer stemmer) {

    // if there is no parse for the sentence, or there is no proposition for the sentence, then 'graph' will be empty
    final List<PropositionUtils.PathNode> graph =
        PropositionUtils.constructPropositionGraph(sentenceTheory);

    // each PathNode internally contains a SynNode. This makes explicit the mapping from those SynNodes to PathNode
    // each PathNode is like a wrapper around a SynNode ; it contains info on proposition connections to other SynNode/PathNode
    final Map<SynNode, PropositionUtils.PathNode> synToPathNodes =
        PropositionUtils.mapSynNodeToPathNode(graph);

    // head of arg
    Optional<SynNode> argNode = Optional.absent();
    if (candidateArgument.isPresent()) {
      argNode = Optional.of(PropositionUtils.getTerminalHead(candidateArgument.get().head()));
    } else {
      final Parse parse = sentenceTheory.parse();
      final Optional<SynNode> valueNode = parse.root().get().nodeByTokenSpan(candidateValue.span());
      if (valueNode.isPresent()) {
        argNode = Optional.of(PropositionUtils.getTerminalHead(valueNode.get()));
      }
    }

    Optional<Integer> pathLength = Optional.absent();
    Optional<Symbol> rolePath = Optional.absent();
    Optional<Symbol> roleWordPath = Optional.absent();
    Optional<Symbol> argRoleOnPath = Optional.absent();
    Optional<Set<Symbol>> pathRoles = Optional.absent();
    Optional<Set<Symbol>> pathWords = Optional.absent();

    // look for all propositions involving current candidate argument, then note pairs of (prop-role, prop-predicate-word)
    final Multimap<Symbol, Symbol> directPropRolePredicate =
        associatedProps(sentenceTheory, candidateArgument, language, stemmer);

    final Set<Symbol> propRolesInContainingPropositions =
        PropositionUtils.propRolesInContainingPropositions(sentenceTheory, candidateArgument);

    return new PropositionPath(argNode, synToPathNodes, pathLength, rolePath, roleWordPath,
        argRoleOnPath,
        pathRoles, pathWords, directPropRolePredicate, propRolesInContainingPropositions);
  }

  /**
   * copied from AAUtils. Could use a lot of cleanup.
   */
  // Gather features from propositions that have the candidateArgument as one of their args
  // We go through each proposition in the current sentence. If a proposition has candidateArgument as one of its args:
  // - note the prop-role between proposition and _candidateArgument.
  //   Store pair <prop-role, prop predicate headword lemma> in predAssocPropFeas
  // - we consider all other arguments in the same proposition as neighbors of candidateArgument.
  //   For each such 'neighbor' arg:
  //     - note the prop-role between proposition and arg.
  //       Store pair <prop-role, headword lemma of arg> in argAssocPropFeas
  @LanguageSpecific("English")
  public static Multimap<Symbol, Symbol> associatedProps(final SentenceTheory sentenceTheory,
      final Optional<Mention> candidateArgument,
      final Language language, final Stemmer stemmer) {
    //Multimap<Symbol, Symbol> predAssocPropFeas = HashMultimap.create();
    ImmutableMultimap.Builder<Symbol, Symbol> ret = new ImmutableMultimap.Builder<Symbol, Symbol>();

    if (candidateArgument.isPresent()) {
      for (final Proposition prop : sentenceTheory.propositions()) {
        final Optional<SynNode> predHead = prop.predHead();
        if ((predHead.isPresent() && predHead.get().head()
            .equals(candidateArgument.get().head().head())) ||
            prop.predType() == Proposition.PredicateType.SET) {
          continue;
        }

        // check whether this proposition have the candidateArgument as one of its args
        boolean found = false;
        for (final Proposition.Argument arg : prop.args()) {
          if (arg instanceof Proposition.MentionArgument) {
            final Proposition.MentionArgument arg1 = (Proposition.MentionArgument) arg;
            if (arg1.mention() == candidateArgument.get()) {
              found = true;
              break;
            }
          }
        }

        if (found) {                // this proposition has the candidateArgument as one of its args
          if (predHead.isPresent()) {
            final Symbol predHeadSym = predHead.get().headWord();
            final Symbol predHeadPosSym = predHead.get().headPOS();
            Symbol predHeadLemma;

            // if the predicate headword is a noun or verb, get its lemma form
            if (predHeadPosSym.toString().startsWith("NN") || predHeadPosSym.toString()
                .startsWith("VB")) {
              predHeadLemma = stemmer
                  .stem(Symbol.from(language.lowercase(predHeadSym.toString())), predHeadPosSym);
            } else {
              predHeadLemma = Symbol.from(language.lowercase(predHeadSym.toString()));
            }

            for (final Proposition.Argument arg : prop
                .args()) {                // go through each arg of current proposition
              Optional<Symbol> roleSym;
              if (prop.predType() == Proposition.PredicateType.POSS) {
                roleSym = Optional.of(Symbol.from("poss"));
              } else {
                roleSym = arg.role();
              }

              if (arg instanceof Proposition.MentionArgument) {        // arg is a mention
                final Mention m = ((Proposition.MentionArgument) arg).mention();
                final Symbol argSym = m.head().headWord();
                final Symbol argPosSym = m.head().headPOS();

                if (m == candidateArgument
                    .get()) {        // if this argument is the candidate itself, pair it with the proposition
                  //predAssocPropFeas.put(roleSym.get(), predHeadLemma);
                  ret.put(roleSym.get(), predHeadLemma);
                }
								/*
								else {		// this argument is not the candidateArgument (its neighbor instead) ; so pair it with the candidate
									if(roleSym.isPresent() && !(roleSym.get().toString().compareTo("<ref>")==0 && prop.predType()==Proposition.PredicateType.NOUN)) {
										if(argPosSym.toString().startsWith("NN") || argPosSym.toString().startsWith("VB")) {
											Symbol argLemma = stemmer.stem(argSym, argPosSym);
											argAssocPropFeas.put(roleSym.get(), argLemma);
										}
									}
								}
								*/
              }
							/*
							else if(arg instanceof Proposition.PropositionArgument) {
								Proposition p = arg.parentProposition();
								Optional<SynNode> pHead = p.predHead();
								if(pHead.isPresent()) {
									Symbol argSym = pHead.get().headWord();
									Symbol argPosSym = pHead.get().headPOS();

									if(roleSym.isPresent()) {
										if(argPosSym.toString().startsWith("NN") || argPosSym.toString().startsWith("VB")) {
											Symbol argLemma = stemmer.stem(argSym, argPosSym);
											argAssocPropFeas.put(roleSym.get(), argLemma);
										}
									}
								}
							}
							else if(arg instanceof Proposition.TextArgument) {
								// ignore for now
							}
							*/
            } // went through each arg of current proposition
          }
        } // tested for: this proposition has candidateArgument as one of its args

      } // went through each proposition in sentence
    }

    //return predAssocPropFeas;
    return ret.build();
  }

  public static PropositionPath getPropPath(final EventMention em,
      final Optional<Mention> candidateArgument, final ValueMention candidateValue,
      final SentenceTheory sentenceTheory,
      final Language language, final Stemmer stemmer) {

    // if there is no parse for the sentence, or there is no proposition for the sentence, then 'graph' will be empty
    final List<PropositionUtils.PathNode> graph =
        PropositionUtils.constructPropositionGraph(sentenceTheory);

		/*
		System.out.println("== getPropPath start ==");
		StringBuffer s = new StringBuffer("");
		s.append("anchor:["+em.anchorNode().headWord().toString()+"]");
		if(candidateArgument.isPresent()) {
			s.append(" mention:["+candidateArgument.get().head().headWord().toString()+"]");
			s.append(" value:[NULL]");
		}
		else {
			s.append(" mention:[NULL]");
			s.append(" value:["+candidateValue.span().tokenizedText()+"]");
		}
		System.out.println(s.toString());
		for(int i=0; i<graph.size(); i++) {
			System.out.println("SynNode " + i + " " + graph.get(i).toString());
		}
		*/

    // each PathNode internally contains a SynNode. This makes explicit the mapping from those SynNodes to PathNode
    // each PathNode is like a wrapper around a SynNode ; it contains info on proposition connections to other SynNode/PathNode
    final Map<SynNode, PropositionUtils.PathNode> synToPathNodes =
        PropositionUtils.mapSynNodeToPathNode(graph);

    // head of anchor
    final SynNode anchorNode = PropositionUtils.getTerminalHead(em.anchorNode());

    // head of arg
    Optional<SynNode> argNode = Optional.absent();
    if (candidateArgument.isPresent()) {
      argNode = Optional.of(PropositionUtils.getTerminalHead(candidateArgument.get().head()));
    } else {
      final Parse parse = sentenceTheory.parse();
      final Optional<SynNode> valueNode = parse.root().get().nodeByTokenSpan(candidateValue.span());
      if (valueNode.isPresent()) {
        argNode = Optional.of(PropositionUtils.getTerminalHead(valueNode.get()));
      }
    }

    Optional<Integer> pathLength = Optional.absent();
    Optional<Symbol> rolePath = Optional.absent();
    Optional<Symbol> roleWordPath = Optional.absent();
    Optional<Symbol> argRoleOnPath = Optional.absent();
    Optional<Set<Symbol>> pathRoles = Optional.absent();
    Optional<Set<Symbol>> pathWords = Optional.absent();

    if (argNode.isPresent() && synToPathNodes.containsKey(anchorNode) && synToPathNodes
        .containsKey(argNode.get())) {
      final PropositionUtils.PathNode anchorPathNode = synToPathNodes.get(anchorNode);
      final PropositionUtils.PathNode argPathNode = synToPathNodes.get(argNode.get());

      final Optional<List<PropositionUtils.PathSynNode>> path =
          PropositionUtils.findPropPath(anchorPathNode, argPathNode);

      if (path.isPresent()) {
        pathLength = Optional.of(path.get().size() - 1);

        final String pathRoleString = PropositionUtils.pathAsRoleString(path.get());
        if (pathRoleString.compareTo("") != 0) {
          rolePath = Optional.of(Symbol.from(pathRoleString));
        }

        final String pathRoleWordString =
            PropositionUtils.pathAsRoleWordString(path.get(), stemmer);
        if (pathRoleWordString.compareTo("") != 0) {
          roleWordPath = Optional.of(Symbol.from(pathRoleWordString));
        }

        final String argRoleOnPathString = PropositionUtils.argRoleOnPath(path.get());
        if (argRoleOnPathString.compareTo("") != 0) {
          argRoleOnPath = Optional.of(Symbol.from(argRoleOnPathString));
        }

        //System.out.println("path: len=" + pathLength + " pathRoleString=" + pathRoleString + " pathRoleWordString=" + pathRoleWordString + " argRoleOnPathString=" + argRoleOnPathString);

        pathRoles = PropositionUtils.pathRoles(path.get());
        pathWords = PropositionUtils.pathWords(path.get(), stemmer);
      }
    }
    //System.out.println("== getPropPath end ==");

    //Optional<Set<Symbol>> verbPaths = Optional.absent();
		/*
		if(argNode.isPresent() && synToPathNodes.containsKey(argNode.get())) {
			final Set<String> paths = PropositionUtils.pathToVerbString(argNode.get(), synToPathNodes, sentenceTheory, stemmer);
			if(paths.size()>0) {
				Set<Symbol> ret = Sets.newHashSet();
				for(final String p : paths) {
					ret.add(Symbol.from(p));
				}
				verbPaths = Optional.of(ret);
			}
		}
		*/

    // look for all propositions involving current candidate argument, then note pairs of (prop-role, prop-predicate-word)
    final Multimap<Symbol, Symbol> directPropRolePredicate =
        associatedProps(sentenceTheory, candidateArgument, language, stemmer);

    final Set<Symbol> propRolesInContainingPropositions =
        PropositionUtils.propRolesInContainingPropositions(sentenceTheory, candidateArgument);

    return new PropositionPath(argNode, synToPathNodes, pathLength, rolePath, roleWordPath,
        argRoleOnPath,
        pathRoles, pathWords, directPropRolePredicate, propRolesInContainingPropositions);
  }


  public Map<SynNode, List<PropositionUtils.PathSynNode>> pathToTargets(
      final Set<SynNode> targets) {
    final ImmutableMap.Builder<SynNode, List<PropositionUtils.PathSynNode>> ret =
        new ImmutableMap.Builder<SynNode, List<PropositionUtils.PathSynNode>>();

    if (argNode.isPresent() && synToPathNodes.containsKey(argNode.get())) {
      final PropositionUtils.PathNode argPathNode = synToPathNodes.get(argNode.get());

      for (final SynNode node : targets) {
        if (synToPathNodes.containsKey(node)) {
          final PropositionUtils.PathNode targetNode = synToPathNodes.get(node);
          final Optional<List<PropositionUtils.PathSynNode>> path =
              PropositionUtils.findPropPath(targetNode, argPathNode);
          if (path.isPresent()) {
            final int len = path.get().size() - 1;
            if (len <= 3 && path.get().size() != 0) {
              ret.put(node, path.get());
              //final String pathRoleString = PropositionUtils.pathAsRoleString(path.get());
              //if(pathRoleString.compareTo("")!=0) {
              //	ret.put(node, Symbol.from(pathRoleString));
              //}
            }
          }
        }
      }
    }

    return ret.build();
  }

  public Optional<Integer> pathLength() {
    return pathLength;
  }

  public Optional<Symbol> rolePath() {
    return rolePath;
  }

  public Optional<Symbol> roleWordPath() {
    return roleWordPath;
  }

  public Optional<Symbol> argRoleOnPath() {
    return argRoleOnPath;
  }

  public Optional<Set<Symbol>> pathRoles() {
    return pathRoles;
  }

  public Optional<Set<Symbol>> pathWords() {
    return pathWords;
  }

  public Multimap<Symbol, Symbol> directPropRolePredicate() {
    return directPropRolePredicate;
  }

  public final Set<Symbol> propRolesInContainingPropositions() {
    return propRolesInContainingPropositions;
  }

  private final Optional<SynNode> argNode;
  private final Map<SynNode, PropositionUtils.PathNode> synToPathNodes;
  private final Optional<Integer> pathLength;
  private final Optional<Symbol> rolePath;
  private final Optional<Symbol> roleWordPath;
  private final Optional<Symbol> argRoleOnPath;
  private final Optional<Set<Symbol>> pathRoles;
  private final Optional<Set<Symbol>> pathWords;

  private final Multimap<Symbol, Symbol> directPropRolePredicate;
  private final Set<Symbol> propRolesInContainingPropositions;

  @JsonAutoDetect(fieldVisibility=JsonAutoDetect.Visibility.NONE)
  public static final class Extractor {
    private final Language language;
    private final Stemmer stemmer;
    // repeatedly recalculating the proposition graph for each sentence is very expensive
    // and dominates feature extraction time.  Therefore we remember the graphs for the last
    // 50 sentences we've seen
    // we use weakKeys so documents are not kept around just for the cache
    private final LoadingCache<SentenceTheory, List<PropositionUtils.PathNode>>
        sentencePropGraphCache =
        CacheBuilder.newBuilder().maximumSize(50).weakKeys().build(
            new CacheLoader<SentenceTheory, List<PropositionUtils.PathNode>>() {
              @Override
              public List<PropositionUtils.PathNode> load(final SentenceTheory st)
                  throws Exception {
                return PropositionUtils.constructPropositionGraph(st);
              }
            }
        );

    @JsonCreator
    @Inject
    public Extractor(@JacksonInject("language") final Language language,
        @JacksonInject("stemmer") final Stemmer stemmer) {
      this.language = checkNotNull(language);
      this.stemmer = checkNotNull(stemmer);
    }

    public PropositionPath getPropPath(final Optional<Mention> candidateArgument,
        final Optional<ValueMention> candidateValue, final Optional<SynNode> candidateNode,
        final SentenceTheory sentenceTheory) {
      // A candidate argument may have some or all of `candidateArgument`, `candidateValue`, and
      // `candidateNode` present.  When looking for a corresponding `SynNode`, we prefer them in the
      // order node, argument, value because that is the order of objects which most closely
      // correspond to `SynNode`s
      checkArgument(candidateArgument.isPresent() || candidateValue.isPresent()
          || candidateNode.isPresent());

      // if there is no parse for the sentence, or there is no proposition for the sentence,
      // then 'graph' will be empty
      final List<PropositionUtils.PathNode> graph;
      try {
        graph = sentencePropGraphCache.get(sentenceTheory);
      } catch (ExecutionException e) {
        throw new SerifException(e);
      }

      // each PathNode internally contains a SynNode. This makes explicit the mapping from those SynNodes to PathNode
      // each PathNode is like a wrapper around a SynNode ; it contains info on proposition connections to other SynNode/PathNode
      final Map<SynNode, PropositionUtils.PathNode> synToPathNodes =
          PropositionUtils.mapSynNodeToPathNode(graph);

      // head of arg
      Optional<SynNode> argNode = Optional.absent();
      if (candidateNode.isPresent()) {
        argNode = Optional.of(PropositionUtils.getTerminalHead(candidateNode.get()));
      } else if (candidateArgument.isPresent()) {
        argNode = Optional.of(PropositionUtils.getTerminalHead(candidateArgument.get().head()));
      } else {
        final Parse parse = sentenceTheory.parse();
        final Optional<SynNode> valueNode =
            parse.root().get().nodeByTokenSpan(candidateValue.get().span());
        if (valueNode.isPresent()) {
          argNode = Optional.of(PropositionUtils.getTerminalHead(valueNode.get()));
        }
      }

      Optional<Integer> pathLength = Optional.absent();
      Optional<Symbol> rolePath = Optional.absent();
      Optional<Symbol> roleWordPath = Optional.absent();
      Optional<Symbol> argRoleOnPath = Optional.absent();
      Optional<Set<Symbol>> pathRoles = Optional.absent();
      Optional<Set<Symbol>> pathWords = Optional.absent();

      // look for all propositions involving current candidate argument, then note pairs of (prop-role, prop-predicate-word)
      final Multimap<Symbol, Symbol> directPropRolePredicate =
          associatedProps(sentenceTheory, candidateArgument, language, stemmer);

      final Set<Symbol> propRolesInContainingPropositions =
          PropositionUtils.propRolesInContainingPropositions(sentenceTheory, candidateArgument);

      return new PropositionPath(argNode, synToPathNodes, pathLength, rolePath, roleWordPath,
          argRoleOnPath,
          pathRoles, pathWords, directPropRolePredicate, propRolesInContainingPropositions);
    }

    public PropositionPath getPropPath(final EventMention em,
        final Optional<Mention> candidateArgument, final Optional<ValueMention> candidateValue,
        final Optional<SynNode> nodeValue,
        final SentenceTheory sentenceTheory) {
      checkArgument(candidateArgument.isPresent() || candidateValue.isPresent()
          || nodeValue.isPresent());

      // if there is no parse for the sentence, or there is no proposition for the sentence, then 'graph' will be empty
      final List<PropositionUtils.PathNode> graph;
      try {
        graph = sentencePropGraphCache.get(sentenceTheory);
      } catch (ExecutionException e) {
        throw new SerifException(e);
      }

      // each PathNode internally contains a SynNode. This makes explicit the mapping from those SynNodes to PathNode
      // each PathNode is like a wrapper around a SynNode ; it contains info on proposition connections to other SynNode/PathNode
      final Map<SynNode, PropositionUtils.PathNode> synToPathNodes =
          PropositionUtils.mapSynNodeToPathNode(graph);

      // head of anchor
      final SynNode anchorNode = PropositionUtils.getTerminalHead(em.anchorNode());

      // head of arg
      Optional<SynNode> argNode = Optional.absent();
      if (nodeValue.isPresent()) {
        argNode = Optional.of(PropositionUtils.getTerminalHead(nodeValue.get()));
      } else if (candidateArgument.isPresent()) {
        argNode = Optional.of(PropositionUtils.getTerminalHead(candidateArgument.get().head()));
      } else {
        final Parse parse = sentenceTheory.parse();
        final Optional<SynNode> valueNode =
            parse.root().get().nodeByTokenSpan(candidateValue.get().span());
        if (valueNode.isPresent()) {
          argNode = Optional.of(PropositionUtils.getTerminalHead(valueNode.get()));
        }
      }

      Optional<Integer> pathLength = Optional.absent();
      Optional<Symbol> rolePath = Optional.absent();
      Optional<Symbol> roleWordPath = Optional.absent();
      Optional<Symbol> argRoleOnPath = Optional.absent();
      Optional<Set<Symbol>> pathRoles = Optional.absent();
      Optional<Set<Symbol>> pathWords = Optional.absent();

      if (argNode.isPresent() && synToPathNodes.containsKey(anchorNode) && synToPathNodes
          .containsKey(argNode.get())) {
        final PropositionUtils.PathNode anchorPathNode = synToPathNodes.get(anchorNode);
        final PropositionUtils.PathNode argPathNode = synToPathNodes.get(argNode.get());

        final Optional<List<PropositionUtils.PathSynNode>> path =
            PropositionUtils.findPropPath(anchorPathNode, argPathNode);

        if (path.isPresent()) {
          pathLength = Optional.of(path.get().size() - 1);

          final String pathRoleString = PropositionUtils.pathAsRoleString(path.get());
          if (pathRoleString.compareTo("") != 0) {
            rolePath = Optional.of(Symbol.from(pathRoleString));
          }

          final String pathRoleWordString =
              PropositionUtils.pathAsRoleWordString(path.get(), stemmer);
          if (pathRoleWordString.compareTo("") != 0) {
            roleWordPath = Optional.of(Symbol.from(pathRoleWordString));
          }

          final String argRoleOnPathString = PropositionUtils.argRoleOnPath(path.get());
          if (argRoleOnPathString.compareTo("") != 0) {
            argRoleOnPath = Optional.of(Symbol.from(argRoleOnPathString));
          }

          pathRoles = PropositionUtils.pathRoles(path.get());
          pathWords = PropositionUtils.pathWords(path.get(), stemmer);
        }
      }

      // look for all propositions involving current candidate argument, then note pairs of (prop-role, prop-predicate-word)
      final Multimap<Symbol, Symbol> directPropRolePredicate =
          associatedProps(sentenceTheory, candidateArgument, language, stemmer);

      final Set<Symbol> propRolesInContainingPropositions =
          PropositionUtils.propRolesInContainingPropositions(sentenceTheory, candidateArgument);

      return new PropositionPath(argNode, synToPathNodes, pathLength, rolePath, roleWordPath,
          argRoleOnPath,
          pathRoles, pathWords, directPropRolePredicate, propRolesInContainingPropositions);
    }

  }
}
