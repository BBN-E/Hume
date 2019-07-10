package com.bbn.necd.common.theory;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.common.CollectionUtils;
import com.bbn.necd.common.PropositionUtils;
import com.bbn.serif.theories.Proposition;
import com.bbn.serif.theories.Proposition.Argument;
import com.bbn.serif.theories.Proposition.MentionArgument;
import com.bbn.serif.theories.Proposition.PredicateType;
import com.bbn.serif.theories.Proposition.PropositionArgument;
import com.bbn.serif.theories.Proposition.TextArgument;
import com.bbn.serif.theories.SentenceTheory;
import com.bbn.serif.theories.SynNode;

import com.google.common.base.Objects;
import com.google.common.base.Optional;
import com.google.common.collect.HashMultimap;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableListMultimap;
import com.google.common.collect.ImmutableMultimap;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Multimap;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.List;
import java.util.Map;

public final class PropositionConnection {
  private static final Logger log = LoggerFactory.getLogger(PropositionConnection.class);

  final ImmutableMultimap<SynNodePair, PropositionInfo> connections;

  private PropositionConnection(ImmutableMultimap<SynNodePair, PropositionInfo> connections) {
    this.connections = connections;
  }

  public ImmutableMultimap<SynNodePair, PropositionInfo> getConnections() {
    return connections;
  }

  public ImmutableSet<PropositionInfo> getPropInfo(final SynNode node1, final SynNode node2) {
    final SynNodePair pair1 = SynNodePair.from(node1, node2);
    final SynNodePair pair2 = SynNodePair.from(node2, node1);

    if(connections.containsKey(pair1)) {
      return ImmutableSet.copyOf(connections.get(pair1));
    } else if(connections.containsKey(pair2)) {
      return ImmutableSet.copyOf(connections.get(pair2));
    } else {
      return ImmutableSet.of();
    }
  }

  /*
  public ImmutableSet<Symbol> getRoles(final SynNode node1, final SynNode node2) {
    final SynNodePair pair1 = SynNodePair.from(node1, node2);
    final SynNodePair pair2 = SynNodePair.from(node2, node1);

    if(connections.containsKey(pair1)) {
      return ImmutableSet.copyOf(connections.get(pair1));
    } else if(connections.containsKey(pair2)) {
      return ImmutableSet.copyOf(connections.get(pair2));
    } else {
      return ImmutableSet.of();
    }
  }
  */

  public static PropositionConnection from(final SentenceTheory st) {
    final PropositionConnection.Builder connectionsBuilder = PropositionConnection.builder();

    if(!st.parse().isPresent()) {
      return connectionsBuilder.build();
    }

    final ImmutableMultimap<SynNode, SynNode> setMembers = gatherSetMembers(st);

    for (final Proposition prop : st.propositions()) {
      final PredicateType predType = prop.predType();
      final Optional<SynNode> predHead = PropositionUtils.getTerminalHead(prop);

      final ImmutableListMultimap<Symbol, SynNode> mentionTextArgs = gatherMentionTextArgs(prop);   // prop-role -> head (of MentionArgument or TextArgument)
      final ImmutableListMultimap<Symbol, SynNode> rolesArgs = gatherRolesArgs(prop);   // prop-role -> head (of all arguments, including proposition)

      if (predType == Proposition.PredicateType.NAME) {
        // skip
      } else if (predType == Proposition.PredicateType.MODIFIER && predHead.isPresent()) {
        modifierConnection(setMembers, mentionTextArgs, rolesArgs, predHead, connectionsBuilder, prop);
      } else if (predType == Proposition.PredicateType.POSS && predHead.isPresent()) {
        possConnection(setMembers, mentionTextArgs, rolesArgs, predHead, connectionsBuilder, prop);
      } else if (predType == Proposition.PredicateType.COMP) {
        compConnection(setMembers, mentionTextArgs, rolesArgs, predHead, connectionsBuilder, prop);
      } else if (predType == Proposition.PredicateType.LOC) {
        locConnection(setMembers, mentionTextArgs, rolesArgs, predHead, connectionsBuilder, prop);
      } else if ((predType == Proposition.PredicateType.COPULA || predType == Proposition.PredicateType.VERB) && predHead.isPresent()) {
        copulaConnection(setMembers, mentionTextArgs, rolesArgs, predHead, connectionsBuilder, prop);
      } else if ((predType == Proposition.PredicateType.NOUN || predType == Proposition.PredicateType.PRONOUN) && predHead.isPresent()) {
        nounConnection(setMembers, mentionTextArgs, rolesArgs, predHead, connectionsBuilder, prop);
      }
    }

    return connectionsBuilder.build();
  }

  public int size() {
    return connections.size();
  }


  private static void modifierConnection(final ImmutableMultimap<SynNode, SynNode> setMembers,
      final ImmutableListMultimap<Symbol, SynNode> mentionTextArgs, final ImmutableListMultimap<Symbol, SynNode> rolesArgs,
      final Optional<SynNode> predHead, final PropositionConnection.Builder connectionsBuilder, final Proposition prop) {
    if (rolesArgs.containsKey(PropositionUtils.ROLE_REF)) {
      final ImmutableList<SynNode> args = rolesArgs.get(PropositionUtils.ROLE_REF);  // there should exactly be one
      final SynNode node1 = predHead.get();
      final SynNode node2 = args.get(0);
      connectionsBuilder.add(node1, node2, PropositionUtils.ROLE_MOD, prop);
      // and now, role fall-through for set members
      final SynNode setRef = mentionTextArgs.get(PropositionUtils.ROLE_REF).get(0);
      if (setMembers.containsKey(setRef)) {
        for (final SynNode member : setMembers.get(setRef)) {
          connectionsBuilder.add(node1, member, PropositionUtils.ROLE_MOD, prop);
        }
      }
    }
  }

  private static void possConnection(final ImmutableMultimap<SynNode, SynNode> setMembers,
      final ImmutableListMultimap<Symbol, SynNode> mentionTextArgs, final ImmutableListMultimap<Symbol, SynNode> rolesArgs,
      final Optional<SynNode> predHead, final PropositionConnection.Builder connectionsBuilder, final Proposition prop) {
    if (rolesArgs.containsKey(PropositionUtils.ROLE_POSS)) {
      final List<SynNode> args = rolesArgs.get(PropositionUtils.ROLE_POSS);  // there should exactly be one
      final SynNode node1 = predHead.get();
      final SynNode node2 = args.get(0);
      connectionsBuilder.add(node1, node2, PropositionUtils.ROLE_POSS, prop);
      // and now, role fall-through for set members
      final SynNode setRef = mentionTextArgs.get(PropositionUtils.ROLE_POSS).get(0);
      if (setMembers.containsKey(setRef)) {
        for (final SynNode member : setMembers.get(setRef)) {
          connectionsBuilder.add(node1, member, PropositionUtils.ROLE_POSS, prop);
        }
      }
    }
  }

  private static void compConnection(final ImmutableMultimap<SynNode, SynNode> setMembers,
      final ImmutableListMultimap<Symbol, SynNode> mentionTextArgs, final ImmutableListMultimap<Symbol, SynNode> rolesArgs,
      final Optional<SynNode> predHead, final PropositionConnection.Builder connectionsBuilder, final Proposition prop) {
    if (rolesArgs.containsKey(PropositionUtils.ROLE_MEMBER)) {
      final ImmutableList<SynNode> args = rolesArgs.get(PropositionUtils.ROLE_MEMBER);   // there should be more than one
      for (int i = 0; i < (args.size() - 1); i++) {
        for (int j = (i + 1); j < args.size(); j++) {
          final SynNode node1 = args.get(i);
          final SynNode node2 = args.get(j);
          connectionsBuilder.add(node1, node2, PropositionUtils.ROLE_COMP, prop);
        }
      }
    }
  }

  private static void locConnection(final ImmutableMultimap<SynNode, SynNode> setMembers,
      final ImmutableListMultimap<Symbol, SynNode> mentionTextArgs, final ImmutableListMultimap<Symbol, SynNode> rolesArgs,
      final Optional<SynNode> predHead, final PropositionConnection.Builder connectionsBuilder, final Proposition prop) {
    if (rolesArgs.containsKey(PropositionUtils.ROLE_REF) && rolesArgs.containsKey(PropositionUtils.ROLE_LOC)) {
      final ImmutableList<SynNode> node1 = rolesArgs.get(PropositionUtils.ROLE_REF);  // there should only be one
      final ImmutableList<SynNode> node2 = rolesArgs.get(PropositionUtils.ROLE_LOC);  // there should only be one
      if (node1.get(0) != node2.get(0)) {
        connectionsBuilder.add(node1.get(0), node2.get(0), PropositionUtils.ROLE_LOC, prop);
        final SynNode setRef = mentionTextArgs.get(PropositionUtils.ROLE_LOC).get(0);
        // and now, role fall-through for set members
        if (setMembers.containsKey(setRef)) {
          for (final SynNode member : setMembers.get(setRef)) {
            connectionsBuilder.add(node1.get(0), member, PropositionUtils.ROLE_LOC, prop);
          }
        }
      }
    }
  }

  private static void copulaConnection(final ImmutableMultimap<SynNode, SynNode> setMembers,
      final ImmutableListMultimap<Symbol, SynNode> mentionTextArgs, final ImmutableListMultimap<Symbol, SynNode> rolesArgs,
      final Optional<SynNode> predHead, final PropositionConnection.Builder connectionsBuilder, final Proposition prop) {
    final SynNode node1 = predHead.get();
    for (final Map.Entry<Symbol, SynNode> entry : rolesArgs.entries()) {
      final Symbol role = entry.getKey();
      final SynNode node2 = entry.getValue();
      connectionsBuilder.add(node1, node2, role, prop);
    }
    for (final Map.Entry<Symbol, SynNode> entry : mentionTextArgs.entries()) {
      // and now, role fall-through for set members
      final Symbol role = entry.getKey();
      final SynNode node2 = entry.getValue();
      if (node1 != node2) {
        if (setMembers.containsKey(node2)) {
          for (final SynNode member : setMembers.get(node2)) {
            connectionsBuilder.add(node1, member, role, prop);
          }
        }
      }
    }
  }

  private static void nounConnection(final ImmutableMultimap<SynNode, SynNode> setMembers,
      final ImmutableListMultimap<Symbol, SynNode> mentionTextArgs, final ImmutableListMultimap<Symbol, SynNode> rolesArgs,
      final Optional<SynNode> predHead, final PropositionConnection.Builder connectionsBuilder, final Proposition prop) {
    final SynNode node1 = predHead.get();
    for (final Map.Entry<Symbol, SynNode> entry : rolesArgs.entries()) {
      final Symbol role = entry.getKey();
      final SynNode node2 = entry.getValue();
      if (role != PropositionUtils.ROLE_REF) {
        connectionsBuilder.add(node1, node2, role, prop);
      }
    }
    for (final Map.Entry<Symbol, SynNode> entry : mentionTextArgs.entries()) {
      // and now, role fall-through for set members
      final Symbol role = entry.getKey();
      final SynNode node2 = entry.getValue();
      if ((role != PropositionUtils.ROLE_REF) && node1 != node2) {
        if (setMembers.containsKey(node2)) {
          for (final SynNode member : setMembers.get(node2)) {
            connectionsBuilder.add(node1, member, role, prop);
          }
        }
      }
    }
  }

  // SynNodeA -> SynNodeB , if SynNodeB is a (set) member of SynNodeA
  private static ImmutableMultimap<SynNode, SynNode> gatherSetMembers(final SentenceTheory st) {
    final ImmutableMultimap.Builder<SynNode, SynNode> ret = ImmutableMultimap.builder();

    for (final Proposition prop : st.propositions()) {
      if (prop.predType() == PredicateType.SET) {       // collect members of SET propositions
        Optional<SynNode> setRef = Optional.absent();
        final ImmutableSet.Builder<SynNode> members = ImmutableSet.builder();

        for (final Argument arg : prop.args()) {
          final Optional<Symbol> role = arg.role();
          if(role.isPresent() && ((arg instanceof MentionArgument) || (arg instanceof TextArgument))) {
            final SynNode argHead = (arg instanceof MentionArgument)? PropositionUtils.getTerminalHead((MentionArgument)arg) : PropositionUtils.getTerminalHead((TextArgument)arg);
            if (role.get() == PropositionUtils.ROLE_REF) {
              setRef = Optional.of(argHead);
            } else if (role.get() == PropositionUtils.ROLE_MEMBER) {
              members.add(PropositionUtils.getTerminalHead(argHead));
            }
          }
        }

        if (setRef.isPresent()) {
          ret.putAll(setRef.get(), members.build());
        }
      }
    }

    return ret.build();
  }

  private static ImmutableListMultimap<Symbol, SynNode> gatherRolesArgs(final Proposition prop) {
    final ImmutableListMultimap.Builder<Symbol, SynNode> ret = ImmutableListMultimap.builder();

    for (final Argument arg : prop.args()) {
      if (arg.role().isPresent()) {
        final Symbol role = arg.role().get();

        if (arg instanceof MentionArgument) {
          ret.put(role, PropositionUtils.getTerminalHead((MentionArgument) arg));
        } else if (arg instanceof TextArgument) {
          ret.put(role, PropositionUtils.getTerminalHead((TextArgument) arg));
        } else if (arg instanceof PropositionArgument) {
          final Optional<SynNode> argHead = PropositionUtils.getTerminalHead((PropositionArgument) arg);
          if (argHead.isPresent()) {
            ret.put(role, argHead.get());
          }
        }
      }
    }

    return ret.build();
  }

  private static ImmutableListMultimap<Symbol, SynNode> gatherMentionTextArgs(final Proposition prop) {
    final ImmutableListMultimap.Builder<Symbol, SynNode> ret = ImmutableListMultimap.builder();

    for (final Argument arg : prop.args()) {
      if (arg.role().isPresent()) {
        final Symbol role = arg.role().get();
        if (arg instanceof MentionArgument) {
          ret.put(role, PropositionUtils.getTerminalHead((MentionArgument) arg));
        } else if (arg instanceof TextArgument) {
          ret.put(role, PropositionUtils.getTerminalHead((TextArgument) arg));
        }
      }
    }

    return ret.build();
  }




  public static Builder builder() {
    return new Builder();
  }

  public static class Builder {
    final ImmutableMultimap.Builder<SynNodePair, PropositionInfo> connectionsBuilder;        // we allow for multiple roles between the same pair of SynNode
    Multimap<SynNodePair, PropositionInfo> connectedNodes;

    private Builder() {
      connectionsBuilder = ImmutableMultimap.builder();
      connectedNodes = HashMultimap.create();
    }

    public Builder add(final SynNode source, final SynNode target, final Symbol role, final Proposition prop) {
      if(source != target) {
        final SynNodePair pair = SynNodePair.from(source, target);
        final PropositionInfo propInfo = PropositionInfo.from(prop, role);

        //if(connectedNodes.containsKey(pair)) {
        //  log.info("Adding duplicate connection from {} to {} of type {}", source, target, role);
        //}

        if(!connectedNodes.containsEntry(pair, propInfo)) {
          connectionsBuilder.put(pair, propInfo);
          connectedNodes.put(pair, propInfo);
        }
      }

      return this;
    }

    public PropositionConnection build() {
      return new PropositionConnection(connectionsBuilder.build());
    }
  }

  public static class PropositionInfo {
    private final Proposition prop;
    private final Symbol role;

    private PropositionInfo(final Proposition prop, final Symbol role) {
      this.prop = prop;
      this.role = role;
    }

    public static PropositionInfo from(final Proposition prop, final Symbol role) {
      return new PropositionInfo(prop, role);
    }

    public Proposition getProp() {
      return prop;
    }

    public Symbol getRole() {
      return role;
    }

    @Override
    public int hashCode() {
      return Objects.hashCode(prop, role);
    }

    @Override
    public boolean equals(final Object obj) {
      if (this == obj) {
        return true;
      }
      if (obj == null) {
        return false;
      }
      if (getClass() != obj.getClass()) {
        return false;
      }

      final PropositionInfo other = (PropositionInfo) obj;
      return Objects.equal(prop, other.prop) && Objects.equal(role, other.role);
    }
  }

  private static class SynNodePair {
    private final SynNode node1;
    private final SynNode node2;

    private SynNodePair(final SynNode node1, final SynNode node2) {
      this.node1 = node1;
      this.node2 = node2;
    }

    public static SynNodePair from(final SynNode node1, final SynNode node2) {
      if(CollectionUtils.spanPairIsInCorrectOrder(node1.span(), node2.span())) {
        return new SynNodePair(node1, node2);
      } else {
        return new SynNodePair(node2, node1);
      }
    }

    public SynNode getFirstMember() {
      return node1;
    }

    public SynNode getSecondMember() {
      return node2;
    }

    @Override
    public int hashCode() {
      return Objects.hashCode(node1, node2);
    }

    @Override
    public boolean equals(final Object obj) {
      if(this == obj) {
        return true;
      }
      if(obj == null) {
        return false;
      }
      if(getClass() != obj.getClass()) {
        return false;
      }

      final SynNodePair other = (SynNodePair) obj;
      return (Objects.equal(node1, other.node1) && Objects.equal(node2, other.node2));
    }
  }

}
