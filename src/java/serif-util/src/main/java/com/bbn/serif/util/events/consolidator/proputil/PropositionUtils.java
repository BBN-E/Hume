package com.bbn.serif.util.events.consolidator.proputil;

import com.bbn.bue.common.collections.TableUtils;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.nlp.languages.LanguageSpecific;
import com.bbn.serif.util.events.consolidator.proputil.Stemmer;
import com.bbn.serif.theories.Mention;
import com.bbn.serif.theories.Parse;
import com.bbn.serif.theories.Proposition;
import com.bbn.serif.theories.Proposition.Argument;
import com.bbn.serif.theories.Proposition.MentionArgument;
import com.bbn.serif.theories.Proposition.PredicateType;
import com.bbn.serif.theories.Proposition.PropositionArgument;
import com.bbn.serif.theories.Proposition.TextArgument;
import com.bbn.serif.theories.SentenceTheory;
import com.bbn.serif.theories.SynNode;

import com.google.common.base.Function;
import com.google.common.base.Optional;
import com.google.common.collect.HashBasedTable;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableListMultimap;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableMultimap;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Lists;
import com.google.common.collect.Maps;
import com.google.common.collect.Ordering;
import com.google.common.collect.Table;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.HashSet;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.Queue;
import java.util.Set;

import static com.google.common.base.Functions.compose;


/**
 * Captures the proposition path between two SynNodes in the same sentence
 *
 * @author ychan
 */
public final class PropositionUtils {

  private static final Logger log = LoggerFactory.getLogger(PropositionUtils.class);

  private PropositionUtils() {
    throw new UnsupportedOperationException();
  }

  /*
   * Methods for extracting head SynNode for: MentionArgument , TextArgument , PropositionArgument , Proposition
   */
  private static SynNode getHead(final MentionArgument a) {
    return a.mention().head();
  }

  private static SynNode getHead(final TextArgument a) {
    return a.node();
  }

  // here, we parallel the logic of method "getTerminalHead(final Proposition prop)", but do 'getHead' instead of 'getTerminalHead'
  private static Optional<SynNode> getHead(final PropositionArgument a) {
    final Proposition prop = a.proposition();

    if ((prop.predType() == Proposition.PredicateType.NAME) || (prop.predType()
                                                                    == Proposition.PredicateType.POSS)) {
      for (final Proposition.Argument arg : prop.args()) {
        if (arg.role().isPresent() && arg.role().get() == ROLE_REF) {
          if (arg instanceof MentionArgument) {
            return Optional.of(getHead((MentionArgument) arg));
          } else if (arg instanceof TextArgument) {
            return Optional.of(getHead((TextArgument) arg));
          }
        }
      }
    }

    return prop.predHead();
  }

  private static SynNode getTerminalHead(final MentionArgument a) {
    return getTerminalHead(a.mention().head());
  }

  private static SynNode getTerminalHead(final TextArgument a) {
    return getTerminalHead(a.node());
  }

  private static Optional<SynNode> getTerminalHead(final PropositionArgument a) {
    return getTerminalHead(a.proposition());
  }

  // NAME propositions predHead is absent
  // POSS propositions predHead usually points to tokens such as 's
  // So for both of the above, you'll be better off returning the head SynNode of the <ref> argument in the proposition
  private static Optional<SynNode> getTerminalHead(final Proposition prop) {
    if ((prop.predType() == Proposition.PredicateType.NAME) || (prop.predType()
                                                                    == Proposition.PredicateType.POSS)) {
      for (final Proposition.Argument arg : prop.args()) {
        if (arg.role().isPresent() && arg.role().get() == ROLE_REF) {
          if (arg instanceof MentionArgument) {
            return Optional.of(getTerminalHead((MentionArgument) arg));
          } else if (arg instanceof TextArgument) {
            return Optional.of(getTerminalHead((TextArgument) arg));
          }
        }
      }
    }

    final Optional<SynNode> head = prop.predHead();
    if (head.isPresent()) {
      return Optional.of(getTerminalHead(head.get()));
    } else {
      return Optional.absent();
    }
  }

  public static SynNode getTerminalHead(final SynNode node) {
    SynNode curr = node;
    while (curr.head() != curr) {
      curr = curr.head();
    }
    return curr;
  }


  public static String pathAsString(final List<PathSynNode> path) {
    if (path.size() == 0) {
      return "";
    }

    StringBuffer s = new StringBuffer(path.get(path.size() - 1).getNode().headWord().toString());
    for (int i = (path.size() - 2); i >= 0; i--) {
      s.append("_");
      s.append(path.get(i).getRole().toString());
      s.append("_");
      s.append(path.get(i).getNode().headWord().toString());
    }

    return s.toString();
  }

  public static String argRoleOnPath(final List<PathSynNode> path) {
    if (path.size() == 0) {
      return "";
    }

    return path.get(0).getRole().toString();
  }

  public static String pathAsRolePostagString(final List<PathSynNode> path) {
    if (path.size() == 0) {
      return "";
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

    return s.toString();
  }

  public static String pathAsRoleWordString(final List<PathSynNode> path, final Stemmer stemmer) {
    if (path.size() == 0) {
      return "";
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

    return s.toString();
  }

  public static Optional<Set<Symbol>> pathWords(final List<PathSynNode> path,
      final Stemmer stemmer) {
    final ImmutableSet.Builder<Symbol> ret = new ImmutableSet.Builder<Symbol>();

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

  public static String pathAsRoleString(final List<PathSynNode> path) {
    if (path.size() == 0) {
      return "";
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

    return s.toString();
  }

  public static Optional<Set<Symbol>> pathRoles(final List<PathSynNode> path) {
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

  public static Set<String> pathToVerbString(final SynNode source,
      final Map<SynNode, PropositionUtils.PathNode> synToPathNodes,
      final SentenceTheory st, final Stemmer stemmer) {
    final ImmutableSet.Builder<String> ret = new ImmutableSet.Builder<String>();

    final List<List<PathSynNode>> paths = pathToVerb(source, synToPathNodes, st);
    for (final List<PathSynNode> path : paths) {
      final int pathLength = path.size() - 1;
      if (pathLength <= 2) {
        final String pathRoleString = pathAsRoleString(path);
        StringBuffer s = new StringBuffer("");
        s.append(pathRoleString);
        s.append("_");

        final SynNode node = path.get(0)
            .getNode();        // since we are going from arg to verbs, the first element is the verb
        s.append(stemmer.stem(node.headWord(), node.headPOS()).toString());

        ret.add(s.toString());
      }
    }

    return ret.build();
  }

  // prop path to all verbs in sentence ; source is the candidate arg
  @LanguageSpecific("English")
  public static List<List<PathSynNode>> pathToVerb(final SynNode source,
      final Map<SynNode, PropositionUtils.PathNode> synToPathNodes, final SentenceTheory st) {
    final ImmutableList.Builder<List<PathSynNode>> ret =
        new ImmutableList.Builder<List<PathSynNode>>();

    if (synToPathNodes.containsKey(source)) {
      final PropositionUtils.PathNode sourcePathNode = synToPathNodes.get(source);

      final Parse parse = st.parse();
      final SynNode root = parse.root().get();
      for (int i = 0; i < root.numTerminals(); i++) {
        final SynNode node = root.nthTerminal(i);
        if ((node != source) && node.headPOS().toString().startsWith("VB")) {
          if (synToPathNodes.containsKey(node)) {
            final PropositionUtils.PathNode currPathNode = synToPathNodes.get(node);

            final Optional<List<PropositionUtils.PathSynNode>> path =
                findPropPath(sourcePathNode, currPathNode);
            if (path.isPresent()) {
              ret.add(path.get());
            }
          }
        }
      }
    }

    return ret.build();
  }

  // breadth first search for a path from source to target
  public static Optional<List<PathSynNode>> findPropPath(final PathNode source,
      final PathNode target) {
    Queue<PathNode> Q = new LinkedList<PathNode>();
    Set<PathNode> seenNodes = new HashSet<PathNode>();
    Queue<PathSynNode> q =
        new LinkedList<PathSynNode>();                // to record our path traversal
    Map<PathSynNode, PathSynNode> parents =
        Maps.newHashMap();        // to record our path traversal
    Map<PathSynNode, Integer> nodeDepth =
        Maps.newHashMap();        // keeps track of the depth we are in, so we can stop exploring if we are too deep

    seenNodes.add(source);

    Q.add(source);
    q.add(PathSynNode.from(ROLE_NULL, source.getNode()));
    nodeDepth.put(q.peek(), 0);

    Optional<PathSynNode> destination = Optional
        .absent();                // this will be present if we can get from source to target

    while (!Q.isEmpty()) {
      final PathNode node = Q.remove();
      final PathSynNode parent = q.remove();
      final int currentDepth = nodeDepth.get(parent);

      if (node == target) {
        destination = Optional.of(parent);
        break;
      }

      if (currentDepth < maxPropPathLength) {
        for (int i = 0; i < node.numberOfNeighbor(); i++) {
          final PathNode n = node.getNeighborNode(i);
          final Symbol r = node.getNeighborRole(i);
          if (!seenNodes.contains(n)) {
            seenNodes.add(n);
            Q.add(n);

            final PathSynNode child = PathSynNode.from(r, n.getNode());
            q.add(child);
            parents.put(child, parent);
            nodeDepth.put(child, currentDepth + 1);
          }
        }
      }
    }

    if (destination.isPresent()) {
      ImmutableList.Builder<PathSynNode> path =
          new ImmutableList.Builder<PropositionUtils.PathSynNode>();
      PathSynNode curr = destination.get();
      path.add(curr);
      while (parents.containsKey(curr)) {
        final PathSynNode p = parents.get(curr);
        curr = p;
        path.add(curr);
      }
      final List<PathSynNode> ret = path.build();
      return Optional.of(ret);
    } else {
      return Optional.absent();
    }
  }

  public static ImmutableMap<SynNode, PathNode> mapSynNodeToPathNode(final List<PathNode> nodes) {
    ImmutableMap.Builder<SynNode, PathNode> ret =
        new ImmutableMap.Builder<SynNode, PropositionUtils.PathNode>();

    for (final PathNode node : nodes) {
      final SynNode synNode = node.getNode();
      ret.put(synNode, node);
    }

    return ret.build();
  }

  public static ImmutableList<PropositionUtils.PathNode> constructPropositionGraph(final SentenceTheory st) {
    ImmutableList.Builder<PropositionUtils.PathNode> graph =
        new ImmutableList.Builder<PropositionUtils.PathNode>();

    final Table<SynNode, SynNode, Symbol> connections = extractPropositionConnections(st);

    if (connections.size() == 0) {
      return graph.build();
    }

    final Parse parse = st.parse();

    // grab the terminal SynNodes
    Map<SynNode, Integer> terminalIndices = Maps.newHashMap();
    List<PropositionUtils.PathNode> nodes = Lists.newArrayList();
    List<SynNode> terminalSynNodes = Lists.newArrayList();

    for (int i = 0; i < parse.root().get().numTerminals(); i++) {
      final SynNode synNode = parse.root().get().nthTerminal(i);
      terminalSynNodes.add(synNode);
      terminalIndices.put(synNode, i);
      nodes.add(PathNode.from(synNode));
    }

    for (int i = 0; (i + 1) < terminalSynNodes.size(); i++) {
      final SynNode node1 = terminalSynNodes.get(i);
      for (int j = (i + 1); j < terminalSynNodes.size(); j++) {
        final SynNode node2 = terminalSynNodes.get(j);

        Optional<Symbol> role = Optional.absent();
        if (connections.contains(node1, node2)) {
          role = Optional.of(connections.get(node1, node2));
        } else if (connections.contains(node2, node1)) {
          role = Optional.of(connections.get(node2, node1));
        }

        if (role.isPresent()) {
          nodes.get(i).addNeighbor(role.get(), nodes.get(j));
          nodes.get(j).addNeighbor(role.get(), nodes.get(i));
        }
      }
    }

		/*
		for(final Table.Cell<SynNode, SynNode, Symbol> cell : connections.cellSet()) {
			final SynNode node1 = cell.getRowKey();
			final SynNode node2 = cell.getColumnKey();
			final Symbol role = cell.getValue();

			if(terminalIndices.containsKey(node1) && terminalIndices.containsKey(node2)) {
				final int i1 = terminalIndices.get(node1);
				final int i2 = terminalIndices.get(node2);
				nodes.get(i1).addNeighbor(role, nodes.get(i2));
				nodes.get(i2).addNeighbor(role, nodes.get(i1));
			}
			else {
				System.out.println("ERROR : cannot find either node1 or node2 in terminalIndices");
			}
		}
		*/

    graph.addAll(nodes);
    return graph.build();
  }

  private static boolean usePropConnection(final Table<SynNode, SynNode, Symbol> table,
      final SynNode node1, final SynNode node2, final Symbol newRole) {
    if (!table.contains(node1, node2) && !table.contains(node2, node1)) {
      return true;
    } else {
      if (newRole == ROLE_SUB || newRole == ROLE_OBJ || newRole == ROLE_IOBJ) {
        // TODO: what is the logic here? If we want a hierarchy of roles, we should have a full
        // hierarchy of roles...
        return true;
      } else {
        //log.warn("Refusing to add duplicate connection from {} to {} of type {}", node1, node2,
        //    newRole);
        return false;
      }
    }
  }

  // collect members of SET propositions
  public static Map<SynNode, Set<SynNode>> propositionSetMembersOfSentence(
      final SentenceTheory st) {
    final ImmutableMap.Builder<SynNode, Set<SynNode>> ret =
        new ImmutableMap.Builder<SynNode, Set<SynNode>>();

    for (final Proposition prop : st.propositions()) {
      final PredicateType predType = prop.predType();

      if (predType == Proposition.PredicateType.SET) {
        Optional<SynNode> setRef = Optional.absent();
        Set<SynNode> members = new HashSet<SynNode>();
        for (final Proposition.Argument arg : prop.args()) {
          final Optional<Symbol> role = arg.role();
          Optional<SynNode> argHead = Optional.absent();
          if (arg instanceof MentionArgument) {
            argHead = Optional.of(getHead((MentionArgument) arg));
          } else if (arg instanceof TextArgument) {
            argHead = Optional.of(getHead((TextArgument) arg));
          }
          if (role.isPresent() && argHead.isPresent()) {
            if (role.get() == ROLE_REF) {
              setRef = argHead;
            } else if (role.get() == ROLE_MEMBER) {
              members.add(getTerminalHead(argHead.get()));
            }
          }
        }
        if (setRef.isPresent()) {
          ret.put(setRef.get(), members);
        }
      }
    }

    return ret.build();
  }

  // this doesn't account for set fall-through
  public static Set<Symbol> propRolesInContainingPropositions(final SentenceTheory st,
      final Optional<Mention> mention) {
    final ImmutableSet.Builder<Symbol> ret = new ImmutableSet.Builder<Symbol>();

    if (!mention.isPresent()) {
      return ret.build();
    }

    final ImmutableSet.Builder<SynNode> setReferencesB = ImmutableSet.builder();
    for (final Proposition prop : st.propositions()) {
      final PredicateType predType = prop.predType();

      // if proposition is a set, we check whether the given mention is an member of this set
      // if it is a member, we record the set reference, and then later use that to do set-fall-through
      if (predType == Proposition.PredicateType.SET) {
        Optional<SynNode> setRef = Optional.absent();
        boolean inSet = false;
        //Set<SynNode> members = new HashSet<SynNode>();
        for (final Proposition.Argument arg : prop.args()) {
          Optional<SynNode> argHead = Optional.absent();
          if (arg instanceof MentionArgument) {
            argHead = Optional.of(getHead((MentionArgument) arg));
          } else if (arg instanceof TextArgument) {
            argHead = Optional.of(getHead((TextArgument) arg));
          }
          final Optional<Symbol> role = arg.role();
          if (role.isPresent()) {
            if (role.get() == ROLE_REF && argHead.isPresent()) {
              setRef = argHead;
            } else if (role.get() == ROLE_MEMBER) {
              if (arg instanceof Proposition.MentionArgument) {
                final MentionArgument arg1 = (MentionArgument) arg;
                if (arg1.mention() == mention.get()) {
                  inSet = true;
                }
              }
            }
          }
        }
        if (inSet && setRef.isPresent()) {
          setReferencesB.add(setRef.get());
        }
      } else {
        for (final Argument arg : prop.args()) {
          if (arg instanceof Proposition.MentionArgument) {
            final MentionArgument arg1 = (MentionArgument) arg;
            if (arg1.mention() == mention.get()) {
              if (arg1.role().isPresent() && arg1.role().get() != ROLE_REF) {
                ret.add(arg1.role().get());
              }
            }
          }
        }
      }
    }

    // if there are set references, we need to do role fall-through
    final ImmutableSet<SynNode> setReferences = setReferencesB.build();
    if (setReferences.size() > 0) {
      for (final Proposition prop : st.propositions()) {
        final PredicateType predType = prop.predType();
        if (predType != Proposition.PredicateType.SET) {
          for (final Argument arg : prop.args()) {
            Optional<SynNode> argHead = Optional.absent();
            if (arg instanceof MentionArgument) {
              argHead = Optional.of(getHead((MentionArgument) arg));
            } else if (arg instanceof TextArgument) {
              argHead = Optional.of(getHead((TextArgument) arg));
            }
            final Optional<Symbol> role = arg.role();
            if (role.isPresent() && role.get() != ROLE_REF && argHead.isPresent() && setReferences
                .contains(argHead.get())) {
              ret.add(role.get());
            }
          }
        }
      }
    }

    return ret.build();
  }

  private static Table<SynNode, SynNode, Symbol> extractPropositionConnections(
      final SentenceTheory st) {
    final Table<SynNode, SynNode, Symbol> dummyTable = HashBasedTable.create();
    final ImmutableMultimap<SynNode, SynNode> setMembers = gatherSetMembers(st);

    for (final Proposition prop : st.propositions()) {
      final PredicateType predType = prop.predType();
      final Optional<SynNode> predHead = getTerminalHead(prop);

      final ImmutableListMultimap<Symbol, SynNode> mentionTextArgs = gatherMentionTextArgs(prop);
      final ImmutableListMultimap<Symbol, SynNode> rolesArgs = gatherRolesArgs(prop);

      if (predType == Proposition.PredicateType.NAME) {
        // skip
      } else if (predType == Proposition.PredicateType.MODIFIER && predHead.isPresent()) {
        if (rolesArgs.containsKey(ROLE_REF)) {
          final List<SynNode> args = rolesArgs.get(ROLE_REF);        // there should exactly be one
          final SynNode node1 = predHead.get();
          final SynNode node2 = args.get(0);
          if (node1 != node2) {   // sanity check to prevent self referencing
            attemptToAddConnection(node1, node2, ROLE_MOD, dummyTable);
            // and now, role fall-through for set members
            final SynNode setRef = mentionTextArgs.get(ROLE_REF).get(0);
            if (setMembers.containsKey(setRef)) {
              for (final SynNode member : setMembers.get(setRef)) {
                if ((node1 != member) &&
                    usePropConnection(dummyTable, node1, member, ROLE_MOD)) {
                  //!dummyTable.contains(node1, member) && !dummyTable.contains(member, node1) ) {
                  //propConnections.put(node1, member, ROLE_MOD);
                  dummyTable.put(node1, member, ROLE_MOD);
                }
              }
            }
          }
        }
      } else if (predType == Proposition.PredicateType.POSS && predHead.isPresent()) {
        if (rolesArgs.containsKey(ROLE_POSS)) {
          final List<SynNode> args = rolesArgs.get(ROLE_POSS);        // there should exactly be one
          final SynNode node1 = predHead.get();
          final SynNode node2 = args.get(0);
          if (node1 != node2) {
            attemptToAddConnection(node1, node2, ROLE_POSS, dummyTable);
            // and now, role fall-through for set members
            final SynNode setRef = mentionTextArgs.get(ROLE_POSS).get(0);
            if (setMembers.containsKey(setRef)) {
              for (final SynNode member : setMembers.get(setRef)) {
                if ((node1 != member) &&
                    usePropConnection(dummyTable, node1, member, ROLE_POSS)) {
                  //!dummyTable.contains(node1, member) && !dummyTable.contains(member, node1) ) {
                  //propConnections.put(node1, member, ROLE_POSS);
                  dummyTable.put(node1, member, ROLE_POSS);
                }
              }
            }
          }
        }
      } else if (predType == Proposition.PredicateType.COMP) {
        if (rolesArgs.containsKey(ROLE_MEMBER)) {
          final List<SynNode> args =
              rolesArgs.get(ROLE_MEMBER);        // there should be more than one
          for (int i = 0; i < (args.size() - 1); i++) {
            for (int j = (i + 1); j < args.size(); j++) {
              final SynNode node1 = args.get(i);
              final SynNode node2 = args.get(j);
              if (node1 != node2) {
                attemptToAddConnection(node1, node2, ROLE_COMP, dummyTable);
              }
            }
          }
        }
      }
				/*
				else if(predType==Proposition.PredicateType.SET) {
					if(rolesArgs.containsKey(ROLE_MEMBER)) {
						final List<SynNode> args = rolesArgs.get(ROLE_MEMBER);	// there should be more than one
						for(int i=0; i<(args.size()-1); i++) {
							for(int j=(i+1); j<args.size(); j++) {
								final SynNode node1 = args.get(i);
								final SynNode node2 = args.get(j);
								if(node1 != node2) {
									if(!dummyTable.contains(node1, node2) && !dummyTable.contains(node2, node1)) {
										propConnections.put(node1, node2, ROLE_MEMBER);
										dummyTable.put(node1, node2, ROLE_MEMBER);
										//propConnections.put(node2, node1, ROLE_MEMBER);
									}
								}
							}
						}
					}
				}
				*/
      else if (predType == Proposition.PredicateType.LOC) {
        if (rolesArgs.containsKey(ROLE_REF) && rolesArgs.containsKey(ROLE_LOC)) {
          final List<SynNode> node1 =
              rolesArgs.get(ROLE_REF);                // there should only be one
          final List<SynNode> node2 =
              rolesArgs.get(ROLE_LOC);                // there should only be one
          if (node1.get(0) != node2.get(0)) {
            attemptToAddConnection(node1.get(0), node2.get(0), ROLE_LOC, dummyTable);
            // and now, role fall-through for set members
            final SynNode setRef = mentionTextArgs.get(ROLE_LOC).get(0);
            if (setMembers.containsKey(setRef)) {
              for (final SynNode member : setMembers.get(setRef)) {
                if ((node1.get(0) != member) &&
                    usePropConnection(dummyTable, node1.get(0), member, ROLE_LOC)) {
                  //!dummyTable.contains(node1.get(0), member) && !dummyTable.contains(member, node1.get(0)) ) {
                  //propConnections.put(node1.get(0), member, ROLE_LOC);
                  dummyTable.put(node1.get(0), member, ROLE_LOC);
                }
              }
            }
          }
        }
      } else if ((predType == Proposition.PredicateType.COPULA
                      || predType == Proposition.PredicateType.VERB) && predHead
          .isPresent()) {        // predHead should be present
        final SynNode node1 = predHead.get();
        for (final Map.Entry<Symbol, SynNode> entry : rolesArgs.entries()) {
          final Symbol role = entry.getKey();
          final SynNode node2 = entry.getValue();
          if (node1 != node2) {
            attemptToAddConnection(node1, node2, role, dummyTable);
          }
        }
        // and now, role fall-through for set members
        for (final Map.Entry<Symbol, SynNode> entry : mentionTextArgs.entries()) {
          final Symbol role = entry.getKey();
          final SynNode node2 = entry.getValue();
          if (node1 != node2) {
            if (setMembers.containsKey(node2)) {
              for (final SynNode member : setMembers.get(node2)) {
                if ((node1 != member) &&
                    usePropConnection(dummyTable, node1, member, role)) {
                  //!dummyTable.contains(node1, member) && !dummyTable.contains(member, node1) ) {
                  //propConnections.put(node1, member, role);
                  dummyTable.put(node1, member, role);
                }
              }
            }
          }
        }
      } else if ((predType == Proposition.PredicateType.NOUN
                      || predType == Proposition.PredicateType.PRONOUN) && predHead.isPresent()) {
        final SynNode node1 = predHead.get();
        for (final Map.Entry<Symbol, SynNode> entry : rolesArgs.entries()) {
          final Symbol role = entry.getKey();
          final SynNode node2 = entry.getValue();
          if ((role != ROLE_REF) && (node1 != node2)) {
            attemptToAddConnection(node1, node2, role, dummyTable);
          }
        }
        // and now, role fall-through for set members
        for (final Map.Entry<Symbol, SynNode> entry : mentionTextArgs.entries()) {
          final Symbol role = entry.getKey();
          final SynNode node2 = entry.getValue();
          if ((role != ROLE_REF) && node1 != node2) {
            if (setMembers.containsKey(node2)) {
              for (final SynNode member : setMembers.get(node2)) {
                if ((node1 != member) &&
                    usePropConnection(dummyTable, node1, member, role)) {
                  //!dummyTable.contains(node1, member) && !dummyTable.contains(member, node1) ) {
                  //propConnections.put(node1, member, role);
                  dummyTable.put(node1, member, role);
                }
              }
            }
          }
        }
      }

      //}
    }

    return TableUtils.copyOf(ByRowColKeyGornAddresses.immutableSortedCopy(dummyTable.cellSet()));
  }

  private static final Function<SynNode, String> ToDottedGornAddress =
      new Function<SynNode, String>() {
        @Override
        public String apply(final SynNode input) {
          return input.gornAddress().toDottedString();
    }
      };

  private static Ordering<Table.Cell<SynNode, SynNode, Symbol>> ByRowColKeyGornAddresses =
      Ordering.natural().onResultOf(
          compose(ToDottedGornAddress,
              TableUtils.<SynNode, SynNode, Symbol>toRowKeyFunction()))
          .compound(Ordering.natural().onResultOf(compose(ToDottedGornAddress,
              TableUtils.<SynNode, SynNode, Symbol>toColumnKeyFunction())));

  private static void attemptToAddConnection(final SynNode source, final SynNode target,
      final Symbol role, final Table<SynNode, SynNode, Symbol> connectionTable) {
    if (usePropConnection(connectionTable, source, target, role)) {
      connectionTable.put(source, target, role);
    }
  }

  private static ImmutableMultimap<SynNode, SynNode> gatherSetMembers(final SentenceTheory st) {
    final ImmutableMultimap.Builder<SynNode, SynNode> setMembersB = ImmutableMultimap.builder();
    // collect members of SET propositions
    for (final Proposition prop : st.propositions()) {
      final PredicateType predType = prop.predType();

      if (predType == PredicateType.SET) {
        Optional<SynNode> setRef = Optional.absent();
        Set<SynNode> members = new HashSet<SynNode>();
        for (final Argument arg : prop.args()) {
          final Optional<Symbol> role = arg.role();
          Optional<SynNode> argHead = Optional.absent();
          if (arg instanceof MentionArgument) {
            argHead = Optional.of(getHead((MentionArgument) arg));
          } else if (arg instanceof TextArgument) {
            argHead = Optional.of(getHead((TextArgument) arg));
          }
          if (role.isPresent() && argHead.isPresent()) {
            if (role.get() == ROLE_REF) {
              setRef = argHead;
            } else if (role.get() == ROLE_MEMBER) {
              members.add(getTerminalHead(argHead.get()));
            }
          }
        }
        if (setRef.isPresent()) {
          setMembersB.putAll(setRef.get(), members);
        }
      }
    }
    return setMembersB.build();
  }

  private static ImmutableListMultimap<Symbol, SynNode> gatherRolesArgs(final Proposition prop) {
    ImmutableListMultimap.Builder<Symbol, SynNode> rolesArgs = ImmutableListMultimap.builder();
    for (final Argument arg : prop.args()) {
      if (arg.role().isPresent()) {
        final Symbol role = arg.role().get();

        if (arg instanceof MentionArgument) {
          final SynNode argHead = getTerminalHead((MentionArgument) arg);
          rolesArgs.put(role, argHead);
        } else if (arg instanceof TextArgument) {
          final SynNode argHead = getTerminalHead((TextArgument) arg);
          rolesArgs.put(role, argHead);
        } else if (arg instanceof PropositionArgument) {
          final Optional<SynNode> argHead = getTerminalHead((PropositionArgument) arg);
          if (argHead.isPresent()) {
            rolesArgs.put(role, argHead.get());
          }
        }
      }
    }
    return rolesArgs.build();
  }

  private static ImmutableListMultimap<Symbol, SynNode> gatherMentionTextArgs(
      final Proposition prop) {
    // use immutable classes to guarantee key iteration order
    ImmutableListMultimap.Builder<Symbol, SynNode> mentionTextArgs =
        ImmutableListMultimap.builder();        // used later for fall-through roles
    for (final Argument arg : prop.args()) {
      if (arg.role().isPresent()) {
        final Symbol role = arg.role().get();
        if (arg instanceof MentionArgument) {
          final SynNode argHead = getHead((MentionArgument) arg);
          mentionTextArgs.put(role, argHead);
        } else if (arg instanceof TextArgument) {
          final SynNode argHead = getHead((TextArgument) arg);
          mentionTextArgs.put(role, argHead);
        } else if (arg instanceof PropositionArgument) {
          final Optional<SynNode> argHead = getHead((PropositionArgument) arg);
          if (argHead.isPresent()) {
            mentionTextArgs.put(role, argHead.get());
          }
      }
      }
    }
    return mentionTextArgs.build();
  }

  public final static class PathSynNode {

    private PathSynNode(final Symbol role, final SynNode node) {
      this.role = role;
      this.node = node;
    }

    public static PathSynNode from(final Symbol role, final SynNode node) {
      return new PathSynNode(transformRole(role), node);
    }

    public Symbol getRole() {
      return role;
    }

    public SynNode getNode() {
      return node;
    }

    private static Symbol transformRole(final Symbol role) {
      final String r = role.toString();
      if (r.startsWith("<") && r.endsWith(">")) {
        return role;
      } else {
        StringBuffer s = new StringBuffer("<");
        s.append(r);
        s.append(">");
        return Symbol.from(s.toString());
      }
    }

    private final Symbol role;
    private final SynNode node;
  }

  public final static class PathNode {

    private PathNode(final SynNode node) {
      this.node = node;
      this.neighborRoles = Lists.newArrayList();
      this.neighborNodes = Lists.newArrayList();
    }

    public static PathNode from(final SynNode node) {
      return new PathNode(node);
    }

    public SynNode getNode() {
      return node;
    }

    public int numberOfNeighbor() {
      return neighborNodes.size();
    }

    public Symbol getNeighborRole(final int index) {
      return neighborRoles.get(index);
    }

    public PathNode getNeighborNode(final int index) {
      return neighborNodes.get(index);
    }

    public void addNeighbor(final Symbol role, final PathNode neighbor) {
      neighborRoles.add(role);
      neighborNodes.add(neighbor);
    }

    final SynNode node;
    List<Symbol> neighborRoles;
    List<PathNode> neighborNodes;

    @Override
    public String toString() {
      StringBuffer s = new StringBuffer("");
      s.append(node.headWord().toString());
      s.append(" |||");
      for (int i = 0; i < neighborNodes.size(); i++) {
        s.append(" ");
        s.append(neighborRoles.get(i).toString());
        s.append("_");
        s.append(neighborNodes.get(i).getNode().headWord().toString());
      }
      return s.toString();
    }
  }


  private static final Symbol ROLE_NULL = Symbol.from("NULL");
  private static final Symbol ROLE_REF = Symbol.from("<ref>");
  private static final Symbol ROLE_MOD = Symbol.from("<mod>");
  private static final Symbol ROLE_POSS = Symbol.from("<poss>");
  private static final Symbol ROLE_MEMBER = Symbol.from("<member>");
  private static final Symbol ROLE_COMP = Symbol.from("<comp>");
  private static final Symbol ROLE_LOC = Symbol.from("<loc>");

  private static final Symbol ROLE_SUB = Symbol.from("<sub>");
  private static final Symbol ROLE_OBJ = Symbol.from("<obj>");
  private static final Symbol ROLE_IOBJ = Symbol.from("<iobj>");

  private static final int maxPropPathLength = 3;
}
