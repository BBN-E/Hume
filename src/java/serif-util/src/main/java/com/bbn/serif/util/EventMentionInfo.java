package com.bbn.serif.util;

import com.google.common.base.Optional;
import com.google.common.collect.Multimap;

import java.util.Map;

public class EventMentionInfo {
    String eventType;
    String docId;
    Optional<Pair<Long, Long>> sentOffset = Optional.absent();
    Pair<Long, Long> triggerOffset;
    Multimap<String, Map<String, String>> roleInfos;
    double score;
    //ImmutableList<Pair<Long, Long>> timeOffset;
    //ImmutableList<Pair<Long, Long>> placeOffset;
    //ImmutableList<Pair<Long, Long>> actorOffset;

    Optional<String> trigger_text = Optional.absent();
    Optional<String> extractorName = Optional.absent();

    EventMentionInfo(final String eventType, final String docId,
        final Optional<Pair<Long, Long>> sentOffset, final Pair<Long, Long> triggerOffset,
        final Multimap<String, Map<String, String>> roleInfos, final double score) {
        //final ImmutableList<Pair<Long, Long>> timeOffset,
        //final ImmutableList<Pair<Long, Long>> placeOffset,
        //final ImmutableList<Pair<Long, Long>> actorOffset) {
        this.eventType = eventType;
        this.docId = docId;
        this.sentOffset = sentOffset;
        this.triggerOffset = triggerOffset;
        this.roleInfos = roleInfos;
        this.score = score;
        //this.timeOffset = timeOffset;
        //this.placeOffset = placeOffset;
        //this.actorOffset = actorOffset;
    }

    public void setTriggerText(String triggerText) {
        trigger_text = Optional.of(triggerText);
    }

    public void setExtractorName(String extractorName) {
        this.extractorName = Optional.of(extractorName);
    }

    public Optional<String> getExtractorName() {
        return this.extractorName;
    }

    public String getEventType() {
        return eventType;
    }

    public String getDocId() {
        return docId;
    }

    public Optional<Pair<Long, Long>> getSentOffset() {
        return sentOffset;
    }

    public Pair<Long, Long> getTriggerOffset() {
        return triggerOffset;
    }

    public Multimap<String, Map<String, String>> getRoleInfos() {
        return roleInfos;
    }

    /*
    public ImmutableList<Pair<Long, Long>> getTimeOffset() {
        return timeOffset;
    }

    public ImmutableList<Pair<Long, Long>> getPlaceOffset() {
        return placeOffset;
    }

    public ImmutableList<Pair<Long, Long>> getActorOffset() {
        return actorOffset;
    }
    */

    public double getScore() {
        return score;
    }

    public String toString() {
        return "docId: " + this.docId
                + "\ttype: " + this.eventType;
    }
}
