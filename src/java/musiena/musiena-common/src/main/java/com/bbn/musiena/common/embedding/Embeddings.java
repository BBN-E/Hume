package com.bbn.musiena.common.embedding;


import com.bbn.bue.common.parameters.Parameters;
import com.bbn.musiena.common.theory.RealVector;

import com.google.common.base.Charsets;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableSet;
import com.google.common.io.Files;
import com.google.common.primitives.Doubles;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.BufferedReader;
import java.io.File;
import java.io.IOException;

import static com.google.common.base.Preconditions.checkArgument;

public final class Embeddings {
  private static final Logger log = LoggerFactory.getLogger(Embeddings.class);

  private final ImmutableList<RealVector> vectors;
  private final ImmutableMap<String, Integer> vocab;


  private Embeddings(final ImmutableList<RealVector> vectors, final ImmutableMap<String, Integer> vocab) {
    this.vectors = ImmutableList.copyOf(vectors);
    this.vocab = ImmutableMap.copyOf(vocab);
  }

  public static Embeddings from(final Parameters params) throws IOException {
    return from(params.getExistingFile("word.vocab"), params.getExistingFile("word.embeddings"));
    //final ImmutableMap<String, Integer> vocab = readVocab(params.getExistingFile("word.vocab"));
    //return new Embeddings(readEmbeddings(params.getExistingFile("word.embeddings"), vocab.keySet()), vocab);
  }

  public static Embeddings from(final ImmutableMap<String, String> params) throws IOException {
    return from(new File(params.get("word.vocab")), new File(params.get("word.embeddings")));
    //final ImmutableMap<String, Integer> vocab = readVocab(new File(params.get("word.vocab")));
    //return new Embeddings(readEmbeddings(new File(params.get("word.embeddings")), vocab.keySet()), vocab);
  }

  public static Embeddings from(final File wordVocab, final File wordEmbeddings) throws IOException {
    final ImmutableMap<String, Integer> vocab = readVocab(wordVocab);
    return new Embeddings(readEmbeddings(wordEmbeddings, vocab.keySet()), vocab);
  }

  public ImmutableList<RealVector> getVectors() {
    return vectors;
  }

  public int numberOfVectors() {
    return vectors.size();
  }

  public ImmutableMap<String, Integer> getVocab() {
    return vocab;
  }

  public int frequencyOfWord(final String word) {
    return vocab.get(word);
  }

  public RealVector getVectorByIndex(final int index) {
    checkArgument(0<=index && index<vectors.size());
    return vectors.get(index);
  }

  private static ImmutableList<RealVector> readEmbeddings(final File infile, final ImmutableSet<String> vocab) throws IOException {
    final BufferedReader br = Files.asCharSource(infile, Charsets.UTF_8).openBufferedStream();

    int lineCount = 0;

    String line;
    final ImmutableList.Builder<RealVector> ret = ImmutableList.builder();
    while ((line = br.readLine()) != null) {
      final String[] tokens = line.split(" ");
      final String id = tokens[0];

      if(vocab.contains(id)) {
        double[] values = new double[tokens.length-1];
        for(int i=1; i<tokens.length; i++) {        // and now we record the embeddings (real numbers)
          final double v = Doubles.tryParse(tokens[i]);
          values[i-1] = v;
        }

        ret.add(RealVector.builder().id(id).vector(values).build());

        lineCount += 1;
        if((lineCount % 100000)==0) {
          log.info("Loaded {} embeddings", lineCount);
        }
      }
    }
    br.close();

    return ret.build();
  }

  private static ImmutableMap<String, Integer> readVocab(final File vocabFile) throws IOException {
    final ImmutableList<String> lines = Files
        .asCharSource(vocabFile, Charsets.UTF_8).readLines();

    final ImmutableMap.Builder<String, Integer> ret = ImmutableMap.builder();
    for(final String line : lines) {
      if(line.indexOf(" ")!=-1) {
        final String[] tokens = line.split(" ");
        ret.put(tokens[0], Integer.parseInt(tokens[1]));
      } else {
        ret.put(line, 1); // dummy 1
      }
    }

    return ret.build();
  }

  public ImmutableMap<String, Integer> constructWordIdToIndex() {
    final ImmutableMap.Builder<String, Integer> ret = ImmutableMap.builder();

    for(int i=0; i<vectors.size(); i++) {
      ret.put(vectors.get(i).id(), i);
    }

    return ret.build();
  }

  // we assume all embeddings are of the same size
  public int getDimensionSize() {
    return vectors.get(0).vector().length;
  }
}
