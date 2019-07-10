package com.bbn.necd.common;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.serif.theories.Mention;
import com.bbn.serif.theories.Parse;
import com.bbn.serif.theories.Proposition;
import com.bbn.serif.theories.SentenceTheory;
import com.bbn.serif.theories.SynNode;
import com.bbn.serif.theories.Proposition.MentionArgument;
import com.bbn.serif.theories.Proposition.PropositionArgument;
import com.bbn.serif.theories.Proposition.TextArgument;
import com.bbn.serif.theories.ValueMention;
import com.google.common.base.Optional;

public final class PropositionUtils {
  public static SynNode getHead(final MentionArgument a) {
    return a.mention().head();
  }

  public static SynNode getHead(final TextArgument a) {
    return a.node();
  }

  public static SynNode getTerminalHead(final SynNode node) {
    SynNode curr = node;
    while (curr.head() != curr) {
      curr = curr.head();
    }
    return curr;
  }

  public static SynNode getTerminalHead(final MentionArgument a) {
    return getTerminalHead(a.mention().head());
  }

  public static SynNode getTerminalHead(final TextArgument a) {
    return getTerminalHead(a.node());
  }

  public static Optional<SynNode> getTerminalHead(final PropositionArgument a) {
    return getTerminalHead(a.proposition());
  }

  // NAME propositions predHead is absent
  // POSS propositions predHead usually points to tokens such as 's
  // So for both of the above, you'll be better off returning the head SynNode of the <ref> argument in the proposition
  public static Optional<SynNode> getTerminalHead(final Proposition prop) {
    if ((prop.predType() == Proposition.PredicateType.NAME) || (prop.predType() == Proposition.PredicateType.POSS)) {
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

  public static SynNode getTerminalHead(final Mention mention) {
    return getTerminalHead(mention.head());
  }

  public static Optional<SynNode> getTerminalHead(final ValueMention mention, final SentenceTheory st) {
    if (st.parse().isPresent()) {
      final Parse parse = st.parse().get();
      final Optional<SynNode> valueNode = parse.root().nodeByTokenSpan(mention.span());
      if (valueNode.isPresent()) {
        return Optional.of(getTerminalHead(valueNode.get()));
      }
    }
    return Optional.absent();
  }

  /*
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
*/


  public static final Symbol ROLE_NULL = Symbol.from("NULL");
  public static final Symbol ROLE_REF = Symbol.from("<ref>");
  public static final Symbol ROLE_MOD = Symbol.from("<mod>");
  public static final Symbol ROLE_POSS = Symbol.from("<poss>");
  public static final Symbol ROLE_MEMBER = Symbol.from("<member>");
  public static final Symbol ROLE_COMP = Symbol.from("<comp>");
  public static final Symbol ROLE_LOC = Symbol.from("<loc>");

  public static final Symbol ROLE_SUB = Symbol.from("<sub>");
  public static final Symbol ROLE_OBJ = Symbol.from("<obj>");
  public static final Symbol ROLE_IOBJ = Symbol.from("<iobj>");

}
