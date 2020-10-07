package com.bbn.serif.util.events.consolidator.coreference;

import com.bbn.serif.theories.DocTheory;
import com.bbn.serif.theories.EventMention;
import com.bbn.serif.util.events.consolidator.cas.CanonicalArgumentString;
import com.bbn.serif.util.events.consolidator.common.DocumentInfo;
import com.bbn.serif.util.events.consolidator.common.EventCandidate;
import com.bbn.serif.util.events.consolidator.common.PlaceContainmentCache;
import com.bbn.serif.util.events.consolidator.common.PropPathCache;

import com.google.common.collect.ImmutableList;

import static com.google.common.base.Preconditions.checkNotNull;

/**
 * Combine event frames across the doc (from different sentences)
 */
public final class DocumentSieve {

  //private final Language language;
  //private final Stemmer stemmer;
  //private final WordCategoryCache wordCategoryCache;
  private final TypeSpecificConstraints typeSpecificConstraints;
  //private final Set<MergeFilter> mergeFilters;
  private final PlaceContainmentCache placeContainmentCache;
  private final PropPathCache propPathCache;
  private final CanonicalArgumentString cas;

  /*
  @Inject
  private DocumentSieve(final Language language, @SieveLinkerM.SieveStemmerP final Stemmer stemmer,
      final WordCategoryCache wordCategoryCache, final TypeSpecificConstraints typeSpecificConstraints,
      final Set<MergeFilter> mergeFilters) {
    this.language = checkNotNull(language);
    this.stemmer = checkNotNull(stemmer);
    this.wordCategoryCache = checkNotNull(wordCategoryCache);
    this.typeSpecificConstraints = checkNotNull(typeSpecificConstraints);
    this.mergeFilters = checkNotNull(mergeFilters);
  }
  */

  public DocumentSieve(final SieveKnowledge sieveKnowledge, final DocumentInfo documentInfo) {
    //this.language = checkNotNull(sieveKnowledge.language());
    //this.stemmer = checkNotNull(sieveKnowledge.stemmer());
    //this.wordCategoryCache = checkNotNull(wordCategoryCache);
    this.typeSpecificConstraints = checkNotNull(sieveKnowledge.typeSpecificConstraints());
    //this.mergeFilters = checkNotNull(mergeFilters);
    this.placeContainmentCache = documentInfo.placeContainmentCache();
    this.propPathCache = documentInfo.propPathCache();
    this.cas = sieveKnowledge.cas();
  }

  /*
  @Override
  Set<SherlockDocumentEvent> siftSingleEventType(final Symbol eventType, final SherlockDocument doc,
      final Set<SherlockDocumentEvent> inputEventFrames) {

    final ImmutableMultimap<Integer, SherlockDocumentEvent> sentencesEventFrames =
        SieveUtils.aggregateEventFramesBySentence(inputEventFrames);

    final ImmutableList<ImmutableList<SherlockDocumentEvent>> sentenceSortedEFs =
        toSentenceSortedOrder(sentencesEventFrames); // for each sentence, a List of EventFrames

    return combineEventFramesAcrossSentences(doc, sentenceSortedEFs, Combination.COMBINATION_ALL);
  }

  private static ImmutableList<ImmutableList<SherlockDocumentEvent>> toSentenceSortedOrder(
      final ImmutableMultimap<Integer, SherlockDocumentEvent> sentenceEASet) {

    final ImmutableList.Builder<ImmutableList<SherlockDocumentEvent>> ret = ImmutableList.builder();
    for (final Integer sentenceNumber : Ordering.natural().immutableSortedCopy(sentenceEASet.keySet())) {
      final Collection<SherlockDocumentEvent> efs = sentenceEASet.get(sentenceNumber);
      final ImmutableList<SherlockDocumentEvent> efList =
          SieveUtils.firstAnchorArgumentStart.immutableSortedCopy(efs);
      ret.add(efList);
    }
    return ret.build();
  }
  */

  public ImmutableList<EventCandidate> combineEventFramesAcrossSentences(
      final DocTheory doc,
      final ImmutableList<ImmutableList<EventCandidate>> eventsGroupedBySentence) {
      //final Combination combinationType) {

    final ImmutableList.Builder<EventCandidate> newEventFrames = ImmutableList.builder();
    final int numSentences = eventsGroupedBySentence.size();

    boolean candidateIsCombined[][] = new boolean[eventsGroupedBySentence.size()][];
    for(int i=0; i<eventsGroupedBySentence.size(); i++) {
      candidateIsCombined[i] = new boolean[eventsGroupedBySentence.get(i).size()];
    }

    // we proceed through the sentences in the document one-by-one
    for (int focusSentIdx = 0; focusSentIdx < numSentences; focusSentIdx++) {
      // for each event in the focus sentence, we will search through the remainder of the document
      // looking for other events in can be combined with
      //int combiningIndex = 0;
      for(int combiningIndex=0; combiningIndex<eventsGroupedBySentence.get(focusSentIdx).size(); combiningIndex++) {
        EventCandidate combiningEvent = eventsGroupedBySentence.get(focusSentIdx).get(combiningIndex);
      //for (EventCandidate combiningEvent : eventsGroupedBySentence.get(focusSentIdx)) {
        if(candidateIsCombined[focusSentIdx][combiningIndex]) { // skip if this is already combined
          continue;
        }

        /*
        final ImmutableList.Builder<EventMention> emsBuilder = ImmutableList.builder();
        emsBuilder.addAll(combiningEvent.eventMentions());

        if(combiningEvent.type().asString().compareTo("RespectForRightsFreedoms_001")==0) {
          System.out.println("Right now, emsBuilder consists of the following arguments:");
          for (final EventMention em : emsBuilder.build()) {
            for (final Value v : SieveUtils.getValues(ImmutableSet.copyOf(em.arguments()))) {
              if (v.timexVal().isPresent()) {
                System.out.println(
                    v.timexVal().get().asString() + " anchor=" + em.anchorNode().head().span()
                        .startCharOffset().asInt() + "," + em.anchorNode().head().span()
                        .endCharOffset().asInt());
              }
            }
          }
        }
        */

        // we start the search for events to combine with the focus event with the *next* sentence
        // rather than the sentence containing the focus event itself. This is because we want to
        // respect the decisions of the previously applied sentence-level sieve
        for (int toCombineSentIdx = focusSentIdx + 1; toCombineSentIdx < numSentences; toCombineSentIdx++) {

          //int toCombineIndex = 0;
          for(int toCombineIndex=0; toCombineIndex<eventsGroupedBySentence.get(toCombineSentIdx).size(); toCombineIndex++) {
            final EventCandidate candidateEFToCombine = eventsGroupedBySentence.get(toCombineSentIdx).get(toCombineIndex);

          //for (final EventCandidate candidateEFToCombine : eventsGroupedBySentence.get(toCombineSentIdx)) {
            if(candidateIsCombined[toCombineSentIdx][toCombineIndex]) { // skip if this is already combined
              continue;
            }

            //final boolean satisfiesCombinationType = combinationType
            //    .satisfy(combiningEvent, candidateEFToCombine, wordCategoryCache, language, stemmer);
            final boolean satisfiesConstraints =
                satisfiesConstraints(doc, combiningEvent, candidateEFToCombine);

            //if (satisfiesCombinationType && satisfiesConstraints &&
            //    SieveUtils.mayMerge(mergeFilters, doc, combiningEvent, candidateEFToCombine)) {
            if(satisfiesConstraints) {
              // note when we do a merge, we updated combining event to the merged event, so this
              // new larger event is what we will try to merge with events seen later

              //combiningEvent = SherlockDocumentEvent.builder().eventType(combiningEvent.eventType())
              //    .addAllArguments(combiningEvent.arguments())
              //    .addAllArguments(candidateEFToCombine.arguments())
              //    .derivation(SherlockUtils.deriveFromRuleOnly("CombineEventFramesAcrossSentences"))
              //    .build();

              //int counta = combiningEvent.eventMentions().size();
              //ArrayList<EventMention> combinedEventMentions = Lists.newArrayList(combiningEvent.eventMentions());
              //int countb = candidateEFToCombine.eventMentions().size();
              //combinedEventMentions.addAll(candidateEFToCombine.eventMentions());
              //combiningEvent = new EventCandidate(doc, combiningEvent.type(), combinedEventMentions);
              //combiningEvent.addEventMentions(ImmutableList.copyOf(candidateEFToCombine.eventMentions()));
              //int countc = combiningEvent.eventMentions().size();
              //System.out.println("DOCUMENTSIEVE a,b,c = " + counta + " " + countb + " " + countc);

              /*
              emsBuilder.addAll(candidateEFToCombine.eventMentions());

              System.out.println("SatisfiesConstraints, so emsBuilder will consist of the following arguments:");
              for (final EventMention em : emsBuilder.build()) {
                for (final Value v : SieveUtils.getValues(ImmutableSet.copyOf(em.arguments()))) {
                  if (v.timexVal().isPresent()) {
                    System.out.println(
                        v.timexVal().get().asString() + " anchor=" + em.anchorNode().head().span()
                            .startCharOffset().asInt() + "," + em.anchorNode().head().span()
                            .endCharOffset().asInt());
                  }
                }
              }
              */

              final ImmutableList.Builder<EventMention> emsBuilder = ImmutableList.builder();
              emsBuilder.addAll(combiningEvent.eventMentions());
              emsBuilder.addAll(candidateEFToCombine.eventMentions());
              combiningEvent = new EventCandidate(doc, combiningEvent.type(), emsBuilder.build());

              candidateIsCombined[focusSentIdx][combiningIndex] = true;
              candidateIsCombined[toCombineSentIdx][toCombineIndex] = true;
              // in order to respect the decisions of the sentence-level sieve, we do not
              // attempt any merges with other events in a sentence where we have already performed
              // a successful merge
              break;


            }

            //toCombineIndex += 1;
          }
        }

        //final EventCandidate newCandidate = new EventCandidate(doc, combiningEvent.type(), emsBuilder.build());

        /*
        if(newCandidate.type().asString().compareTo("RespectForRightsFreedoms_001")==0) {
          System.out.println("I'm adding a new EventCandidate:");
          for (final EventMention em : newCandidate.eventMentions()) {
            for (final Value v : SieveUtils.getValues(ImmutableSet.copyOf(em.arguments()))) {
              if (v.timexVal().isPresent()) {
                System.out.println(
                    v.timexVal().get().asString() + " anchor=" + em.anchorNode().head().span()
                        .startCharOffset().asInt() + "," + em.anchorNode().head().span()
                        .endCharOffset().asInt());
              }
            }
          }
        }
        */

        newEventFrames.add(combiningEvent);
        //newEventFrames.add(new EventCandidate(doc, combiningEvent.type(), emsBuilder.build()));

        //combiningIndex += 1;
      }
    }

    return newEventFrames.build();
  }

  private boolean satisfiesConstraints(final DocTheory doc,
      final EventCandidate ef1, final EventCandidate ef2) {

    if(!ef1.eventMentions().get(0).type().equalTo(ef2.eventMentions().get(0).type())) {
      return false;
    }

    final boolean conflictOnEventRole = typeSpecificConstraints
        .conflictsOnArgumentsForEventRole(doc, ef1, ef2, this.placeContainmentCache, this.propPathCache, this.cas);
    final boolean conflictOnAnchorPostag = SieveGeneralRules.conflictsOnAnchorPostag(ef1, ef2);
    final boolean conflictOnLifeMarry = typeSpecificConstraints.conflictsOnLifeMarry(ef1, ef2, doc, this.cas);
    final boolean conflictOnBusinessMergeOrg = typeSpecificConstraints
        .conflictsOnBusinessMergeOrg(ef1, ef2, doc, this.cas);
    //final boolean conflictOnEventClasses = wordCategoryCache
    //    .conflictsOnIncompatibleEventClasses(ef1, ef2);
    //final boolean conflictOnInvoluntary = wordCategoryCache.conflictsOnInvoluntary(ef1, ef2);

    /*
    if(ef1.eventMentions().get(0).type().asString().compareTo("RespectForRightsFreedoms_001")==0) {
      System.out.println("In DocumentSieve.satisfiesConstaints, trying to combine:");
      for(final EventMention em : ef1.eventMentions()) {
        for(final Value v : SieveUtils.getValues(ImmutableSet.copyOf(em.arguments()))) {
          if(v.timexVal().isPresent()) {
            System.out.println(" - " + v.timexVal().get().asString() + " anchor=" + em.anchorNode().head().span().startCharOffset().asInt() + "," + em.anchorNode().head().span().endCharOffset().asInt());
          }
        }
      }
      System.out.println(" WITH");
      for(final EventMention em : ef2.eventMentions()) {
        for(final Value v : SieveUtils.getValues(ImmutableSet.copyOf(em.arguments()))) {
          if(v.timexVal().isPresent()) {
            System.out.println(" - " + v.timexVal().get().asString() + " anchor=" + em.anchorNode().head().span().startCharOffset().asInt() + "," + em.anchorNode().head().span().endCharOffset().asInt());
          }
        }
      }
      System.out.println("conflictOnEventRole=" + conflictOnEventRole);
    }
    */

    final boolean haveConflict = conflictOnEventRole || conflictOnAnchorPostag ||
        //conflictOnEventClasses || conflictOnInvoluntary ||
        conflictOnLifeMarry || conflictOnBusinessMergeOrg;

    return !haveConflict;
  }

  /*
  public enum Combination {
    COMBINATION_ANCHOR {
      @Override
      public boolean satisfy(final SherlockDocumentEvent ef1, final SherlockDocumentEvent ef2,
          WordCategoryCache wordCategoryCache,
          final Language language, final Stemmer stemmer) {
        return SieveUtils.hasCommonAnchorHwLemma(ef1, ef2, language, stemmer);
      }
    }, COMBINATION_EVENT_CLASS {
      @Override
      public boolean satisfy(final SherlockDocumentEvent ef1, final SherlockDocumentEvent ef2,
          WordCategoryCache wordCategoryCache,
          final Language language, final Stemmer stemmer) {
        return wordCategoryCache.hasCommonEventClasses(ef1, ef2);
      }
    }, COMBINATION_ALL {
      @Override
      public boolean satisfy(final SherlockDocumentEvent ef1, final SherlockDocumentEvent ef2,
          WordCategoryCache wordCategoryCache,
          final Language language, final Stemmer stemmer) {
        return true;
      }
    };

    public abstract boolean satisfy(final SherlockDocumentEvent ef1,
        final SherlockDocumentEvent ef2, WordCategoryCache wordCategoryCache,
        final Language language, final Stemmer stemmer);
  }
  */

}
