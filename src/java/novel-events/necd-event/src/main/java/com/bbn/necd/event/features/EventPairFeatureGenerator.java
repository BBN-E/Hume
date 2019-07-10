package com.bbn.necd.event.features;

import com.bbn.bue.common.parameters.Parameters;
import com.bbn.bue.common.parameters.ParametersModule;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.bue.common.symbols.SymbolUtils;
import com.bbn.necd.event.features.PropositionTreeEvent.WordPos;
import com.bbn.necd.event.features.WordNetWrapper.WordPosPair;
import com.bbn.necd.event.icews.ActorType;
import com.bbn.necd.event.icews.ICEWSActors;
import com.bbn.necd.icews.ICEWSDatabase;
import com.bbn.necd.wordnet.WordNetSimilarity;
import com.bbn.nlp.banks.wordnet.IWordNet;
import com.bbn.nlp.banks.wordnet.WordNetM;
import com.bbn.nlp.banks.wordnet.WordNetPOS;

import com.google.common.base.Function;
import com.google.common.cache.CacheBuilder;
import com.google.common.cache.CacheLoader;
import com.google.common.cache.LoadingCache;
import com.google.common.collect.FluentIterable;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Sets;
import com.google.inject.Guice;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.sql.SQLException;
import java.util.Set;

import javax.annotation.Nonnull;

import static com.google.common.base.Preconditions.checkArgument;
import static com.google.common.base.Preconditions.checkNotNull;

/**
 * Generate features for pairs of events.
 */
public class EventPairFeatureGenerator {

  private static final Logger log = LoggerFactory.getLogger(EventPairFeatureGenerator.class);

  private final static int CACHE_SIZE = 10000;

  private final WordNetWrapper wn;
  private final ICEWSDatabase icews;
  private final LoadingCache<Long, ImmutableSet<Symbol>> actorCache;
  private final LoadingCache<Long, ImmutableSet<Symbol>> agentCache;

  private EventPairFeatureGenerator(WordNetWrapper wn, ICEWSDatabase icewsDatabase) {
    this.wn = checkNotNull(wn);
    this.icews = checkNotNull(icewsDatabase);
    this.actorCache = CacheBuilder.newBuilder().maximumSize(CACHE_SIZE)
        .build(new ActorSectorCacheLoader(icewsDatabase));
    this.agentCache = CacheBuilder.newBuilder().maximumSize(CACHE_SIZE)
        .build(new AgentSectorCacheLoader(icewsDatabase));
  }

  public static EventPairFeatureGenerator create(final Parameters wordNetParams,
      final Parameters icewsParams) throws IOException, SQLException {
    final ParametersModule paramsModule = ParametersModule.createAndDump(wordNetParams);
    final IWordNet wordNet = Guice.createInjector(
        paramsModule, WordNetM.fromParameters(wordNetParams)).getInstance(IWordNet.class);
    final WordNetSimilarity verbSim = WordNetSimilarity.fromWordNet(wordNet, WordNetPOS.VERB);
    final WordNetSimilarity nounSim = WordNetSimilarity.fromWordNet(wordNet, WordNetPOS.NOUN);
    final WordNetWrapper wordNetWrapper = WordNetWrapper.fromWordNet(wordNet, nounSim, verbSim);
    final ICEWSDatabase icewsDatabase = ICEWSDatabase.fromParameters(icewsParams);
    return new EventPairFeatureGenerator(wordNetWrapper, icewsDatabase);
  }

  public EventFeatures generate(final PropositionTreeEvent event) {
    checkNotNull(event);
    final ImmutableSet<Symbol> sourceSectors = getEventActorSectors(event, ICEWSActors.Role.SOURCE);
    final ImmutableSet<Symbol> targetSectors = getEventActorSectors(event, ICEWSActors.Role.TARGET);

    final ImmutableList<Symbol> predicates = event.getPredicates();
    final ImmutableList<Symbol> stems = event.getStems();
    final ImmutableList<Integer> predicateTokenIndices = event.getPredicateTokenIndices();

    final EventFeatures.Builder eventFeaturesBuilder = EventFeatures.builder(event.getId(),
        event.getEventCode(), event.getPredType(), event.getEventFilter(),
        event.getDocId(), event.getSentenceIndex());

    eventFeaturesBuilder.withPredicates(predicates);
    eventFeaturesBuilder.withStems(stems);
    eventFeaturesBuilder.withPos(event.getPos());
    eventFeaturesBuilder.withPredicateTokenIndices(predicateTokenIndices);
    eventFeaturesBuilder.withSourceSectors(sourceSectors);
    eventFeaturesBuilder.withTargetSectors(targetSectors);
    eventFeaturesBuilder.withSourceTokens(event.getSourceTokens());
    eventFeaturesBuilder.withTargetTokens(event.getTargetTokens());
    PropositionTreeFeatures.addFeatures(event, eventFeaturesBuilder);

    return eventFeaturesBuilder.build();
  }

  public EventPairFeatures generate(final PropositionTreeEvent event1, final PropositionTreeEvent event2) {
    checkNotNull(event1);
    checkNotNull(event2);

    final ImmutableList<WordPos> predPos1 = event1.getPredicatesWithPos();
    final ImmutableList<WordPos> predPos2 = event2.getPredicatesWithPos();

    final ImmutableList<Double> conSim =
        predicateFeaturePairs(predPos1, predPos2, wn.conSimFunction());
    final ImmutableList<Double> conSimCombinations =
        predicateFeatureCombinations(predPos1, predPos2, wn.conSimFunction());
    final ImmutableList<Boolean> sameStem =
        predicateFeaturePairs(predPos1, predPos2, wn.shareStemFunction());
    final ImmutableList<Boolean> sameStemCombinations =
        predicateFeatureCombinations(predPos1, predPos2, wn.shareStemFunction());
    final ImmutableList<Boolean> shareSynset =
        predicateFeaturePairs(predPos1, predPos2, wn.shareSynsetFunction());
    final ImmutableList<Boolean> shareSynsetCombinations =
        predicateFeatureCombinations(predPos1, predPos2, wn.shareSynsetFunction());
    final ImmutableList<Boolean> sameWord =
        predicateFeaturePairs(predPos1, predPos2, wn.sameWordFunction());
    final ImmutableList<Boolean> sameWordCombinations =
        predicateFeatureCombinations(predPos1, predPos2, wn.sameWordFunction());

    // Compare sectors
    final double sourceSectorOverlap = sectorOverlap(
        getEventActorSectors(event1, ICEWSActors.Role.SOURCE),
        getEventActorSectors(event2, ICEWSActors.Role.SOURCE));
    final double targetSectorOverlap = sectorOverlap(
        getEventActorSectors(event1, ICEWSActors.Role.TARGET),
        getEventActorSectors(event2, ICEWSActors.Role.TARGET));

    return EventPairFeatures.create(formatId(event1.getId(), event2.getId()), shareSynset, shareSynsetCombinations,
        sameWord, sameWordCombinations, sameStem, sameStemCombinations, conSim, conSimCombinations, sourceSectorOverlap,
        targetSectorOverlap);
  }

  private static <T> ImmutableList<T> predicateFeaturePairs(final ImmutableList<WordPos> predPos1,
      final ImmutableList<WordPos> predPos2, final Function<WordPosPair, T> featureFunction) {
    checkArgument(!checkNotNull(predPos1).isEmpty());
    checkArgument(!checkNotNull(predPos2).isEmpty());
    checkNotNull(featureFunction);

    // Work from the shorter size
    int size = Math.min(predPos1.size(), predPos2.size());

    // Compute the function on each pair
    final ImmutableList.Builder<T> ret = ImmutableList.builder();
    for (int i = 0; i < size; i++) {
      ret.add(featureFunction.apply(WordPosPair.create(predPos1.get(i), predPos2.get(i))));
    }
    return ret.build();
  }

  private static <T> ImmutableList<T> predicateFeatureCombinations(final ImmutableList<WordPos> predPos1,
      final ImmutableList<WordPos> predPos2, final Function<WordPosPair, T> featureFunction) {
    checkArgument(!checkNotNull(predPos1).isEmpty());
    checkArgument(!checkNotNull(predPos2).isEmpty());
    checkNotNull(featureFunction);

    // Compute the function on each pair
    final ImmutableList.Builder<T> ret = ImmutableList.builder();
    for (int i = 0; i < predPos1.size(); i++) {
      for (int j = 0; j < predPos2.size(); j++) {
        ret.add(featureFunction.apply(WordPosPair.create(predPos1.get(i), predPos2.get(j))));
      }
    }
    return ret.build();
  }

  public void close() {
    try {
      icews.close();
    } catch (SQLException e) {
      // We don't care if there's an exception here; we've done our duty in closing it.
    }
  }

  private double sectorOverlap(final Set<Symbol> sectors1, final Set<Symbol> sectors2) {
    // If one is empty, return 0.0
    if (sectors1.isEmpty() || sectors2.isEmpty()) {
      return 0.0;
    } else {
      // Intersection / union
      return (double) Sets.intersection(sectors1, sectors2).size() / Sets.union(sectors1, sectors2).size();
    }
  }

  private ImmutableSet<Symbol> getEventActorSectors(final PropositionTreeEvent event,
      final ICEWSActors.Role role) {
    // Extract the actor information
    final long actorId;
    final ActorType actorType;
    switch (role) {
      case SOURCE:
        actorId = event.getSourceActorId();
        actorType = event.getSourceActorType();
        break;
      case TARGET:
        actorId = event.getTargetActorId();
        actorType = event.getTargetActorType();
        break;
      default:
        throw new IllegalArgumentException("Unknown role: " + role);
    }
    return getSectorsForActor(actorId, actorType);
  }

  private ImmutableSet<Symbol> getSectorsForActor(long actorId, ActorType actorType) {
    if (ActorType.PROPER_NOUN.equals(actorType)) {
      // Look up in actor sector cache
      return actorCache.getUnchecked(actorId);
    } else if (ActorType.COMPOSITE.equals(actorType)) {
      // Look up in agent sector cache
      return agentCache.getUnchecked(actorId);
    } else {
      throw new IllegalArgumentException("Cannot look up sectors for ActorType: " + actorType);
    }
  }

  private static Symbol formatId(final Symbol id1, final Symbol id2) {
    return Symbol.from('[' + id1.asString() + ':' + id2.asString() + ']');
  }

  private static final class ActorSectorCacheLoader extends CacheLoader<Long, ImmutableSet<Symbol>> {
    private ICEWSDatabase icews;

    private ActorSectorCacheLoader(final ICEWSDatabase db) {
      this.icews = db;
    }

    @Override
    public ImmutableSet<Symbol> load(@Nonnull final Long actorId) throws Exception {
      return FluentIterable.from(icews.getSectorsForActorId(actorId))
          .transform(SymbolUtils.symbolizeFunction())
          .toSet();
    }
  }

  private static final class AgentSectorCacheLoader extends CacheLoader<Long, ImmutableSet<Symbol>> {
    private ICEWSDatabase icews;

    private AgentSectorCacheLoader(final ICEWSDatabase db) {
      this.icews = db;
    }

    @Override
    public ImmutableSet<Symbol> load(@Nonnull final Long actorId) throws Exception {
      return FluentIterable.from(icews.getSectorsForAgentId(actorId))
          .transform(SymbolUtils.symbolizeFunction())
          .toSet();
    }
  }
}
