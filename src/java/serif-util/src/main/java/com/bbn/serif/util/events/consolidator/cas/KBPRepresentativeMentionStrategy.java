package com.bbn.serif.util.events.consolidator.cas;

import com.bbn.bue.common.parameters.Parameters;
import com.bbn.nlp.languages.LanguageSpecific;
import com.bbn.serif.coreference.representativementions.FocusedRepresentativeMentionStrategy;
import com.bbn.serif.coreference.representativementions.RepresentativeMentionUtils;
import com.bbn.serif.theories.Entity;
import com.bbn.serif.theories.Mention;
import com.bbn.serif.theories.Spanning;
import com.bbn.serif.theories.Spannings;
import com.google.common.base.Function;
import com.google.common.base.Functions;
import com.google.common.base.Predicates;
import com.google.common.collect.FluentIterable;
import com.google.common.collect.Ordering;
import com.google.common.collect.Range;

import static com.bbn.serif.theories.Mention.OfType;
import static com.google.common.collect.Iterables.filter;

public final class KBPRepresentativeMentionStrategy implements FocusedRepresentativeMentionStrategy {
    private KBPRepresentativeMentionStrategy() {

    }

    // if on, the CAS of a desc is always itself. At worst it
    // gets INEXACT and doesn't risk wrongness
    private boolean useLocalDescs;
    // do not allow strings containing http to be CASes
    private boolean blockHTTP;
    // do not allow excessively long names to be CASes
    private boolean blockLongNames;
    // if on, the CAS of a name is always itself. At worst
    // it gets INEXACT and doesn't risk wrongness
    private boolean resolveNamesLocally;

    private KBPRepresentativeMentionStrategy(boolean useLocalDescs,
        boolean blockHTTP, boolean blockLongNames, boolean resolveNamesLocally)
    {
        this.useLocalDescs = useLocalDescs;
        this.blockHTTP = blockHTTP;
        this.blockLongNames = blockLongNames;
        this.resolveNamesLocally = resolveNamesLocally;
    }

    public static KBPRepresentativeMentionStrategy createFromParameters(Parameters params) {
        return new KBPRepresentativeMentionStrategy(
                params.getBoolean("useLocalCASForDescs"),
                params.getBoolean("blockHTTP"),
                params.getBoolean("blockLongNames"),
                params.getBoolean("resolveNamesLocally"));
    }

    public static Builder builder() {
        return new Builder();
    }

    /** This copies code directly from {@link com.bbn.serif.coreference.representativementions.DefaultFocusedRepresentativeMentionStrategy}
     * and {@link com.bbn.serif.coreference.representativementions.DefaultRepresentativeMentionFinder}, which is
     * usually a no-no, but in this case since it is a crucial component of an eval system, we want to
     * control exactly what is happening.
     *
     * @param e
     * @param m
     * @return
     */
    @Override
    public Entity.RepresentativeMention representativeMentionForEntity(Entity e, Mention m) {
        // for KBP, we prefer descs to be resolved locally when no name is available
        // because the scorer metric rewards this
        if (useLocalDescs && m.mentionType() == Mention.Type.DESC && !e.hasNameMention()) {
            return Entity.RepresentativeMention.from(e, m);
        }

        if (resolveNamesLocally && m.mentionType() == Mention.Type.NAME) {
            return Entity.RepresentativeMention.from(e, m);
        }

        if (e.hasNameMention()) {
            return handleEntitiesWithNames(e);
        } else if (e.hasDescMention()) {
            return handleEntitiesWithDescs(e, m);
        } else {
            // a pronoun is all we've got...
            return Entity.RepresentativeMention.from(e, m);
        }
    }

    public Entity.RepresentativeMention handleEntitiesWithDescs(Entity e, Mention m) {
        if (m.isPronoun()) {
            final Ordering<Spanning> descOrdering =
                    // prefer the closest mention to the focusMention by sentence distance
                    Spannings.InCloserSentenceTo(m)
                            // break ties by the earlier mention, then the longer mention
                            .compound(Spannings.EarliestThenLongest);

            // restrict our options to DESC mentions
            // we are assured at the call site of this method that this maximum
            // exists
            return Entity.RepresentativeMention.from(e,
                    descOrdering.max(FluentIterable.from(e).filter(OfType(Mention.Type.DESC))));
        } else {
            return Entity.RepresentativeMention.from(e,
                    Spannings.EarliestThenLongest.max(
                            filter(e, OfType(Mention.Type.DESC))));
        }
    }

    public Entity.RepresentativeMention handleEntitiesWithNames(Entity e) {
        // highest priority: prefer countries
        Ordering<Mention> ordering = RepresentativeMentionUtils.PreferCountries;
        if (blockHTTP) {
            // if activated, only take a string with HTTP if we must
            ordering = ordering.compound(NotHttp);
        }
        // if activated, only take an excessively long name if we must
        if (blockLongNames) {
            ordering = ordering.compound(NotTooLong);
        }
        // in all other cases, take the longest atomic string we can get
        ordering = ordering.compound(Mention.ByAtomicStringLength);

        final Mention ret = ordering.max(
                // only consider those mentions of type NAME
                filter(e, OfType(Mention.Type.NAME)));

        return Entity.RepresentativeMention.from(e, ret, ret.atomicHead().span());
    }


    // true is ordered as greater than false, so we must reverse
    @LanguageSpecific("locale")
    private static Ordering<Mention> NotHttp = Ordering.natural().onResultOf(new Function<Mention, Boolean>() {
        @Override
        public Boolean apply(Mention m) {
            return m.span().tokenizedText().utf16CodeUnits().toLowerCase().contains("http");
        }
    }).reverse();

    private static Ordering<Mention> NotTooLong = Ordering.natural().onResultOf(
            Functions.forPredicate(Predicates.compose(Range.atMost(35), Mention.AtomicStringLength)));

    public static class Builder {
        private boolean useLocalDescs = false;
        private boolean blockHTTP = false;
        private boolean blockLongNames = false;
        private boolean resolveNamesLocally = false;

        private Builder() {}

        public Builder useLocalDescriptions() {
            useLocalDescs = true;
            return this;
        }

        public Builder blockHTTP() {
            blockHTTP = true;
            return this;
        }

        public Builder blockLongNames() {
            blockLongNames = true;
            return this;
        }

        public Builder resolveNamesLocally() {
            resolveNamesLocally = true;
            return this;
        }

        public KBPRepresentativeMentionStrategy build() {
            return new KBPRepresentativeMentionStrategy(useLocalDescs, blockHTTP,
                    blockLongNames, resolveNamesLocally);
        }
    }
}
