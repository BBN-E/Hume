package com.bbn.serif.util.resolver.documentresolver;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.bue.sexp.Sexp;
import com.bbn.bue.sexp.SexpReader;
import com.bbn.bue.sexp.SexpUtils;
import com.bbn.serif.common.SerifException;
import com.bbn.serif.patterns.PatternSet;
import com.bbn.serif.patterns.PatternSetFactory;
import com.bbn.serif.patterns.matching.*;
import com.bbn.serif.theories.*;
import com.bbn.serif.util.resolver.Resolver;
import com.google.common.base.Optional;
import com.google.common.collect.ImmutableCollection;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableMultimap;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.HashSet;
import java.util.Set;

public class PatternPruner implements DocumentResolver, Resolver {

    private final ImmutableMap<Symbol, PatternSetMatcher> matcherByType;
    private final int eventContextSize;
    private final int maxEERDistance;

    // Hack: Use this to keep track of events pruned from the current doc so we can remove relevant EERs
    private Set<EventMention> prunedEvents;


    public PatternPruner(String patternFile, int eventContextSize, Optional<Integer> maxEERDistance) throws IOException {
        String patternFileContents = new String(Files.readAllBytes(Paths.get(patternFile)));

        // Create Sexp from patternString
        SexpReader sexpReader = SexpReader.builder().build();
        Sexp patternSetSexp = sexpReader.read(patternFileContents);

        // Create a separate PatternSet for each event type
        final ImmutableMap.Builder<Symbol, PatternSetMatcher> matcherMapBuilder = new ImmutableMap.Builder<>();
        ImmutableList<Sexp> sexpList = SexpUtils.getSexpArgsAsList(patternSetSexp);
        for (final Sexp sexp : sexpList) {
            System.out.println("Creating a PatternPruner pruning set for " + SexpUtils.getSexpType(sexp));
            PatternSet patternSet = PatternSetFactory.fromSexp(sexp);
            matcherMapBuilder.put(SexpUtils.getSexpType(sexp), PatternSetMatcher.of(patternSet));
        }
        this.matcherByType = matcherMapBuilder.build();

        this.eventContextSize = eventContextSize;
        System.out.println("PatternPruner Event context window size: " + this.eventContextSize);

        if (maxEERDistance.isPresent()) {
            this.maxEERDistance = maxEERDistance.get().intValue();
            System.out.println("PatternPruner will prune EERMentions with arg distance > " + this.maxEERDistance);
        } else {
            this.maxEERDistance = Integer.MAX_VALUE;
        }

        prunedEvents = new HashSet<>();
    }

    @Override
    public DocTheory resolve(DocTheory docTheory) {
        prunedEvents.clear(); // empty any existing pruned events
        final DocTheory afterSentencePruningDt = sentenceLevelPruning(docTheory);
        final DocTheory afterDocLevelPruningDt = documentLevelPruning(afterSentencePruningDt);
        return afterDocLevelPruningDt;
    }

    private DocTheory sentenceLevelPruning(DocTheory docTheory) {
        // Create a DocumentPatternMatcher for each type
        final ImmutableMap.Builder<Symbol, PatternSetMatcher.DocumentPatternMatcher> docMatcherBuilder = new ImmutableMap.Builder<>();
        for (final Symbol type: matcherByType.keySet()) {
            final PatternSetMatcher matcher = matcherByType.get(type);
            docMatcherBuilder.put(type, matcher.inContextOf(docTheory));
        }
        final ImmutableMap<Symbol, PatternSetMatcher.DocumentPatternMatcher> docMatcherByType = docMatcherBuilder.build();

        DocTheory.Builder newDTBuilder = docTheory.modifiedCopyBuilder();
        for (int i = 0; i < docTheory.numSentences(); ++i) {
            final SentenceTheory sentenceTheory = docTheory.sentenceTheory(i);

            // for each type, store all matching mentions in the sentence
            final ImmutableMap.Builder<Symbol, Set> sentMatchesByTypeBuilder = new ImmutableMap.Builder<>();
            for (final Symbol type: docMatcherByType.keySet()) {
                final PatternSetMatcher.DocumentPatternMatcher matcher = docMatcherByType.get(type);
                final PatternReturns patternReturns = matcher.findMatchesIn(sentenceTheory);
/*                for (final PatternMatch match : patternReturns.matches()) {
                    if (match.spanning().isPresent()) {
                        System.out.println("Match: (" + match.getClass().toString() + ") " + match.spanning().get().span().text().toString());
                    }
                }
 */
                sentMatchesByTypeBuilder.put(type, patternReturns.matches());
            }
            final ImmutableMap<Symbol, Set> sentMatchesByType = sentMatchesByTypeBuilder.build();

            final SentenceTheory afterEventsSt = pruneEventMentions(docTheory, sentenceTheory, sentMatchesByType);
            final SentenceTheory afterRelationsSt = pruneRelationMentions(docTheory, afterEventsSt, sentMatchesByType);
            newDTBuilder.replacePrimarySentenceTheory(sentenceTheory, afterRelationsSt);
        }
        return newDTBuilder.build();
    }

    private DocTheory documentLevelPruning(DocTheory docTheory) {
        // Create a DocumentPatternMatcher for each type
        final ImmutableMap.Builder<Symbol, PatternSetMatcher.DocumentPatternMatcher> docMatcherBuilder = new ImmutableMap.Builder<>();
        for (final Symbol type: matcherByType.keySet()) {
            final PatternSetMatcher matcher = matcherByType.get(type);
            docMatcherBuilder.put(type, matcher.inContextOf(docTheory));
        }
        final ImmutableMap<Symbol, PatternSetMatcher.DocumentPatternMatcher> docMatcherByType = docMatcherBuilder.build();

        // Do a pass over the sentences to get matches that still exist after Event and Relation pruning
        final ImmutableMultimap.Builder<Symbol, PatternMatch> docMatchesByTypeBuilder = new ImmutableMultimap.Builder<>();
        for (final Symbol type: docMatcherByType.keySet()) {
            final PatternSetMatcher.DocumentPatternMatcher matcher = docMatcherByType.get(type);
            final PatternReturns patternReturns = matcher.findMatchesInDocument();
/*            for (final PatternMatch match : patternReturns.matches()) {
                if (match.spanning().isPresent()) {
                    System.out.println("Match: (" + match.getClass().toString() + ") " + match.spanning().get().span().text().toString());
                } else {
                    System.out.println("Match: (" + match.getClass().toString() + ")");
                }
            }
*/
            docMatchesByTypeBuilder.putAll(type, patternReturns.matches());
        }
        final ImmutableMultimap<Symbol, PatternMatch> docMatchesByType = docMatchesByTypeBuilder.build();
        final DocTheory afterMissingEventsDt = pruneEERWithMissingEvents(docTheory);
        final DocTheory afterEERPatternsDt = pruneEERMentions(afterMissingEventsDt, docMatchesByType);
        final DocTheory afterEERDistanceDt = pruneLongDistanceEERMentions(afterEERPatternsDt);
        return afterEERDistanceDt;
    }

    private SentenceTheory pruneEventMentions(DocTheory dt, SentenceTheory sentenceTheory,
                                              ImmutableMap<Symbol, Set> matchesByType) {
        final ImmutableList.Builder<EventMention> retainedEventMentionsBuilder = new ImmutableList.Builder<>();
        for (final EventMention em :  sentenceTheory.eventMentions()) {
            boolean foundMatch = false;
            Symbol eventType = em.type();
            if (matchesByType.containsKey(eventType)) {
                final Set<PatternMatch> matches = matchesByType.get(eventType);
                TokenSequence.Span eventSpan = getEventSpan(em, sentenceTheory);
//                System.out.println("Event: [" + eventSpan.toString() + "] (" + eventType.toString() + ") " + eventSpan.startCharOffset() + " - " + eventSpan.endCharOffset());
                for (final PatternMatch match : matches) {
                    if (match.spanning().isPresent()) {
                        if (match instanceof EventPatternMatch) {
                            EventMention eventMention = (EventMention) match.spanning().get();
                            if (eventMention.equals(em)) {
                                foundMatch = true;
                                System.out.println("PatternPruner: removing [" + eventSpan.toString() + "]" +
                                        " EventMention: " + eventMention.toString() + " from docid " + dt.docid());
                                break;
                            }
                        } else if (match instanceof MentionPatternMatch) {
                            Mention mention = (Mention) match.spanning().get();
                            TokenSequence.Span headSpan = mention.atomicHead().span();
//                            System.out.println("    matchingMention: " + headSpan.text().toString() + " " + headSpan.startCharOffset() + " - " + headSpan.endCharOffset());
                            if (eventSpan.contains(headSpan)) {
                                foundMatch = true;
                                System.out.println("PatternPruner: removing [" + eventSpan.toString() + "] " +
                                        " Mention: " + mention.toString() + " from docid " + dt.docid());
                                break;
                            }
                        } else if (match instanceof PropPatternMatch) {
                            Proposition prop = (Proposition) match.spanning().get();
                            if (prop.predHead().isPresent()) {
                                TokenSequence.Span predHeadSpan = prop.predHead().get().span();
                                if (predHeadSpan.contains(eventSpan)) {
                                    foundMatch = true;
                                    System.out.println("PatternPruner: removing [" + eventSpan.toString() + "]" +
                                            " Proposition: " + prop.toString() + " from docid " + dt.docid());
                                    break;
                                }
                            }
                            TokenSequence.Span propSpan = prop.span();
                            if (propSpan.contains(eventSpan)) {
                                foundMatch = true;
                                System.out.println("PatternPruner: removing  [" + eventSpan.toString() + "]" +
                                        " Proposition: " + prop.toString() + " from docid " + dt.docid());
                                break;
                            }
                        } else if (match instanceof TokenSpanPatternMatch) {
                            TokenSequence.Span span = match.spanning().get().span();
                            int tokens_between  = eventSpan.numberOfTokensBetweenSpansInSameSentence(span);
                            if (tokens_between < eventContextSize) {
                                foundMatch = true;
                                System.out.println("PatternPruner: removing [" + eventSpan.toString() + "]" +
                                        " Span: " + span.originalText() + " from docid " + dt.docid());
                                break;
                            }

                        }
                    }
                }
            }
            if (!foundMatch)
                retainedEventMentionsBuilder.add(em);
            else
                prunedEvents.add(em);
        }

        return sentenceTheory.modifiedCopyBuilder().eventMentions(
                new EventMentions.Builder().eventMentions(retainedEventMentionsBuilder.build()).build())
                .build();
    }


    private SentenceTheory pruneRelationMentions(DocTheory dt, SentenceTheory sentenceTheory,
                                                 ImmutableMap<Symbol, Set> matchesByType) {
        final ImmutableList.Builder<RelationMention> retainedRelationMentionsBuilder = new ImmutableList.Builder<>();
        for (final RelationMention rm :  sentenceTheory.relationMentions()) {
            boolean foundMatch = false;
            Symbol relationType = rm.type();
            if (matchesByType.containsKey(relationType)) {
                final Set<PatternMatch> matches = matchesByType.get(relationType);
                for (final PatternMatch match : matches) {
                    if (match.spanning().isPresent()) {
                        if (match instanceof MentionPatternMatch) {
                            Mention mention = (Mention) match.spanning().get();
                            TokenSpan relationSpan = rm.tokenSpan();
//                            System.out.println("Relation: [" + relationSpan.toString() + "] (" + relationType.toString() + ") " + relationSpan.startCharOffset() + " - " + relationSpan.endCharOffset());
                            TokenSequence.Span headSpan = mention.atomicHead().span();
//                            System.out.println("    matchingMention: " + headSpan.text().toString() + " " + headSpan.startCharOffset() + " - " + headSpan.endCharOffset());
                            if (relationSpan.contains(headSpan)) {
                                foundMatch = true;
                                System.out.println("PatternPruner: removing [" + relationSpan.toString() + "]" +
                                        " Mention: " + mention.toString() + " from docid " + dt.docid());
                                break;
                            }
                        }
                    }
                }
            }
            if (!foundMatch)
                retainedRelationMentionsBuilder.add(rm);
        }

        return sentenceTheory.modifiedCopyBuilder().relationMentions(
                new RelationMentions.Builder().relationMentions(retainedRelationMentionsBuilder.build()).build())
                .build();
    }

    // Remove any EventEventRelationMentions whose argument Events were already pruned
    private DocTheory pruneEERWithMissingEvents(DocTheory docTheory) {
        final ImmutableList.Builder<EventEventRelationMention> retainedEERMentionsBuilder = new ImmutableList.Builder<>();
        for (EventEventRelationMention eer : docTheory.eventEventRelationMentions()) {
            boolean foundPrunedEvent = false;
            EventEventRelationMention.Argument leftArg = eer.leftEventMention();
            EventEventRelationMention.Argument rightArg = eer.rightEventMention();
            if (leftArg instanceof EventEventRelationMention.EventMentionArgument) {
                EventMention leftMention = ((EventEventRelationMention.EventMentionArgument) leftArg).eventMention();
                if (prunedEvents.contains(leftMention)) {
                    foundPrunedEvent = true;
                }
            } else {
                throw new SerifException("Pruning for other subclasses of EventEventRelationMention.Argument is not implemented");
            }
            if (rightArg instanceof EventEventRelationMention.EventMentionArgument) {
                EventMention rightMention = ((EventEventRelationMention.EventMentionArgument) rightArg).eventMention();
                if (prunedEvents.contains(rightMention)) {
                    foundPrunedEvent = true;
                }
            } else {
                throw new SerifException("Pruning for other subclasses of EventEventRelationMention.Argument is not implemented");
            }
            if (!foundPrunedEvent) {
                retainedEERMentionsBuilder.add(eer);
            } else {
                EventMention leftMention = ((EventEventRelationMention.EventMentionArgument) eer.leftEventMention()).eventMention();
                EventMention rightMention = ((EventEventRelationMention.EventMentionArgument) eer.rightEventMention()).eventMention();
                System.out.println("PatternPruner: removing [" + eer.toString() +
                        "] because an argument Event was pruned from docid " + docTheory.docid());
                System.out.println("\t\tArg1: [" + leftMention.toString() + "]");
                System.out.println("\t\tArg2: [" + rightMention.toString() + "]");
            }
        }
        return docTheory.modifiedCopyBuilder().eventEventRelationMentions(
                EventEventRelationMentions.create(retainedEERMentionsBuilder.build())).build();
    }

    private DocTheory pruneEERMentions(DocTheory docTheory, ImmutableMultimap<Symbol, PatternMatch> matchesByType) {
        final ImmutableList.Builder<EventEventRelationMention> retainedEERMentionsBuilder = new ImmutableList.Builder<>();
        for (EventEventRelationMention eer : docTheory.eventEventRelationMentions()) {
            boolean foundMatch = false;
            Symbol relationType = eer.relationType();
            if (matchesByType.containsKey(relationType)) {
                final ImmutableCollection<PatternMatch> matches = matchesByType.get(relationType);
//                System.out.println("EER: [" + eer.toString() + "] (" + relationType.toString() + ") ");
                for (final PatternMatch match : matches) {
                    if (match instanceof EventEventRelationPatternMatch) {
                        EventEventRelationMention eerMention = ((EventEventRelationPatternMatch) match).eventEventRelationMention();
                        if (eerMention.equals(eer)) {
                            foundMatch = true;
                            System.out.println("PatternPruner: removing [" + eer.toString() + "] from docid " + docTheory.docid());
                            EventMention leftMention = ((EventEventRelationMention.EventMentionArgument) eer.leftEventMention()).eventMention();
                            EventMention rightMention = ((EventEventRelationMention.EventMentionArgument) eer.rightEventMention()).eventMention();
                            System.out.println("\t\tArg1: [" + leftMention.toString() + "]");
                            System.out.println("\t\tArg2: [" + rightMention.toString() + "]");
                            break;
                        }
                    }
                }
            }
            if (!foundMatch)
                retainedEERMentionsBuilder.add(eer);
        }
        return docTheory.modifiedCopyBuilder().eventEventRelationMentions(
            EventEventRelationMentions.create(retainedEERMentionsBuilder.build())).build();

    }

    private DocTheory pruneLongDistanceEERMentions(DocTheory docTheory) {
        final ImmutableList.Builder<EventEventRelationMention> retainedEERMentionsBuilder = new ImmutableList.Builder<>();
        for (EventEventRelationMention eer : docTheory.eventEventRelationMentions()) {
//            System.out.println("EER: [" + eer.toString() + "] (" + eer.relationType().toString() + ") ");
            if (eer.leftEventMention() instanceof EventEventRelationMention.EventMentionArgument &&
                    eer.rightEventMention() instanceof EventEventRelationMention.EventMentionArgument) {
                EventMention leftMention = ((EventEventRelationMention.EventMentionArgument) eer.leftEventMention()).eventMention();
                EventMention rightMention = ((EventEventRelationMention.EventMentionArgument) eer.rightEventMention()).eventMention();

                TokenSequence.Span leftSpan = getEventSpan(leftMention, leftMention.sentenceTheory(docTheory));
                TokenSequence.Span rightSpan = getEventSpan(rightMention, rightMention.sentenceTheory(docTheory));
//                System.out.println("\tEvent: [" + leftMention.toString() + "] Span: [" + leftSpan.tokenizedText() + "]");
//                System.out.println("\tEvent: [" + rightMention.toString() + "] Span: [" + rightSpan.tokenizedText() + "]");

                int distance = leftSpan.numberOfTokensBetweenSpansInSameSentence(rightSpan);
//                System.out.println("\tDistance: " + distance);

                if (distance <= this.maxEERDistance) {
                    retainedEERMentionsBuilder.add(eer);
                } else {
                    System.out.println("PatternPruner: removing [" + eer.toString() + "]" +
                            " with arg distance " + distance + " from docid " + docTheory.docid());
                    System.out.println("\t\tArg1: [" + leftMention.toString() + "]");
                    System.out.println("\t\tArg2: [" + rightMention.toString() + "]");
                }
            } else {
                retainedEERMentionsBuilder.add(eer);
            }
        }
        return docTheory.modifiedCopyBuilder().eventEventRelationMentions(
                EventEventRelationMentions.create(retainedEERMentionsBuilder.build())).build();
    }


    private TokenSequence.Span getEventSpan(final EventMention em, final SentenceTheory st) {
        TokenSequence.Span result = em.anchorNode().span();
        Optional<Integer> semantic_start = em.semanticPhraseStart();
        Optional<Integer> semantic_end = em.semanticPhraseEnd();
        if (semantic_start.isPresent() && semantic_end.isPresent())
            result = st.tokenSequence().span(semantic_start.get(), semantic_end.get());
        return result;
    }
}
