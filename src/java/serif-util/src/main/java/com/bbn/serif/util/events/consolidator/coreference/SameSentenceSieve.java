package com.bbn.serif.util.events.consolidator.coreference;

import com.bbn.serif.theories.DocTheory;
import com.bbn.serif.theories.EventMention;
import com.bbn.serif.util.events.consolidator.cas.CanonicalArgumentString;
import com.bbn.serif.util.events.consolidator.common.DocumentInfo;
import com.bbn.serif.util.events.consolidator.common.EventCandidate;
import com.bbn.serif.util.events.consolidator.common.PlaceContainmentCache;
import com.bbn.serif.util.events.consolidator.common.PropPathCache;
import com.bbn.serif.util.events.consolidator.common.SieveUtils;

import com.google.common.collect.ImmutableList;

import static com.google.common.base.Preconditions.checkNotNull;

/**
 * Combine event frames from the same sentence
 */
public final class SameSentenceSieve {

  //private final WordCategoryCache wordCategoryCache;
  private final ConnectiveInfo connectiveInfo;
  private final TypeSpecificConstraints typeSpecificConstraints;
  //private final Set<MergeFilter> mergeFilters;
  private final PlaceContainmentCache placeContainmentCache;
  private final PropPathCache propPathCache;
  private final CanonicalArgumentString cas;
  /*
  @Inject
  private SameSentenceSieve(final WordCategoryCache wordCategoryCache,
      final com.bbn.kbp.linking.sieve.Connectives connectives, final TypeSpecificConstraints typeSpecificConstraints,
      final SentenceInfoCache sentenceInfo, final Set<MergeFilter> mergeFilters) {
    this.wordCategoryCache = checkNotNull(wordCategoryCache);
    this.connectiveInfo = new ConnectiveInfo(connectives, sentenceInfo);
    this.typeSpecificConstraints = checkNotNull(typeSpecificConstraints);
    this.mergeFilters = checkNotNull(mergeFilters);
  }
  */

  public SameSentenceSieve(final SieveKnowledge sieveKnowledge, final DocumentInfo documentInfo) {
    this.connectiveInfo = new ConnectiveInfo(sieveKnowledge.connectives(), documentInfo);
    this.typeSpecificConstraints = checkNotNull(sieveKnowledge.typeSpecificConstraints());
    this.placeContainmentCache = documentInfo.placeContainmentCache();
    this.propPathCache = documentInfo.propPathCache();
    this.cas = sieveKnowledge.cas();
  }

  //public SameSentenceSieve(final Connectives connectives, final TypeSpecificConstraints typeSpecificConstraints, final SentenceInfoCache sentenceInfo) {
    //this.wordCategoryCache = checkNotNull(wordCategoryCache);
  //  this.connectiveInfo = new ConnectiveInfo(connectives, sentenceInfo);
  //  this.typeSpecificConstraints = checkNotNull(typeSpecificConstraints);
    //this.mergeFilters = checkNotNull(mergeFilters);
  //}

  /*
  @Override
  Set<SherlockDocumentEvent> siftSingleEventType(final Symbol eventType, final DocTheory doc,
      final Set<SherlockDocumentEvent> inputEventFrames) {
    final ImmutableMultimap<Integer, SherlockDocumentEvent> sentencesEventFrames =
        SieveUtils.aggregateEventFramesBySentence(inputEventFrames);

    final ImmutableSet.Builder<SherlockDocumentEvent> newEventFrames = ImmutableSet.builder();

    // for each sentence's event frames
    for (final Collection<SherlockDocumentEvent> efs : sentencesEventFrames.asMap().values()) {

      ImmutableSet<SherlockDocumentEvent> previousSentenceFrames = ImmutableSet.of();
      ImmutableSet<SherlockDocumentEvent> currentSentenceFrames =
          ImmutableSet.copyOf(SieveUtils.firstAnchorArgumentStart.immutableSortedCopy(efs));

      // repeatedly apply our sentence-level combination rules until we are making no more progress
      // or we have iterated 100 times (arbitrarily large number to prevent infinite loops)
      int earlyStop = 0;
      while (!currentSentenceFrames.equals(previousSentenceFrames) && earlyStop < 100) {
        previousSentenceFrames = currentSentenceFrames;
        currentSentenceFrames = combineAtMostOneEligibleEventPair(doc, currentSentenceFrames);
        earlyStop++;
      }
      newEventFrames.addAll(currentSentenceFrames);
    }

    Event e = Event();
    doc.documentEvents();
    return newEventFrames.build();
  }
  */

  public ImmutableList<EventCandidate> runSieve(final DocTheory doc, final ImmutableList<EventCandidate> events) {
    // first, let's make sure that we are only given events of the same sentence
    ImmutableList.Builder<Integer> sentenceNumbers = ImmutableList.builder();
    for(final EventCandidate event : events) {
      sentenceNumbers.addAll(event.getSentenceNumbers());
    }
    assert sentenceNumbers.build().size() == 1;

    //final ArrayList<EventCandidate> sortedEvents = SieveUtils.sortedEventCandidatesByAnchor((EventCandidate[]) events.toArray());
    ImmutableList<EventCandidate> previousSentenceFrames = ImmutableList.of();
    ImmutableList<EventCandidate> currentSentenceFrames =
        ImmutableList.copyOf(SieveUtils.sortedEventCandidatesByAnchor(events));

    // repeatedly apply our sentence-level combination rules until we are making no more progress
    // or we have iterated 100 times (arbitrarily large number to prevent infinite loops)
    int earlyStop = 0;
    while (!currentSentenceFrames.equals(previousSentenceFrames) && earlyStop < 100) {
      previousSentenceFrames = currentSentenceFrames;
      currentSentenceFrames = combineAtMostOneEligibleEventPair(doc, currentSentenceFrames);
      earlyStop++;
    }

    return currentSentenceFrames;
  }

  // Finds the first eligible event-frame pair according to conflict conditions and merges them
  // returning a set that differs only by that one merged pair or doesn't differ at all if no
  // event-frame pairs were eligible for merging.
  private ImmutableList<EventCandidate> combineAtMostOneEligibleEventPair(
      final DocTheory doc, final ImmutableList<EventCandidate> input) {

    final ImmutableList<EventCandidate> inputList = input.asList();

    for (int i = 0; i < input.size(); i++) {
      for (int j = i + 1; j < input.size(); j++) {

        final ImmutableList.Builder<EventCandidate> ret = ImmutableList.builder();

        final EventCandidate ef1 = inputList.get(i);
        final EventCandidate ef2 = inputList.get(j);

        //if (!hasConflict(doc, ef1, ef2) && SieveUtils.mayMerge(mergeFilters, doc, ef1, ef2)) {
        if (!hasConflict(doc, ef1, ef2)) {
          //final SherlockDocumentEvent combinedEF = SherlockDocumentEvent.builder()
          //    .eventType(ef1.eventType())
          //    .addAllArguments(ef1.arguments())
          //    .addAllArguments(ef2.arguments())
          //    .derivation(SherlockUtils.deriveFromRuleOnly("CombineSubjectToConstraints"))
          //    .build();
          //ret.add(combinedEF);

          final int earlierIndex = i <= j? i : j;

          for (int k = 0; k < input.size(); k++) {
            if(k == earlierIndex) {
              final ImmutableList.Builder<EventMention> emsBuilder = ImmutableList.builder();
              emsBuilder.addAll(ef1.eventMentions());
              emsBuilder.addAll(ef2.eventMentions());
              //ArrayList<EventMention> combinedEventMentions = Lists.newArrayList(ef1.eventMentions());
              //combinedEventMentions.addAll(ef2.eventMentions());
              ret.add(new EventCandidate(doc, ef1.type(), emsBuilder.build()));
            } else if (k != i && k != j) {
              ret.add(inputList.get(k));
            }
          }
          return ret.build();
        }
      }
    }
    return input;
  }

  private boolean hasConflict(final DocTheory doc,
      final EventCandidate ef1, final EventCandidate ef2) {

    if(!ef1.eventMentions().get(0).type().equalTo(ef2.eventMentions().get(0).type())) {
      return true;
    }

    final boolean conflictOnEventRole =
        typeSpecificConstraints.conflictsOnArgumentsForEventRole(doc, ef1, ef2, this.placeContainmentCache, this.propPathCache, this.cas);
    final boolean conflictOnAnchorPostag = SieveGeneralRules.conflictsOnAnchorPostag(ef1, ef2);

    final boolean conflictOnLifeMarry = typeSpecificConstraints.conflictsOnLifeMarry(ef1, ef2, doc, this.cas);
    final boolean conflictOnBusinessMergeOrg = typeSpecificConstraints
        .conflictsOnBusinessMergeOrg(ef1, ef2, doc, this.cas);

    //final boolean conflictOnEventClasses =
    //    wordCategoryCache.conflictsOnIncompatibleEventClasses(ef1, ef2);
    //final boolean conflictOnInvoluntary = wordCategoryCache.conflictsOnInvoluntary(ef1, ef2);

    final Indicators connectiveIndicators = connectiveInfo.getIndicators(doc, ef1, ef2);

    return conflictOnEventRole || conflictOnAnchorPostag || conflictOnLifeMarry ||
        conflictOnBusinessMergeOrg ||
        //conflictOnEventClasses || conflictOnInvoluntary ||
        connectiveIndicators.hasSingleDisjunctionInBetween() ||
        connectiveIndicators.hasCommaAndDisjunctionAroundSecondSpan() ||
        connectiveIndicators.hasSemiColonInBetween() ||
        connectiveIndicators.hasQuoteInBetween() ||
        connectiveIndicators.hasTemporalSynchronousInBetween() ||
        connectiveIndicators.hasCauseInBetween() ||
        connectiveIndicators.hasPreventionInBetween();
  }



}

