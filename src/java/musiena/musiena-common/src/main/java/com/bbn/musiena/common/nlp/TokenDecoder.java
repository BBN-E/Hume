package com.bbn.musiena.common.nlp;


import com.google.common.base.Joiner;
import com.google.common.collect.ImmutableList;

import opennlp.tools.tokenize.Tokenizer;
import opennlp.tools.tokenize.TokenizerME;
import opennlp.tools.tokenize.TokenizerModel;

import java.io.IOException;
import java.io.InputStream;

public final class TokenDecoder {
  private final Tokenizer decoder;
  private final Joiner whiteSpaceJoiner;

  private TokenDecoder(final Tokenizer decoder) {
    this.decoder = decoder;
    this.whiteSpaceJoiner = Joiner.on(" ");

  }

  public static TokenDecoder from(final String resourceName) throws IOException {
    InputStream modelIn = TokenDecoder.class.getResourceAsStream(resourceName);
    //final String resourcePath = Resources.getResource(TokenDecoder.class, resourceName).getPath();
    //InputStream modelIn = new FileInputStream(resourcePath);

    TokenizerModel model = new TokenizerModel(modelIn);
    Tokenizer decoder = new TokenizerME(model);

    return new TokenDecoder(decoder);
  }

  public ImmutableList<String> decode(final String input) {
    return ImmutableList.copyOf(decoder.tokenize(input));
  }

  public String decodeAsString(final String input) {
    return whiteSpaceJoiner.join(decoder.tokenize(input));
  }



}
