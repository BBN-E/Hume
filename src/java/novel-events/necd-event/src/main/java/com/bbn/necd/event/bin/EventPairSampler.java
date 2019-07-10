package com.bbn.necd.event.bin;

import com.bbn.bue.common.collections.CollectionUtils;
import com.bbn.bue.common.files.FileUtils;
import com.bbn.bue.common.parameters.Parameters;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.bue.common.symbols.SymbolUtils;
import com.bbn.necd.common.sampler.PairwiseSampler;
import com.bbn.necd.common.sampler.Sampler;
import com.bbn.necd.common.sampler.SamplerCluster;
import com.bbn.necd.common.sampler.SymbolPair;
import com.bbn.necd.event.features.EventFeaturesUtils;
import com.bbn.necd.event.features.MinimalPropositionTreeEvent;
import com.bbn.necd.event.features.ProcessedEvent;
import com.bbn.necd.event.features.PropositionTreeEvent;
import com.bbn.necd.event.icews.CAMEOCodes;
import com.bbn.necd.event.io.LabelWriter;
import com.bbn.necd.event.io.LabeledIdWriter;
import com.bbn.necd.event.propositions.EventFilter;
import com.bbn.necd.event.propositions.PropositionPathEventInstance;
import com.bbn.necd.event.propositions.PropositionPredicateType;

import com.google.common.base.Charsets;
import com.google.common.base.Function;
import com.google.common.base.Optional;
import com.google.common.base.Predicate;
import com.google.common.base.Stopwatch;
import com.google.common.collect.FluentIterable;
import com.google.common.collect.HashMultiset;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableMultimap;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Iterables;
import com.google.common.collect.Lists;
import com.google.common.collect.Maps;
import com.google.common.collect.Multimaps;
import com.google.common.collect.Multiset;
import com.google.common.collect.Sets;
import com.google.common.io.Files;
import com.google.common.math.DoubleMath;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;
import java.math.RoundingMode;
import java.sql.SQLException;
import java.util.Collection;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.Set;
import java.util.concurrent.TimeUnit;

import javax.annotation.Nullable;

import static com.bbn.bue.common.StringUtils.CommaSpaceJoin;
import static com.bbn.bue.common.StringUtils.NewlineJoiner;
import static com.bbn.necd.event.EventUtils.orderMapByReversedValues;
import static com.bbn.necd.event.io.CompressedFileUtils.readAsJsonList;
import static com.google.common.base.Preconditions.checkNotNull;
import static com.google.common.base.Predicates.in;
import static com.google.common.base.Predicates.not;

/**
 * Generate features for serialized {@link PropositionPathEventInstance}s.
 *
 * Sampling proceeds in 3 phases:
 * (i) diversity sampling (e.g. uniqueness of predicates on proposition connection, and perhaps sectors of Source, Target)
 * (ii) omit sparse codes that have fewer than densityThreshold instances after the above diversity sampling
 * (iii) pairwise sampling. Specifically it now does this:
 * Pick 2 event codes e1 and e2.
 * Generate a pair of instances from e1. Generate a pair of instances from e2.
 * Generate 2 pairs of instances from e1 x e2.
 * I.e. we generate 2 positives and 2 negatives per iteration. And then repeat.
 */
public final class EventPairSampler {

  private static final Logger log = LoggerFactory.getLogger(EventPairSampler.class);



  // Number of failed attempts to allow for the natural sampling. Does not apply to the normal train/test sampling.
  private static final int MAX_TRIES = 5000;

  public static void main(String[] argv) {
    // we wrap the main method in this way to
    // ensure a non-zero return value on failure
    try {
      trueMain(argv);
    } catch (Exception e) {
      e.printStackTrace();
      System.exit(1);
    }
  }

  public static void trueMain(final String[] argv) throws IOException, SQLException {
    if (argv.length != 1) {
      System.err.println("Usage: eventPairSampler params");
      System.exit(1);
    }

    final Parameters params = Parameters.loadSerifStyle(new File(argv[0]));
    log.info("{} run on parameters:\n{}", EventPairSampler.class, params.dump());

    final Parameters samplerParams = params.copyNamespace("com.bbn.necd.event.sampler");

    // Input
    final List<File> eventFeaturesFiles = FileUtils.loadFileList(samplerParams.getExistingFile("extractedEventFileList"));
    final File eventFeaturesDir = samplerParams.getExistingDirectory("extractedEventDir");

    // Settings
    final int randomSeed = samplerParams.getInteger("randomSeed");
    final int nFolds = samplerParams.getInteger("numCrossvalFolds");
    final int nBatches = samplerParams.getInteger("numBatches");
    final int requestedInstances = samplerParams.getInteger("classificationInstances");
    final int requestedNaturalSamples = samplerParams.getInteger("naturalTestInstances");
    final Optional<Double> optRequestedPosRatio = samplerParams.getOptionalPositiveDouble("positiveInstanceRatio");
    final Optional<Integer> densityThreshold = samplerParams.getOptionalInteger("densityThreshold");
    final Double requestedAccentedRatio = samplerParams.getPositiveDouble("accentedRatio");
    final int predicateDiversityThreshold = samplerParams.getInteger("predicateDiversityThreshold");
    final EventFilter eventFilter = samplerParams.getEnum("eventFilter", EventFilter.class);

    // Output
    final File testDir = samplerParams.getCreatableDirectory("testDir").getAbsoluteFile();
    final File devDir = samplerParams.getCreatableDirectory("devDir").getAbsoluteFile();
    final File trainDir = samplerParams.getCreatableDirectory("trainDir").getAbsoluteFile();
    final File naturalDir = samplerParams.getCreatableDirectory("naturalDir").getAbsoluteFile();
    final File unaccentedDir = samplerParams.getCreatableDirectory("unaccentedDir").getAbsoluteFile();
    final File unaccentedBalancedDir = samplerParams.getCreatableDirectory("unaccentedBalancedDir").getAbsoluteFile();
    final String foldsFilename = samplerParams.getString("foldsFilename");
    final String pairTableSuffix = samplerParams.getString("pairTableSuffix");
    final String idTableSuffix = samplerParams.getString("idTableSuffix");

    // Read in events
    log.info("Loading event features");
    final ImmutableList<ProcessedEvent> eventFeatures =
        loadEventFeatures(eventFeaturesFiles, eventFeaturesDir, eventFilter);
    logPredicateTypes(eventFeatures);
    log.info("Loaded features for {} events", eventFeatures.size());
    log.info("Overall event filter counts:");
    logEventFilters(eventFeatures);

    // Make a second version with only the uncoded events
    final ImmutableList<ProcessedEvent> uncodedEventFeatures = FluentIterable.from(eventFeatures)
        .filter(new Predicate<ProcessedEvent>() {
          @Override
          public boolean apply(ProcessedEvent input) {
            checkNotNull(input);
            return !input.getEventCode().isPresent();
          }
        })
        .toList();
    log.info("{} events are uncoded", uncodedEventFeatures.size());
    log.info("Uncoded event filter counts:");
    logEventFilters(uncodedEventFeatures);

    log.info("Processing and sampling events");
    final Stopwatch stopwatch = Stopwatch.createStarted();

    // Put events into a map by code. Since not all events have codes, we cannot simply do this with Multimaps#index
    final ImmutableMultimap<Symbol, ProcessedEvent> codeEventFeatures =
        EventFeaturesUtils.codeFeaturesMap(eventFeatures);
    log.info("Coded event filter counts:");
    logEventFilters(codeEventFeatures.values());

    // Count codes and display counts
    final Map<Symbol, Integer> codeCounts = Maps.transformValues(codeEventFeatures.asMap(), CollectionUtils.sizeFunction());
    log.info("Unique codes: {}", codeCounts.keySet().size());
    // Sort using a magic incantation
    log.info("Code counts:\n{}", NewlineJoiner.withKeyValueSeparator("\t").join(
        orderMapByReversedValues(codeCounts, SymbolUtils.byStringOrdering())));

    // Track training and testing folds
    final ImmutableList.Builder<File> trainFolds = ImmutableList.builder();
    final ImmutableList.Builder<File> testFolds = ImmutableList.builder();
    final ImmutableList.Builder<File> devFolds = ImmutableList.builder();
    final ImmutableList.Builder<File> naturalFolds = ImmutableList.builder();
    final ImmutableList.Builder<File> unaccentedFolds = ImmutableList.builder();
    final ImmutableList.Builder<File> unaccentedBalancedFolds = ImmutableList.builder();

    int totalFoldCount = 1;
    for (int batch = 0; batch < nBatches; batch++) {
      // The batch number is zero-indexed so that the random seed for the first batch is the one requested, so we
      // offset by 1 for display
      log.info("Starting batch {}", batch + 1);

      // Set a new random seed for the batch
      final int batchRandomSeed = randomSeed + batch;

      // Create hold-out top-level labels for cross validation
      final ImmutableList<ImmutableList<Symbol>> heldOutTopLevelCodes =
          holdOutCrossvalCodes(codeEventFeatures.keySet(), nFolds, new Random(batchRandomSeed));
      log.info("Number of folds: {}", nFolds);
      log.info("Test folds (top-level codes):\n{}", NewlineJoiner.join(Iterables.transform(heldOutTopLevelCodes, CommaSpaceJoin)));
      // Expand to full codes
      final ImmutableList<ImmutableSet<Symbol>> heldOutCodes = expandCodes(heldOutTopLevelCodes, codeEventFeatures.keySet());
      log.info("Test folds (full-codes):\n{}", NewlineJoiner.join(Iterables.transform(heldOutCodes, CommaSpaceJoin)));

      for (final ImmutableSet<Symbol> foldHeldOutCodes : heldOutCodes) {
        // Process each fold
        log.info("Creating fold {}", totalFoldCount);
        final String foldCountString = Integer.toString(totalFoldCount);

        // Cut down events for training and testing. A scope is created for each to avoid accidental leakage.
        { // Training
          final Random rng = new Random(batchRandomSeed);
          final File trainFile = new File(trainDir, foldCountString + "." + pairTableSuffix).getAbsoluteFile();
          trainFolds.add(trainFile);
          final ImmutableMultimap<Symbol, ProcessedEvent> trainingEvents = ImmutableMultimap.copyOf(Multimaps.filterKeys(
              codeEventFeatures, not(in(foldHeldOutCodes))));
          sampleEvents(requestedInstances, optRequestedPosRatio, densityThreshold, rng, trainingEvents, trainFile);
          log.info("Wrote {} train samples to {}", requestedInstances, trainFile);
        }

        { // Dev
          final Random rng = new Random(batchRandomSeed);
          final File devFile = new File(devDir, foldCountString + "." + pairTableSuffix).getAbsoluteFile();
          devFolds.add(devFile);
          final ImmutableMultimap<Symbol, ProcessedEvent> devEvents = ImmutableMultimap.copyOf(Multimaps.filterKeys(
              codeEventFeatures, in(foldHeldOutCodes)));
          sampleEvents(requestedInstances, optRequestedPosRatio, densityThreshold, rng, devEvents, devFile);
          log.info("Wrote {} dev samples to {}", requestedInstances, devFile);
        }

        { // Testing
          final Random rng = new Random(batchRandomSeed);
          final File testFile = new File(testDir, foldCountString + "." + pairTableSuffix).getAbsoluteFile();
          testFolds.add(testFile);
          final ImmutableMultimap<Symbol, ProcessedEvent> testEvents = ImmutableMultimap.copyOf(Multimaps.filterKeys(
              codeEventFeatures, in(foldHeldOutCodes)));
          sampleEvents(requestedInstances, optRequestedPosRatio, densityThreshold, rng, testEvents, testFile);
          log.info("Wrote {} test samples to {}", requestedInstances, testFile);
        }

        {
          // Unstructured pairs for testing
          final Random rng = new Random(batchRandomSeed);
          final File testFile = new File(naturalDir, foldCountString + "." + idTableSuffix).getAbsoluteFile();

          final ImmutableMultimap<Symbol, ProcessedEvent> testCodedEvents = ImmutableMultimap.copyOf(
              Multimaps.filterKeys(codeEventFeatures, in(foldHeldOutCodes)));
          // Sample over all the coded events. We use ArrayList instead of an ImmutableList because of speed
          final List<ProcessedEvent> allEvents = Lists.newArrayList(testCodedEvents.values());

          writeNaturalSample(requestedNaturalSamples, allEvents, ImmutableList.<ProcessedEvent>of(), 0.0,
              rng, testFile, predicateDiversityThreshold);
          naturalFolds.add(testFile);
          log.info("Wrote {} natural samples to {}", requestedNaturalSamples, testFile);
        }

        {
          // Unstructured pairs for testing that include non-coded data
          final Random rng = new Random(batchRandomSeed);
          final File testFile = new File(unaccentedDir, foldCountString + "." + idTableSuffix).getAbsoluteFile();

          final ImmutableMultimap<Symbol, ProcessedEvent> testCodedEvents = ImmutableMultimap.copyOf(
              Multimaps.filterKeys(codeEventFeatures, in(foldHeldOutCodes)));
          // Build a united list of all of the events, coded and uncoded
          final List<ProcessedEvent> allEvents = Lists.newArrayList(testCodedEvents.values());
          allEvents.addAll(uncodedEventFeatures);

          writeNaturalSample(requestedNaturalSamples, allEvents, ImmutableList.<ProcessedEvent>of(), 0.0,
              rng, testFile, predicateDiversityThreshold);
          unaccentedFolds.add(testFile);
          log.info("Wrote {} accented and unaccented samples to {}", requestedNaturalSamples, testFile);
        }

        {
          // Unstructured pairs for testing that include non-coded data, but include a specific positive/negative ratio
          final Random rng = new Random(batchRandomSeed);
          final File testFile = new File(unaccentedBalancedDir, foldCountString + "." + idTableSuffix).getAbsoluteFile();

          final ImmutableMultimap<Symbol, ProcessedEvent> testCodedEvents = ImmutableMultimap.copyOf(
              Multimaps.filterKeys(codeEventFeatures, in(foldHeldOutCodes)));
          // Drop all the events in an array list for sampling speed
          final List<ProcessedEvent> uncodedEventFeaturesArrayList = Lists.newArrayList(uncodedEventFeatures);
          // Put the coded events in another array list
          final List<ProcessedEvent> codedEvents = Lists.newArrayList(testCodedEvents.values());

          writeNaturalSample(requestedNaturalSamples, uncodedEventFeaturesArrayList, codedEvents, requestedAccentedRatio, rng, testFile,
              predicateDiversityThreshold);
          unaccentedBalancedFolds.add(testFile);
          log.info("Wrote {} accented and unaccented (balanced with {} accented) samples to {}", requestedNaturalSamples,
              requestedAccentedRatio, testFile);
        }

        // Update loop count
        totalFoldCount++;
      }
    }

    // Write out folds
    log.info("Writing fold information");
    // Train
    {
      final File trainFoldsFile = new File(trainDir, foldsFilename);
      FileUtils.writeFileList(trainFolds.build(), Files.asCharSink(trainFoldsFile, Charsets.UTF_8));
      log.info("Wrote train fold information to {}", trainFoldsFile);
    }

    // Dev
    {
      final File devFoldsFile = new File(devDir, foldsFilename);
      FileUtils.writeFileList(devFolds.build(), Files.asCharSink(devFoldsFile, Charsets.UTF_8));
      log.info("Wrote dev fold information to {}", devFoldsFile);
    }

    // Test
    {
      final File testFoldsFile = new File(testDir, foldsFilename);
      FileUtils.writeFileList(testFolds.build(), Files.asCharSink(testFoldsFile, Charsets.UTF_8));
      log.info("Wrote test fold information to {}", testFoldsFile);
    }

    // Natural
    {
      final File naturalFoldsFile = new File(naturalDir, foldsFilename);
      FileUtils.writeFileList(naturalFolds.build(), Files.asCharSink(naturalFoldsFile, Charsets.UTF_8));
      log.info("Wrote natural fold information to {}", naturalFoldsFile);
    }

    // Unaccented
    {
      final File unaccentedFoldsFile = new File(unaccentedDir, foldsFilename);
      FileUtils.writeFileList(unaccentedFolds.build(), Files.asCharSink(unaccentedFoldsFile, Charsets.UTF_8));
      log.info("Wrote unaccented fold information to {}", unaccentedFoldsFile);
    }

    // Unaccented with balance
    {
      final File unaccentedBalancedFoldsFile = new File(unaccentedBalancedDir, foldsFilename);
      FileUtils.writeFileList(unaccentedBalancedFolds.build(), Files.asCharSink(unaccentedBalancedFoldsFile, Charsets.UTF_8));
      log.info("Wrote unaccented fold information to {}", unaccentedBalancedFoldsFile);
    }

    // Output timing information
    stopwatch.stop();
    log.info("Sampling took {} seconds", stopwatch.elapsed(TimeUnit.SECONDS));
  }

  private static ImmutableList<ProcessedEvent> loadEventFeatures(List<File> eventFeaturesFiles, File eventFeaturesDir, EventFilter eventFilter) throws IOException {
    final ImmutableList.Builder<ProcessedEvent> eventFeaturesBuilder = ImmutableList.builder();
    for (final File eventFeaturesFile : eventFeaturesFiles) {
      // Path is relative to root
      final File eventFeaturesFileFullPath = new File(eventFeaturesDir, eventFeaturesFile.getName()).getAbsoluteFile();
      log.info("Loading {}", eventFeaturesFileFullPath);
      // Filter down by event filter
      for (final PropositionTreeEvent features :
          readAsJsonList(eventFeaturesFileFullPath, PropositionTreeEvent.class)) {
        // Add it if allowed by the filter
        if (eventFilter.allowsFilter(features.getEventFilter())) {
          eventFeaturesBuilder.add(MinimalPropositionTreeEvent.fromEvent(features));
        }
      }
    }
    return eventFeaturesBuilder.build();
  }

  private static void logPredicateTypes(Iterable<ProcessedEvent> events) {
    final Multiset<PropositionPredicateType> predicateTypes = HashMultiset.create();
    for (final ProcessedEvent event : events) {
      predicateTypes.add(event.getPredType());
    }
    log.info("{} verbal events and {} nominal events", predicateTypes.count(PropositionPredicateType.VERB),
        predicateTypes.count(PropositionPredicateType.NOUN));
  }

  private static void logEventFilters(Iterable<ProcessedEvent> events) {
    final Multiset<EventFilter> predicateTypes = HashMultiset.create();
    for (final ProcessedEvent event : events) {
      predicateTypes.add(event.getEventFilter());
    }
    log.info("{} ALL events and {} SIMPLE events", predicateTypes.count(EventFilter.ALL),
        predicateTypes.count(EventFilter.SIMPLE));
  }

  private static void writeNaturalSample(final int requestedInstances,
      final List<ProcessedEvent> allEvents, final List<ProcessedEvent> codedEvents,
      final double codedRatio, final Random rng, final File output, final int predicateDiversityThreshold) throws IOException {
    // Create the output writer
    try (final LabeledIdWriter writer = LabeledIdWriter.create(output)) {
      // Ids that have been written
      final Set<Symbol> writtenIds = Sets.newHashSet();

      // Number of attempts since we last produced a successful sample
      int failedAttempts = 0;

      // Count the number of times we see each predicate
      final Multiset<ImmutableList<Symbol>> predicateDiversityCounts = HashMultiset.create();

      // Track the number of coded events
      int codedEventsSampled = 0;
      int codedEventsRequested = DoubleMath.roundToInt(requestedInstances * codedRatio, RoundingMode.DOWN);

      // Sampling procedure: (1) Pick an event (2) if it hasn't been picked before, write it out
      // We cannot use a shuffling iterable here because the size is so large. Instead, we just pluck indices from the
      // original
      final int nItems = allEvents.size();
      final int nCodedItems = codedEvents.size();
      while (writtenIds.size() < requestedInstances) {
        // Check for and fail on exhaustion condition
        if (failedAttempts >= MAX_TRIES) {
          throw new RuntimeException(String.format("Maximum tries exceeded after producing %d samples", writtenIds.size()));
        }

        // Pick an event by getting a random index
        final ProcessedEvent features;
        if (codedEventsSampled < codedEventsRequested) {
          // Draw from accented first as needed
          final int index = rng.nextInt(nCodedItems);
          features = codedEvents.get(index);
        } else {
          final int index = rng.nextInt(nItems);
          features = allEvents.get(index);
        }

        final Symbol id = features.getId();
        // Cut down the predicates to the first two for diversity counts
        final ImmutableList<Symbol> predicates = ImmutableList.copyOf(diversityFeature(features));

        // Write it out if it hasn't been picked before and it doesn't exceed the diversity threshold
        if (!writtenIds.contains(id) && predicateDiversityCounts.count(predicates) < predicateDiversityThreshold) {
          if (features.getEventCode().isPresent()) {
            codedEventsSampled++;
          }
          final String code = features.getEventCode().or(Symbol.from("NA")).asString();
          writer.writeLabel(id.asString(), code);
          writtenIds.add(id);
          predicateDiversityCounts.add(predicates);
          failedAttempts = 0;
        } else {
          failedAttempts++;
        }
      }
      log.info("Sampled {} coded events out of a total of {} events", codedEventsSampled, writtenIds.size());
    }
  }

  private static void sampleEvents(final int requestedInstances, final Optional<Double> optRequestedPosRatio,
      final Optional<Integer> densityThreshold, final Random rng,
      final ImmutableMultimap<Symbol, ProcessedEvent> codeEventFeatures, final File labelFile)
      throws IOException {

    // Create the sampler
    final PairwiseSampler pairwiseSampler =
        sample(codeEventFeatures, densityThreshold, requestedInstances, optRequestedPosRatio, rng);

    // Write out samples
    writePairInstances(codeEventFeatures, pairwiseSampler, labelFile);
  }

  private static ImmutableList<ImmutableSet<Symbol>> expandCodes(
      final Iterable<? extends Iterable<Symbol>> heldOutTopLevelCodes, final Set<Symbol> allCodes) {
    final ImmutableList.Builder<ImmutableSet<Symbol>> ret = ImmutableList.builder();
    // Loop over each held out set
    for (final Iterable<Symbol> foldTopLevelCodes : heldOutTopLevelCodes) {
      final ImmutableSet<Symbol> foldTopLevelCodesSet = ImmutableSet.copyOf(foldTopLevelCodes);
      final ImmutableSet.Builder<Symbol> foldFullCodes = ImmutableSet.builder();
      // Loop over each full code
      for (final Symbol fullCode : allCodes) {
        // Check its top-level code against the set of top-level codes
        if (foldTopLevelCodesSet.contains(CAMEOCodes.topLevelCode(fullCode))) {
          foldFullCodes.add(fullCode);
        }
      }
      ret.add(foldFullCodes.build());
    }
    return ret.build();
  }

  private static ImmutableList<ImmutableList<Symbol>> holdOutCrossvalCodes(final Iterable<Symbol> codes,
      final int nFolds, final Random rng) {
    // Turn into a set of top level codes. We put it in a mutable list so we can shuffle in place.
    final List<Symbol> topLevelCodes = Lists.newArrayList(
        FluentIterable.from(codes).transform(TopLevelCodeFunction.INSTANCE).toSet());
    // Shuffle
    Collections.shuffle(topLevelCodes, rng);
    // Split into folds
    return CollectionUtils.partitionAlmostEvenly(topLevelCodes, nFolds);
  }

  private static int writePairInstances(
      final ImmutableMultimap<Symbol, ProcessedEvent> codeEventFeatures,
      final PairwiseSampler pairwiseSampler, final File labelOutput) throws IOException {
    int c = 0;

    // Set up output
    final LabelWriter labelWriter = LabelWriter.create(labelOutput);

    final ImmutableMap.Builder<Symbol, ProcessedEvent> idToEgBuilder = ImmutableMap.builder();
    for (final ProcessedEvent eg : codeEventFeatures.values()) {
      idToEgBuilder.put(eg.getId(), eg);
    }
    final ImmutableMap<Symbol, ProcessedEvent> idToEg = idToEgBuilder.build();

    for(final SymbolPair pair : pairwiseSampler.getIntraPairs()) {
      final ProcessedEvent eg1 = idToEg.get(pair.getFirstMember());
      final ProcessedEvent eg2 = idToEg.get(pair.getSecondMember());
      labelWriter.writeEventPair(eg1, eg2);
      c += 1;
    }

    for(final SymbolPair pair : pairwiseSampler.getInterPairs()) {
      final ProcessedEvent eg1 = idToEg.get(pair.getFirstMember());
      final ProcessedEvent eg2 = idToEg.get(pair.getSecondMember());
      labelWriter.writeEventPair(eg1, eg2);
      c += 1;
    }

    // Clean up
    labelWriter.close();

    return c;
  }

  /*
  The following various sampling methods tie in the generic sampling code to EventFeatures data structure
   */
  private static PairwiseSampler sample(
      final ImmutableMultimap<Symbol, ProcessedEvent> codeEventFeatures,
      final Optional<Integer> densityThreshold, final int requestedInstances,
      final Optional<Double> optRequestedPosRatio, final Random rng) {
    // first perform diversity sampling
    final ImmutableSet<SamplerCluster> diversityClusters = diversitySampling(codeEventFeatures);

    // now we omit clusters having size less than downSampleSize
    final ImmutableSet<SamplerCluster> denseClusters = densityThreshold.isPresent() ? Sampler
        .selectDenseClusters(diversityClusters, densityThreshold.get()) : diversityClusters;

    // now we perform pairwise sampling, i.e. positive & negative sampling
    final double positiveRatio =
        optRequestedPosRatio.isPresent() ? optRequestedPosRatio.get() : 0.5;

    final PairwiseSampler pairwiseSampler =
        PairwiseSampler.builder(denseClusters, requestedInstances, positiveRatio, rng)
            .sample()
            .build();

    return pairwiseSampler;
  }

  private static ImmutableSet<SamplerCluster> diversitySampling(
      final ImmutableMultimap<Symbol, ProcessedEvent> codeEventFeatures) {
    final ImmutableSet.Builder<SamplerCluster> ret = ImmutableSet.builder();

    for (final Map.Entry<Symbol, Collection<ProcessedEvent>> entry : codeEventFeatures.asMap()
        .entrySet()) {
      final Symbol label = entry.getKey();    // this is the event code

      final ImmutableMap<Symbol, ImmutableList<Symbol>> idToDiversityFeatures =
          idToDiversityFeatures(entry.getValue());
      final ImmutableMap<Symbol, ImmutableList<Symbol>> sampledIdToDiversityFeatures =
          Sampler.uniquenessFiltering(idToDiversityFeatures);

      // importantly, after sampling, the keySet() of sampledIdToDiversityFeatures is a subset of the keySet of idToDiversityFeatures
      // keySet() is the set of instance ids. We now grab all the ids that survive the diversity sampling
      final SamplerCluster cluster =
          SamplerCluster.builder(label).withIds(sampledIdToDiversityFeatures.keySet()).build();
      ret.add(cluster);
    }

    return ret.build();
  }

  private static ImmutableMap<Symbol, ImmutableList<Symbol>> idToDiversityFeatures(
      final Collection<ProcessedEvent> egs) {
    final ImmutableMap.Builder<Symbol, ImmutableList<Symbol>> ret = ImmutableMap.builder();

    for (final ProcessedEvent eg : egs) {
      ret.put(eg.getId(), diversityFeature(eg));
    }

    return ret.build();
  }

  private static ImmutableList<Symbol> diversityFeature(final ProcessedEvent features) {
    final ImmutableList<Symbol> predicates = features.getStems();
    if (predicates.size() > 2) {
      // Cut down to first two predicates if needed
      return ImmutableList.copyOf(predicates.subList(0, 2));
    } else {
      return predicates;
    }
  }

  private enum TopLevelCodeFunction implements Function<Symbol, Symbol> {
    INSTANCE;

    @Override
    public Symbol apply(@Nullable Symbol input) {
      checkNotNull(input);
      return CAMEOCodes.topLevelCode(input);
    }
  }
}
