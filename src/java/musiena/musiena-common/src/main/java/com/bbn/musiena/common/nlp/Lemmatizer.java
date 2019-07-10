package com.bbn.musiena.common.nlp;


import com.google.common.base.Joiner;
import com.google.common.base.Splitter;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.Lists;
import com.google.common.collect.Maps;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.util.List;
import java.util.Map;

public final class Lemmatizer {
  private final Map<String, String> lemmaMap;


  private Lemmatizer(final Map<String, String> lemmaMap) {
    this.lemmaMap = lemmaMap;
  }

  public static Lemmatizer from(final String resourceName) throws IOException {
    InputStream is = Lemmatizer.class.getResourceAsStream(resourceName);
    BufferedReader reader = new BufferedReader(new InputStreamReader(is, "UTF-8"));

    //final String resourcePath = Resources.getResource(Lemmatizer.class, resourceName).getPath();

    final Splitter splitter = Splitter.on(" ").trimResults().omitEmptyStrings();

    //BufferedReader reader = Files.asCharSource(new File(resourcePath), Charsets.UTF_8).openBufferedStream();

    String line;
    Map<String, String> lemmaMap = Maps.newHashMap();
    while((line = reader.readLine())!=null) {
      final ImmutableList<String> tokens = ImmutableList.copyOf(splitter.split(line));
      if(tokens.size()==2) {
        lemmaMap.put(tokens.get(0), tokens.get(1));
      }
    }

    return new Lemmatizer(lemmaMap);
  }

  public String getLemma(final String w) {
    final String s = w.toLowerCase();
    if(lemmaMap.containsKey(s)) {
      return lemmaMap.get(s);
    } else {
      return s;
    }
  }

  public Map<String, String> getLemmaMap() {
    return lemmaMap;
  }

  public String lemmatizePhrase(final String phrase) {
    final ImmutableList<String> tokens = ImmutableList.copyOf(Splitter.on(" ").trimResults().omitEmptyStrings().split(phrase));

    List<String> lemmas = Lists.newArrayList();
    for(final String token : tokens) {
      if(lemmaMap.containsKey(token)) {
        lemmas.add(lemmaMap.get(token));
      } else {
        lemmas.add(token);
      }
    }

    return Joiner.on("_").join(lemmas);
  }

}
