package com.bbn.necd.event.bin;

import com.bbn.bue.common.parameters.Parameters;
import com.bbn.serif.common.SerifException;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;

import static com.google.common.base.Preconditions.checkNotNull;

/**
 * Created by ychan on 8/8/16.
 */
public final class TryQuery {
  private static final Logger log = LoggerFactory.getLogger(TryQuery.class);

  public static void main(final String[] argv) throws IOException {
    final String paramFilename = argv[0];

    final Parameters params = Parameters.loadSerifStyle(new File(paramFilename));
    log.info(params.dump());

    checkNotNull(params);
    GeoActors geoActors = null;
    try {
      geoActors = GeoActors.connectToGeonamesDB(params.getExistingFile("geoactors.dbFile"));

      final GeoNames geoNames = GeoNames.connectToGeonamesDB(params.getExistingFile("geonames.dbFile"));
      geoNames.locationRecordsForNameString("boston");

    } catch (GeonamesException e) {
      e.printStackTrace();
      throw new SerifException(e);
    }
  }
}
