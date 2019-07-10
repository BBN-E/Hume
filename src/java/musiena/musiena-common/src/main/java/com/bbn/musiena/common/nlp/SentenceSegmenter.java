package com.bbn.musiena.common.nlp;


import com.google.common.collect.ImmutableList;

import opennlp.tools.sentdetect.SentenceDetectorME;
import opennlp.tools.sentdetect.SentenceModel;

import java.io.IOException;
import java.io.InputStream;

public final class SentenceSegmenter {
  private final SentenceDetectorME decoder;

  private SentenceSegmenter(final SentenceDetectorME decoder) {
    this.decoder = decoder;
  }

  public static SentenceSegmenter from(final String resourceName) throws IOException {
    final InputStream modelIn = SentenceSegmenter.class.getResourceAsStream(resourceName);
    //final String resourcePath = Resources.getResource(SentenceSegmenter.class, resourceName).getPath();
    //InputStream modelIn = new FileInputStream(resourcePath);

    SentenceModel model = new SentenceModel(modelIn);
    SentenceDetectorME decoder = new SentenceDetectorME(model);

    return new SentenceSegmenter(decoder);
  }

  public ImmutableList<String> decode(final String input) {
    return ImmutableList.copyOf(decoder.sentDetect(input));
  }


}
