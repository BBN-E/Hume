package com.bbn.serif.util.events.consolidator.common;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.serif.theories.DocTheory;
import com.bbn.serif.theories.Entity;
import com.bbn.serif.theories.Event;
import com.bbn.serif.theories.EventMention;
import com.bbn.serif.theories.SynNode;
import com.bbn.serif.theories.Value;
import com.bbn.serif.types.Genericity;
import com.bbn.serif.types.Modality;
import com.bbn.serif.types.Polarity;
import com.bbn.serif.types.Tense;

import com.google.common.base.Optional;
import com.google.common.collect.ArrayListMultimap;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Lists;
import com.google.common.collect.Multimap;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;

public class EventCandidate {
  final private DocTheory doc;
  final private Symbol type;      // event type
  //private ArrayList<EventMention> eventMentions;
  final private ImmutableList<EventMention> eventMentions;

  public EventCandidate(final DocTheory doc, final Symbol type, final ImmutableList<EventMention> eventMentions) {
    this.doc = doc;
    this.type = type;
    this.eventMentions = eventMentions;
  }

  public Symbol type() {
    return this.type;
  }

  public ImmutableList<EventMention> eventMentions() {
    return this.eventMentions;
  }

  //public void addEventMentions(final ImmutableList<EventMention> ems) {
  //  this.eventMentions().addAll(ems);
  //}

  public ImmutableSet<SynNode> getAnchorNodes() {
    final ImmutableSet.Builder<SynNode> ret = ImmutableSet.builder();

    for(final EventMention em : this.eventMentions) {
      ret.add(em.anchorNode());
    }

    return ret.build();
  }

  public ImmutableSet<Symbol> getAnchorPostags() {
    final ImmutableSet.Builder<Symbol> ret = ImmutableSet.builder();

    for(final SynNode node : getAnchorNodes()) {
      ret.add(node.headPOS());
    }

    return ret.build();
  }

  public ImmutableSet<EventMention.Argument> arguments() {
    final ImmutableSet.Builder<EventMention.Argument> ret = ImmutableSet.builder();

    for(final EventMention em : this.eventMentions) {
      ret.addAll(em.arguments());
    }

    return ret.build();
  }

  public ImmutableSet<EventMention.Argument> argsForRole(final Symbol role) {
    final ImmutableSet.Builder<EventMention.Argument> ret = ImmutableSet.builder();

    for(final EventMention em : this.eventMentions) {
      ret.addAll(em.argsForRole(role));
    }

    return ret.build();
  }

  public ImmutableSet<Entity> getEntitiesOfArguments() {
    final ImmutableSet.Builder<Entity> ret = ImmutableSet.builder();

    for(final EventMention em : this.eventMentions) {
      ret.addAll(SieveUtils.getEntities(ImmutableSet.copyOf(em.arguments()), this.doc));
    }

    return ret.build();
  }

  public ImmutableSet<Value> getValuesOfArguments() {
    final ImmutableSet.Builder<Value> ret = ImmutableSet.builder();

    for(final EventMention em : this.eventMentions) {
      ret.addAll(SieveUtils.getValues(ImmutableSet.copyOf(em.arguments())));
    }

    return ret.build();
  }

  public ImmutableSet<Event.EntityArgument> getEntityArguments() {
    final ImmutableSet.Builder<Event.EntityArgument> ret = ImmutableSet.builder();
    Multimap<Entity, Symbol> entityRoles = ArrayListMultimap.create();

    for(final EventMention em : this.eventMentions) {
      for(final EventMention.Argument arg : em.arguments()) {
        final Symbol role = arg.role();
        final Optional<Entity> entity = SieveUtils.getEntity(arg, this.doc);
        if(entity.isPresent()) {
          if(!entityRoles.containsEntry(entity.get(), role)) {
            ret.add(new Event.EntityArgument(entity.get(), role));
            entityRoles.put(entity.get(), role);
          }
        }
      }
    }

    return ret.build();
  }

  public ImmutableSet<Event.ValueArgument> getValueArguments() {
    final ImmutableSet.Builder<Event.ValueArgument> ret = ImmutableSet.builder();
    // I think Value class does not implement hash nor equals functions, so we cannot use it as key
    Multimap<String, Symbol> valueRoles = ArrayListMultimap.create();

    for(final EventMention em : this.eventMentions) {
      for(final EventMention.Argument arg : em.arguments()) {
        final Symbol role = arg.role();
        final Optional<Value> value = SieveUtils.getValue(arg);
        if(value.isPresent()) {
          if(!valueRoles.containsEntry(value.get().span().tokenizedText().toString(), role)) {
            ret.add(new Event.ValueArgument(value.get(), role));
            valueRoles.put(value.get().span().tokenizedText().toString(), role);
          }
        }
      }
    }

    return ret.build();
  }

  public ImmutableSet<Integer> getSentenceNumbers() {
    final ImmutableSet.Builder<Integer> ret = ImmutableSet.builder();
    for(final EventMention em : this.eventMentions) {
      ret.add(em.sentenceTheory(this.doc).sentenceNumber());
    }
    return ret.build();
  }

  public ArrayList<EventMention> sortedEventMentionsByAnchor() {
    //this.eventMentions.sort(Comparator.comparing(EventMention::anchorNode::compare));
    //ArrayList<EventMention> sortedEventMentions = Lists.newArrayList(this.eventMentions);

    EventMention[] sortedEventMentions = new EventMention[this.eventMentions.size()];
    for(int i=0; i<this.eventMentions.size(); i++) {
      sortedEventMentions[i] = this.eventMentions.get(i);
    }
    //EventMention[] sortedEventMentions = (EventMention[]) this.eventMentions.toArray();

    Arrays.sort(sortedEventMentions, new Comparator<EventMention>() {
      @Override
      public int compare(EventMention a, EventMention b) {
        return a.anchorNode().headIndex() - b.anchorNode().headIndex();
      }
    });

    return Lists.newArrayList(sortedEventMentions);
  }

  /*
  @Override
  public int hashCode() {
    final ImmutableSet.Builder<Symbol> ids = ImmutableSet.builder();

    for(final EventMention em : this.eventMentions) {
      if(em.externalID().isPresent()) {
        ids.add(em.externalID().get());
      }
    }
    return Objects.hashCode(ids.build());
  }

  @Override
  public boolean equals(final Object obj) {
    if(this == obj) {
      return true;
    }
    if(obj == null) {
      return false;
    }
    if(getClass() != obj.getClass()) {
      return false;
    }
    final Cluster other = (Cluster) obj;
    return Objects.equal(members, other.members);
  }
  */

  public Genericity getGenericity() {
    return this.eventMentions().get(0).genericity();
  }

  public Modality getModality() {
    return this.eventMentions.get(0).modality();
  }

  public Polarity getPolarity() {
    return this.eventMentions.get(0).polarity();
  }

  public Tense getTense() {
    return this.eventMentions.get(0).tense();
  }

  public Event toEvent() {
    ArrayList arguments = Lists.newArrayList();
    arguments.addAll(getEntityArguments());
    arguments.addAll(getValueArguments());

    final Event event = new Event(arguments, (new com.bbn.serif.theories.EventMentions.Builder()).eventMentions(this.eventMentions).build(), type, getGenericity(), getModality(), getPolarity(), getTense(), null);
    return event;
  }

}
