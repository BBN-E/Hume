package com.bbn.necd.common;

import com.bbn.bue.common.parameters.Parameters;
import com.bbn.bue.common.symbols.Symbol;

import com.google.common.base.Optional;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.primitives.Doubles;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.util.List;

/**
 * Created by ychan on 2/9/16.
 * Parameters:
 * - data.predictVectorFile
 * - feature.minValue
 * - pvManager.load (true or false)
 */
public final class PredictVectorManager {
  final ImmutableList<Symbol> featureType;
  final ImmutableMap<Symbol, PredictVector> vectors;


  private PredictVectorManager(final ImmutableList<Symbol> featureType, final ImmutableMap<Symbol, PredictVector> vectors) {
    this.featureType = featureType;
    this.vectors = vectors;
  }

  public int getDim() {
    return featureType.size();
  }

  public ImmutableList<Symbol> getFeatureType() {
    return featureType;
  }

  public ImmutableMap<Symbol, PredictVector> getVectors() {
    return vectors;
  }

  public Optional<PredictVector> getVector(final Symbol id) {
    return Optional.fromNullable(vectors.get(id));
  }

  public static Builder fromParams(final Parameters params) {
    return new Builder(params);
  }


  public static final class Builder {
    private final List<String> vectorFiles;
    private final double minValue;
    private int dim = 0;
    private final boolean pvManagerLoad;

    private Builder(final Parameters params) {
      this.vectorFiles = params.getStringList("data.predictVectorFile");
      this.minValue = params.getDouble("feature.minValue");
      this.pvManagerLoad = params.getBoolean("pvManager.load");
    }

    public PredictVectorManager build() throws  IOException {
      final ImmutableMap<Symbol, PredictVector> vectors = pvManagerLoad? readVectorFiles(vectorFiles) : ImmutableMap.<Symbol, PredictVector>of();

      final ImmutableList.Builder<Symbol> featureTypeBuilder = ImmutableList.builder();
      for(int i=0; i<dim; i++) {
        featureTypeBuilder.add(Symbol.from(PV + ":" + i));
      }
      final ImmutableList<Symbol> featureType = featureTypeBuilder.build();

      return new PredictVectorManager(featureType, vectors);
    }

    private ImmutableMap<Symbol, PredictVector> readVectorFiles(final List<String> files) throws IOException {
      final ImmutableMap.Builder<Symbol, PredictVector> ret = ImmutableMap.builder();

      for(final String fileString : files) {
        BufferedReader br = new BufferedReader(new FileReader(new File(fileString)));
        String line;

        while ((line = br.readLine()) != null) {
          String[] tokens;
          if(line.indexOf("\t")!=-1) {
            tokens = line.split("\t");
          } else {
            tokens = line.split(" ");
          }
          final Symbol id = Symbol.from(tokens[0]);   // the actual word
          double[] values = new double[tokens.length-1];
          for(int i=1; i<tokens.length; i++) {        // and now we record the embeddings (real numbers)
            final double v = Doubles.tryParse(tokens[i]);
            if(v < minValue) {
              values[i-1] = minValue;
            } else {
              values[i-1] = v;
            }
          }

          dim = values.length;    // all the words should have the same dimension
          ret.put(id, PredictVector.from(id, values));
        }

        br.close();
      }

      /*
      final ImmutableList<String> lines = Files.asCharSource(file, Charsets.UTF_8).readLines();
      for(final String line : lines) {
        String[] tokens;
        if(line.indexOf("\t")!=-1) {
          tokens = line.split("\t");
        } else {
          tokens = line.split(" ");
        }
        final Symbol id = Symbol.from(tokens[0]);   // the actual word
        double[] values = new double[tokens.length-1];
        for(int i=1; i<tokens.length; i++) {        // and now we record the embeddings (real numbers)
          final double v = Doubles.tryParse(tokens[i]);
          if(v < minValue) {
            values[i-1] = minValue;
          } else {
            values[i-1] = v;
          }
        }

        dim = values.length;    // all the words should have the same dimension
        ret.put(id, PredictVector.from(id, values));
      }
      */

      return ret.build();
    }
  }


  public static final class PredictVector {
    private final Symbol id;
    private final double[] values;

    private PredictVector(final Symbol id, final double[] values) {
      this.id = id;
      this.values = values;
    }

    public static PredictVector from(final Symbol id, final double[] values) {
      return new PredictVector(id, values);
    }

    public Symbol getId() {
      return id;
    }

    public double[] getValues() {
      return values;
    }

    public String toString() {
      StringBuilder sb = new StringBuilder();
      sb.append(id.asString());

      for(int i=0; i<values.length; i++) {
        sb.append("\t");
        sb.append(String.valueOf(values[i]));
      }

      return sb.toString();
    }
  }

  private static final String PV = "PV";   // feature type prefix
}
