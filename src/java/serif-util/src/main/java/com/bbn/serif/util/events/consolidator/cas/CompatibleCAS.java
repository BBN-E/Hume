package com.bbn.serif.util.events.consolidator.cas;

//import com.bbn.kbp.events2014.sherlock.SherlockEventArgument;

import com.bbn.serif.theories.DocTheory;
import com.bbn.serif.theories.EventMention;
import com.bbn.serif.theories.Mention;
import com.bbn.serif.util.events.consolidator.common.SieveUtils;

import com.google.common.base.Optional;
import com.google.common.collect.ImmutableSet;

public final class CompatibleCAS {

  public static boolean allAreCompatible(final ImmutableSet<EventMention.Argument> args1,
      final ImmutableSet<EventMention.Argument> args2, final CanonicalArgumentString cas, final DocTheory doc) {

    for (final EventMention.Argument arg1 : args1) {
      for (final EventMention.Argument arg2 : args2) {
        if (!isCasCompatible(arg1, arg2, cas, doc)) {
          return false;
        }
      }
    }
    return true;
  }

  /*
  public static boolean isCompatibleName(final EventMention.Argument arg1,
      final EventMention.Argument arg2) {
    final SingleSpanSherlockEvidence cas1 = arg1.entityMention().canonicalStringEvidence();
    final SingleSpanSherlockEvidence cas2 = arg2.entityMention().canonicalStringEvidence();

    // For English, there is no difference between using equals() and equalsIgnoreCase() here,
    // because names have consistent casing. ~ jmolina
    if (cas1.singleString().string().equals(cas2.singleString().string())) {
      return true;
    }

    if ((cas1 instanceof SerifMention) && (cas2 instanceof SerifMention)) {
      final Mention m1 = ((SerifMention) cas1).mention();
      final Mention m2 = ((SerifMention) cas2).mention();

      if (m1.mentionType() == Mention.Type.NAME && m2.mentionType() == Mention.Type.NAME) {
        if (oneContainsTheOther(cas1.singleString(), cas2.singleString())) {
          return true;
        }
      }
    }

    return false;
  }
  */

  /**
   * Two {@link EventMention.Argument}s are considered to have compatible CASes iff those CASes
   * (a) match exactly
   * (b) can be aligned to Serif mentions, and one is a name and the other is not # YS changed this to return false
   * (c) can be aligned to Serif mentions, and one contains the other
   */
  public static boolean isCasCompatible(final EventMention.Argument arg1,
      final EventMention.Argument arg2, final CanonicalArgumentString cas, final DocTheory doc) {
    final Optional<String> cas1 = cas.getCASString(arg1, doc);
    final Optional<String> cas2 = cas.getCASString(arg2, doc);

    // TODO: this fails to specify a Locale
    if (cas1.isPresent() && cas2.isPresent() && cas1.get().equalsIgnoreCase(cas2.get())) {
      return true;
    }

    final Optional<Mention> m1Opt = SieveUtils.getEntityMention(arg1);
    final Optional<Mention> m2Opt = SieveUtils.getEntityMention(arg2);

    if(m1Opt.isPresent() && m2Opt.isPresent()) {
      final Mention m1 = m1Opt.get();
      final Mention m2 = m2Opt.get();

      if (m1.mentionType() == Mention.Type.NAME && m2.mentionType() == Mention.Type.NAME) {
        return oneContainsTheOther(cas1.get(), cas2.get());
      } else {
        return m1.span().toString().compareTo(m2.span().toString())==0;
        //return m1.mentionType() == Mention.Type.NAME || m2.mentionType() == Mention.Type.NAME;
        //return false;
      }
    }
    return false;
  }

  private static boolean oneContainsTheOther(final String string1, final String string2) {
    // lowercasing should use a locale
    final String s1 = " " + string1.toLowerCase() + " ";
    final String s2 = " " + string2.toLowerCase() + " ";

    return s1.contains(s2) || s2.contains(s1);
  }


}
