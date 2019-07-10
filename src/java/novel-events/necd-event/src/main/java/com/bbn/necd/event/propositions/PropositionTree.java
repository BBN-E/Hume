package com.bbn.necd.event.propositions;

import com.bbn.bue.common.strings.offsets.CharOffset;
import com.bbn.bue.common.strings.offsets.OffsetRange;
import com.bbn.necd.event.propositions.PropositionTreeEventInstanceExtractor.PropositionTreePathFilter;
import com.bbn.necd.event.wrappers.MentionInfo;
import com.bbn.serif.theories.Mention;
import com.bbn.serif.theories.Proposition;

import com.fasterxml.jackson.annotation.JsonAutoDetect;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.google.common.base.Optional;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableSet;

import static com.google.common.base.Preconditions.checkNotNull;

/**
 * A proposition tree.
 *
 * Due to serialization issues, we cannot use a standard graph library (i.e., JUNG).
 */
@JsonAutoDetect(
    fieldVisibility = JsonAutoDetect.Visibility.ANY,
    getterVisibility = JsonAutoDetect.Visibility.NONE,
    setterVisibility = JsonAutoDetect.Visibility.NONE)
public final class PropositionTree {

  private final PropositionNode root;

  public PropositionTree(@JsonProperty("root") final PropositionNode root) {
    this.root = checkNotNull(root);
  }

  public PropositionNode root() {
    return root;
  }

  public static PropositionTree from(final Proposition proposition,
      final ImmutableMap<OffsetRange<CharOffset>, Proposition> definitionalProps)
      throws PropositionStructureException {
    final PropositionNode root = PropositionNode.fromRootProposition(proposition, definitionalProps);
    return new PropositionTree(root);
  }

  public Optional<PropositionTreePathFilter> pathToMention(final Mention mention) {
    return pathToMention(mention, ImmutableSet.<MentionInfo>of());
  }

  public Optional<PropositionTreePathFilter> pathToMention(final Mention mention,
      final ImmutableSet<MentionInfo> avoidMentions) {
    return root.pathToMention(mention, avoidMentions);
  }

  public String prettyPrint() {
    return "Root: " + root.prettyPrint();
  }
}
