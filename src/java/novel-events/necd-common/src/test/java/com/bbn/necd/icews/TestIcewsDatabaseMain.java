package com.bbn.necd.icews;

import com.bbn.bue.common.parameters.Parameters;

import java.io.File;
import java.io.IOException;
import java.sql.SQLException;

/**
 * Test basic ICEWS DB loading.
 */
public final class TestIcewsDatabaseMain {

  public static void main(String[] args) throws IOException, SQLException {
    final File paramsFile = new File(TestIcewsDatabaseMain.class.getResource("/icewsdb.params").getPath());
    final ICEWSDatabase db = ICEWSDatabase.fromParameters(Parameters.loadSerifStyle(paramsFile));
    // Try out whatever you like here
  }
}
