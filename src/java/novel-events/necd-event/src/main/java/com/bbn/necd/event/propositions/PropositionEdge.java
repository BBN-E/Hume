package com.bbn.necd.event.propositions;

import com.bbn.bue.common.strings.offsets.CharOffset;
import com.bbn.bue.common.strings.offsets.OffsetRange;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.serif.theories.Mention;
import com.bbn.serif.theories.Proposition;
import com.bbn.serif.theories.Proposition.Argument;

import com.fasterxml.jackson.annotation.JsonAutoDetect;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.google.common.base.MoreObjects;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableSet;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import static com.google.common.base.Preconditions.checkArgument;
import static com.google.common.base.Preconditions.checkNotNull;

/**
 * Represents an edge in a {@link PropositionTree}.
 */
@JsonAutoDetect(
    fieldVisibility = JsonAutoDetect.Visibility.NONE,
    getterVisibility = JsonAutoDetect.Visibility.NONE,
    setterVisibility = JsonAutoDetect.Visibility.NONE)
public final class PropositionEdge {

  private static final Logger log = LoggerFactory.getLogger(PropositionEdge.class);

  @JsonProperty("label")
  private final PropositionRole label;
  @JsonProperty("rawLabel")
  private final Symbol rawLabel;
  @JsonProperty("node")
  private final PropositionNode node;

  private PropositionEdge(
      @JsonProperty("label") final PropositionRole label,
      @JsonProperty("rawLabel") final Symbol rawLabel,
      @JsonProperty("node") final PropositionNode node) {
    this.label = checkNotNull(label);
    this.rawLabel = checkNotNull(rawLabel);
    this.node = checkNotNull(node);
  }

  public PropositionRole label() {
    return label;
  }

  public Symbol rawLabel() {
    return rawLabel;
  }

  public PropositionNode node() {
    return node;
  }

  static PropositionEdge create(final PropositionRole label, final Symbol rawLabel,
      final PropositionNode destination) {
    return new PropositionEdge(label, rawLabel, destination);
  }

  static PropositionEdge fromArgument(final Argument arg,
      final ImmutableMap<OffsetRange<CharOffset>, Proposition> definitionalProps,
      final ImmutableSet<Mention> usedDefinitionalMentions) throws PropositionStructureException {

    // Get the role, which will be unknown at a terminal so we just use unknown
    final Symbol role;
    if (arg.role().isPresent()) {
       role = arg.role().get();
    } else {
      role = PropositionRole.TERMINAL_ROLE_SYMBOL;
    }
    final PropositionRole propositionRole = PropositionRole.fromSymbol(role);
    checkArgument(!propositionRole.equals(PropositionRole.REF_ROLE),
        "Cannot be called on a <ref> argument");

    // Create the child
    final PropositionNode child = PropositionNode.fromArgument(arg, definitionalProps,
        usedDefinitionalMentions);
    return PropositionEdge.create(propositionRole, role, child);
  }

  @Override
  public String toString() {
    return MoreObjects.toStringHelper(this)
        .add("label", label)
        .add("node", node)
        .toString();
  }
}
