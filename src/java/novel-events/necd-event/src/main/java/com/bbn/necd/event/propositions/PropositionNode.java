package com.bbn.necd.event.propositions;

import com.bbn.bue.common.strings.offsets.CharOffset;
import com.bbn.bue.common.strings.offsets.OffsetRange;
import com.bbn.necd.event.propositions.PropositionTreeEventInstanceExtractor.PropositionTreePathFilter;
import com.bbn.necd.event.wrappers.MentionInfo;
import com.bbn.necd.event.wrappers.SynNodeInfo;
import com.bbn.serif.theories.Mention;
import com.bbn.serif.theories.Proposition;
import com.bbn.serif.theories.Proposition.Argument;
import com.bbn.serif.theories.Proposition.MentionArgument;
import com.bbn.serif.theories.Proposition.PropositionArgument;
import com.bbn.serif.theories.Proposition.TextArgument;

import com.fasterxml.jackson.annotation.JsonAutoDetect;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.google.common.base.MoreObjects;
import com.google.common.base.Optional;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableSet;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.List;

import javax.annotation.Nullable;

import static com.bbn.necd.event.propositions.PropositionPredicateType.fromPredicateType;
import static com.google.common.base.Preconditions.checkNotNull;

/**
 * A node in a {@link PropositionTree}.
 */
@JsonAutoDetect(
    fieldVisibility = JsonAutoDetect.Visibility.ANY,
    getterVisibility = JsonAutoDetect.Visibility.NONE,
    setterVisibility = JsonAutoDetect.Visibility.NONE)
public final class PropositionNode {

  private static final Logger log = LoggerFactory.getLogger(PropositionNode.class);

  private final PropositionPredicateType predType;
  private final ImmutableList<PropositionEdge> children;

  @Nullable
  private final SynNodeInfo head;
  @Nullable
  private final MentionInfo mention;

  private PropositionNode(
      @JsonProperty("predType") final PropositionPredicateType predType,
      @JsonProperty("children") final ImmutableList<PropositionEdge> children,
      @JsonProperty("head") @Nullable final SynNodeInfo head,
      @JsonProperty("mention") @Nullable final MentionInfo mention) {
    this.predType = checkNotNull(predType);
    this.children = checkNotNull(children);
    // Nullable
    this.head = head;
    this.mention = mention;
  }

  public PropositionPredicateType predType() {
    return predType;
  }

  public Optional<SynNodeInfo> head() {
    return Optional.fromNullable(head);
  }

  public Optional<MentionInfo> mention() {
    return Optional.fromNullable(mention);
  }

  public ImmutableList<PropositionEdge> children() {
    return children;
  }

  static PropositionNode fromRootProposition(final Proposition prop,
      final ImmutableMap<OffsetRange<CharOffset>, Proposition> definitionalProps)
      throws PropositionStructureException {
    return fromProposition(prop, definitionalProps, ImmutableSet.<Mention>of());
  }

  static PropositionNode fromArgument(final Argument arg,
      final ImmutableMap<OffsetRange<CharOffset>, Proposition> definitionalProps,
      final ImmutableSet<Mention> usedDefinitionalMentions) throws PropositionStructureException {
    // Get argument type
    final PropositionArgumentType argType = PropositionArgumentType.fromArgument(arg);
    switch (argType) {
      case PROPOSITION: {
        return fromProposition(((PropositionArgument) arg).proposition(),
            definitionalProps,
            usedDefinitionalMentions);
      }
      case MENTION: {
        return fromMentionArgument((MentionArgument) arg, definitionalProps,
            usedDefinitionalMentions);
      }
      case TEXT: {
        return fromTextArgument((TextArgument) arg);
      }
      default:
        throw new RuntimeException("Unhandled argument type");
    }
  }


  /**
   * Returns the best path to the specified mention from this node. Requires that the path not
   * include any mentions specified using {@code avoidMentions}.
   */
  public Optional<PropositionTreePathFilter> pathToMention(final Mention mention,
      final ImmutableSet<MentionInfo> avoidMentions) {
    return pathToMention(mention.span().charOffsetRange(), avoidMentions);
  }

  // This is changed to OffsetRange, since we won't have access to the actual Mention class at all times.
  public Optional<PropositionTreePathFilter> pathToMention(final OffsetRange<CharOffset> mention,
      final ImmutableSet<MentionInfo> avoidMentions) {

    // Track arguments' return values
    final ImmutableList.Builder<Optional<PropositionTreePathFilter>> argResultsBuilder = ImmutableList.builder();

    // First, check the arguments themselves
    for (final PropositionEdge edge : children) {
      final PropositionNode node = edge.node();
      // If we find the mention as an argument, return immediately with the same filter we were given.
      if (node.mention().isPresent() && node.mention().get().equalTo(mention)) {
        // Getting a mention itself is always SIMPLE, but the EventFilter may be changed by a previous call
        return Optional.of(PropositionTreePathFilter
            .create(this, ImmutableList.of(edge), EventFilter.SIMPLE));
      } else if (node.mention().isPresent() && avoidMentions.contains(node.mention().get())) {
        // Check if this is another actor mention in the sentence and skip.
        //noinspection UnnecessaryContinue
        continue;
      } else {
        // Otherwise, recurse but set the filter appropriately
        Optional<PropositionTreePathFilter> result = edge.node().pathToMention(mention,
            avoidMentions);
        // If this result would cross a boundary and the path is longer than one, set filter to EventFilter.ALL
        if (result.isPresent() && !EventFilter.SIMPLE.allowsPath(edge) && result.get().path().size() > 1) {
          result = Optional.of(PropositionTreePathFilter.create(result.get().root(),
              result.get().path(), EventFilter.ALL));
        }
        // Add in the root edge to this
        if (result.isPresent()) {
          result = Optional.of(PropositionTreePathFilter.create(this,
              ImmutableList.<PropositionEdge>builder().add(edge).addAll(result.get().path()).build(),
              result.get().filter()));
          argResultsBuilder.add(result);
        }
      }
    }

    // Get the best result
    final ImmutableList<Optional<PropositionTreePathFilter>> argResults = argResultsBuilder.build();
    // As we have optionals here, just picking the best in a loop is simpler than declaring an ordering over the
    // Optional<List>> paths
    int shortestLength = Integer.MAX_VALUE;
    PropositionTreePathFilter shortestPath = null;
    for (final Optional<PropositionTreePathFilter> optPathFilter : argResults) {
      if (optPathFilter.isPresent() && optPathFilter.get().path().size() < shortestLength) {
        shortestPath = optPathFilter.get();
        shortestLength = optPathFilter.get().path().size();
      }
    }

    // Validate root
    if (shortestPath != null && shortestPath.root() != this) {
      log.error("Incorrect root: {}", shortestPath.root());
    }

    return Optional.fromNullable(shortestPath);
  }

  // get all paths of a max path length
  public ImmutableList<ImmutableList<PropositionEdge>> getAllPathsOfLength(final ImmutableList<PropositionEdge> pathFromRoot, final int maxPathLength) {
    final ImmutableList.Builder<ImmutableList<PropositionEdge>> ret = ImmutableList.builder();

    if((pathFromRoot.size()+1) >= maxPathLength) {
      for(final PropositionEdge child : children) {
        ret.add(ImmutableList.<PropositionEdge>builder().addAll(pathFromRoot).add(child).build());
      }
      return ret.build();
    }

    for (final PropositionEdge child : children) {
      final ImmutableList<PropositionEdge> pathWithChild = ImmutableList.<PropositionEdge>builder().addAll(pathFromRoot).add(child).build();
      ret.addAll(child.node().getAllPathsOfLength(pathWithChild, maxPathLength));
    }

    return ret.build();
  }

  // get all neighbor nodes of mention
  // WARNING: there is nothing to prevent the returned list from having duplicates
  public ImmutableList<PropositionEdge> getAllNeighborNodes(final OffsetRange<CharOffset> mention) {
    final ImmutableList.Builder<PropositionEdge> ret = ImmutableList.builder();

    // if myself is the target mention, then return all my children
    if(this.mention().isPresent() && this.mention().get().equalTo(mention)) {
      return children;
    }

    for (final PropositionEdge child : children) {
      final PropositionNode childNode = child.node();

      // if this child is the target mention, add myself
      if (childNode.mention().isPresent() && childNode.mention().get().equalTo(mention)) {
        ret.add(PropositionEdge.create(child.label(), child.rawLabel(), this));
      }
      ret.addAll(child.node().getAllNeighborNodes(mention));
    }

    return ret.build();
  }

  private static PropositionNode create(final SynNodeInfo head,
      final PropositionPredicateType predType, final ImmutableList<PropositionEdge> children) {
    return create(head, predType, children, null);
  }

  private static PropositionNode create(final SynNodeInfo head,
      final PropositionPredicateType predType, final ImmutableList<PropositionEdge> children,
      final MentionInfo mention) {
    return new PropositionNode(predType, children, head, mention);
  }

  @Nullable
  private static MentionInfo refMention(final List<Argument> args) {
    final Optional<MentionArgument> optArg = PropositionUtils.refArgument(args);
    if (optArg.isPresent()) {
      return MentionInfo.from(optArg.get().mention());
    } else {
      return null;
    }
  }

  private static ImmutableList<PropositionEdge> children(final List<Argument> args,
      final ImmutableMap<OffsetRange<CharOffset>, Proposition> definitionalProps,
      final ImmutableSet<Mention> usedDefinitionalMentions) throws PropositionStructureException {
    final ImmutableList.Builder<PropositionEdge> ret = ImmutableList.builder();

    // Use only non-ref arguments
    for (final Argument arg : PropositionUtils.nonRefArguments(args)) {
      ret.add(PropositionEdge.fromArgument(arg, definitionalProps, usedDefinitionalMentions));
    }
    return ret.build();
  }

  private static PropositionNode fromProposition(final Proposition prop,
      final ImmutableMap<OffsetRange<CharOffset>, Proposition> definitionalProps,
      final ImmutableSet<Mention> usedDefinitionalMentions) throws PropositionStructureException {

    // Get arguments
    final ImmutableList<PropositionEdge> children = children(prop.args(), definitionalProps,
        usedDefinitionalMentions);

    // Get mention (which may be null)
    final MentionInfo mention = refMention(prop.args());

    // Extract information for this node
    final PropositionPredicateType predType = fromPredicateType(prop.predType());
    final SynNodeInfo head = prop.predHead().isPresent()
        ? SynNodeInfo.from(prop.predHead().get())
        : null;

    return new PropositionNode(predType, children, head, mention);
  }

  private static PropositionNode fromTextArgument(final TextArgument textArg) {
    log.warn("Assuming NOUN for text argument: {}", textArg);
    return PropositionNode.create(SynNodeInfo.from(textArg.node()),
        PropositionPredicateType.NOUN, ImmutableList.<PropositionEdge>of());
  }

  private static PropositionNode fromMentionArgument(final MentionArgument arg,
      final ImmutableMap<OffsetRange<CharOffset>, Proposition> definitionalProps,
      final ImmutableSet<Mention> usedDefinitionalMentions) throws PropositionStructureException {
    final Mention mention = arg.mention();

    // Get any children by looking up its definition
    final ImmutableList<PropositionEdge> children;
    final OffsetRange<CharOffset> offsets = mention.tokenSpan().charOffsetRange();
    if (!usedDefinitionalMentions.contains(mention) && definitionalProps.containsKey(offsets)) {
      final Proposition definitionalProp = definitionalProps.get(offsets);
      // Note that we've used this mention
      final ImmutableSet<Mention> newUsedDefinitionalMentions =
          ImmutableSet.<Mention>builder().addAll(usedDefinitionalMentions).add(mention).build();
      // Recurse on a new proposition argument for the definitional proposition
      return fromProposition(definitionalProp, definitionalProps, newUsedDefinitionalMentions);
    } else {
      children = ImmutableList.of();
    }

    return PropositionNode.create(SynNodeInfo.from(mention.head()),
        PropositionPredicateType.NOUN, children, MentionInfo.from(mention));
  }

  public String prettyPrint() {
    final StringBuilder sb = new StringBuilder();
    sb.append("Type: ").append(predType).append("\n");
    sb.append("SynNode: ").append(head).append("\n");
    sb.append("Mention: ").append(mention).append("\n");
    if (!children.isEmpty()) {
      sb.append("Children:\n*****BEGIN CHILDREN*****\n");
      int i = 0;
      for (PropositionEdge child : children) {
        sb.append("Child ").append(i++).append("\n");
        sb.append("Role: ").append(child.label()).append(" Node: ")
            .append(child.node().prettyPrint());
      }
      sb.append("*****END CHILDREN*****\n");
    }
    return sb.toString();
  }

  @Override
  public String toString() {
    return MoreObjects.toStringHelper(this)
        .add("head", head)
        .add("predType", predType)
        .add("children", children)
        .add("mention", mention)
        .toString();
  }
}
