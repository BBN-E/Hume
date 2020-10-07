package com.bbn.serif.util.events.consolidator.common;

import com.bbn.bue.common.parameters.Parameters;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.bue.geonames.GeoNames;
import com.bbn.bue.geonames.GeonamesException;
import com.bbn.serif.theories.DocTheory;
import com.bbn.serif.theories.Entity;
import com.bbn.serif.theories.EventMention;
import com.bbn.serif.theories.Mention;
import com.bbn.serif.theories.Value;
import com.bbn.serif.theories.ValueMention;

import com.google.common.base.Optional;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Lists;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;

public final class SieveUtils {

  private static final Logger log = LoggerFactory.getLogger(SieveUtils.class);

  private SieveUtils() {
    throw new UnsupportedOperationException();
  }


  // ==== Get Mentions and Entities for event argument
  public static Optional<Mention> getEntityMention(final EventMention.Argument arg) {
    if (arg instanceof EventMention.MentionArgument) {
      EventMention.MentionArgument mention = (EventMention.MentionArgument) arg;
      return Optional.of(mention.mention());
    } else {
      return Optional.absent();
    }
  }

  public static Optional<String> getEntityMentionText(final EventMention.Argument arg) {
    Optional m = getEntityMention(arg);
    return m.isPresent()?Optional.of(((Mention)m.get()).span().tokenizedText().utf16CodeUnits()):Optional.absent();
  }

  public static Optional<Entity> getEntity(final EventMention.Argument arg, final DocTheory doc) {
    final Optional<Mention> mention = getEntityMention(arg);
    if(mention.isPresent()) {
      return mention.get().entity(doc);
    } else {
      return Optional.absent();
    }
  }

  public static ImmutableSet<Entity> getEntities(final ImmutableSet<EventMention.Argument> args, final DocTheory doc) {
    final ImmutableSet.Builder<Entity> ret = ImmutableSet.builder();

    for(final EventMention.Argument arg : args) {
      final Optional<Entity> entity = getEntity(arg, doc);
      if(entity.isPresent()) {
        ret.add(entity.get());
      }
    }

    return ret.build();
  }
  // ==== END ====


  // ==== Get Values for event argument
  public static Optional<ValueMention> getValueMention(final EventMention.Argument arg) {
    if(arg instanceof EventMention.ValueMentionArgument) {
      EventMention.ValueMentionArgument mention = (EventMention.ValueMentionArgument) arg;
      return Optional.of(mention.valueMention());
    } else {
      return Optional.absent();
    }
  }

  public static Optional<Value> getValue(final EventMention.Argument arg) {
    final Optional<ValueMention> mention = getValueMention(arg);
    if(mention.isPresent()) {
      return mention.get().documentValue();
    } else {
      return Optional.absent();
    }
  }

  public static ImmutableSet<Value> getValues(final ImmutableSet<EventMention.Argument> args) {
    final ImmutableSet.Builder<Value> ret = ImmutableSet.builder();

    for(final EventMention.Argument arg : args) {
      final Optional<Value> value = getValue(arg);
      if(value.isPresent()) {
        ret.add(value.get());
      }
    }

    return ret.build();
  }
  // ==== END ====

  // if the input 'arg' is a value mention, get its timexVal
  public static Optional<Symbol> getTimexVal(final EventMention.Argument arg) {
    final Optional<Value> value = getValue(arg);
    if(value.isPresent()) {
      return value.get().timexVal();
    } else {
      return Optional.absent();
    }
  }

  /*
  // ==== sorting
  public static Function<EventCandidate, Integer> firstAnchorStartFunction() {
    return new Function() {
      public Integer apply(EventCandidate input) {
        return (Integer) Ordering.natural().min(FluentIterable.from(input.getAnchorNodes()).transform(SherlockAccessor.anchorStartFunction()));
      }
    };
  }

  public static Function<SynNode, Integer> anchorStartFunction() {
    return new Function() {

      public Integer apply(final SynNode input) {
        return Integer.valueOf(input.span().startIndex());
      }
    };
  }
  */

  public static ArrayList<EventCandidate> sortedEventCandidatesByAnchor(final ImmutableList<EventCandidate> eventCandidates) {
    //this.eventMentions.sort(Comparator.comparing(EventMention::anchorNode::compare));
    //ArrayList<EventMention> sortedEventMentions = Lists.newArrayList(this.eventMentions);

    EventCandidate[] sortedEventCandidates = new EventCandidate[eventCandidates.size()];
    for(int i=0; i<eventCandidates.size(); i++) {
      sortedEventCandidates[i] = eventCandidates.get(i);
    }
    //EventCandidate[] sortedEventCandidates = eventCandidates.clone();

    Arrays.sort(sortedEventCandidates, new Comparator<EventCandidate>() {
      @Override
      public int compare(EventCandidate a, EventCandidate b) {
        return a.sortedEventMentionsByAnchor().get(0).anchorNode().headIndex() - b.sortedEventMentionsByAnchor().get(0).anchorNode().headIndex();
      }
    });

    return Lists.newArrayList(sortedEventCandidates);
  }

  public static GeoNames getGeonames(final Parameters params) throws GeonamesException, ClassNotFoundException {
    return GeoNames.connectToGeonamesDB(params.getExistingFile("kbpEvents.sherlock.geonames.dbFile"));
  }

  public static final Symbol NN = Symbol.from("NN");
  public static final Symbol NNS = Symbol.from("NNS");
}

