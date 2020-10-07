package com.bbn.serif.util.events;

import com.google.common.base.Optional;
import org.apache.commons.lang3.tuple.Triple;

import java.util.Collection;

public class GenericEventMention {
    Triple<Integer, Integer, Integer> date;

    Collection<String> eventTypes;

    String predType;
    String predHead;

    Optional<String> modal;
    Optional<String> negation;

    Optional<String> sub_actor;
    Optional<String> obj_actor;

    Optional<String> location;
    Optional<String> time;

    GenericEventMention(String predType, String predHead,
                        Optional<String> modal,
                        Optional<String> negation,
                        Optional<String> sub_actor,
                        Optional<String> obj_actor,
                        Optional<String> location,
                        Optional<String> time,
                        Collection<String> eventTypes,
                        Triple<Integer, Integer, Integer> date) {
        this.predType = predType;
        this.predHead = predHead;

        this.modal = modal;
        this.negation = negation;
        this.sub_actor = sub_actor;
        this.obj_actor = obj_actor;
        this.location = location;
        this.time = time;

        this.eventTypes = eventTypes;

        this.date = date;
    }

    public Collection<String> getEventTypes() {
        return eventTypes;
    }

    public String toTabDelimitedString() {
        StringBuilder stringBuilder = new StringBuilder();
        stringBuilder.append(date.getLeft() + "\t");
        stringBuilder.append(date.getMiddle() + "\t");
        stringBuilder.append(date.getRight() + "\t");

        stringBuilder.append(predType + ":" + predHead);
        stringBuilder.append("\t");
        stringBuilder.append(modal.isPresent()?modal.get():"-");
        stringBuilder.append("\t");

        stringBuilder.append(negation.isPresent()?negation.get():"-");
        stringBuilder.append("\t");

        stringBuilder.append(sub_actor.isPresent()?sub_actor.get():"-");
        stringBuilder.append("\t");

        stringBuilder.append(obj_actor.isPresent()?obj_actor.get():"-");
        stringBuilder.append("\t");

        stringBuilder.append(location.isPresent()?location.get():"-");
        stringBuilder.append("\t");

        stringBuilder.append(time.isPresent()?time.get():"-");
        stringBuilder.append("\t");

        return stringBuilder.toString().trim();
    }

    public static GenericEventMention.Builder builder(String predType, String predHead) {
        return new GenericEventMention.Builder(predType, predHead);
    }

    public static class Builder {

        Triple<Integer, Integer, Integer> date;

        Collection<String> eventTypes;

        String predType;
        String predHead;

        Optional<String> modal;
        Optional<String> negation;

        Optional<String> sub_actor;
        Optional<String> obj_actor;

        Optional<String> location;
        Optional<String> time;

        public Builder(String predType, String predHead) {
            this.predType = predType;
            this.predHead = predHead;

            this.modal = Optional.absent();
            this.negation = Optional.absent();
            this.sub_actor = Optional.absent();
            this.obj_actor = Optional.absent();
            this.location = Optional.absent();
            this.time = Optional.absent();
        }

        public GenericEventMention build() {
            return new GenericEventMention(predType, predHead,
                    modal, negation,
                    sub_actor, obj_actor,
                    location, time, eventTypes, date);
        }

        public GenericEventMention.Builder setModal(String modal) {
            this.modal = Optional.of(modal);
            return this;
        }

        public GenericEventMention.Builder setNegation(String negation) {
            this.negation = Optional.of(negation);
            return this;
        }

        public GenericEventMention.Builder setSubActor(String sub_actor) {
            this.sub_actor = Optional.of(sub_actor);
            return this;
        }

        public GenericEventMention.Builder setObjActor(String obj_actor) {
            this.obj_actor = Optional.of(obj_actor);
            return this;
        }

        public GenericEventMention.Builder setLocation(String location) {
            this.location = Optional.of(location);
            return this;
        }

        public GenericEventMention.Builder setTime(String time) {
            this.time = Optional.of(time);
            return this;
        }

        public GenericEventMention.Builder setEventTypes(Collection<String> eventTypes) {
            this.eventTypes = eventTypes;
            return this;
        }

        public GenericEventMention.Builder setDate(int year, int month, int day) {
            this.date = Triple.of(year, month, day);
            return this;
        }
    }
}
