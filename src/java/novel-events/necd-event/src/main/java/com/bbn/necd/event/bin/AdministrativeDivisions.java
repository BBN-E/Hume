package com.bbn.necd.event.bin;

import com.bbn.bue.common.symbols.Symbol;

import com.google.common.base.Optional;
import com.google.common.collect.ImmutableList;

import static com.google.common.base.Preconditions.checkNotNull;

/**
 * Created by ychan on 8/8/16.
 */
public final class AdministrativeDivisions {
  AdministrativeDivisions(Long geoID,Symbol countryCode,
      Optional<Symbol> admin1, Optional<Symbol> admin2, Optional<Symbol> admin3,
      Optional<Symbol> admin4) {
    checkNotNull(geoID);
    checkNotNull(countryCode);
    this.geoID = geoID;
    this.countryCode = countryCode;
    this.admin1 = admin1;
    this.admin2 = admin2;
    this.admin3 = admin3;
    this.admin4 = admin4;
  }

  public Optional<Symbol> admin1() {
    return admin1;
  }

  public Optional<Symbol> admin2() {
    return admin2;
  }

  public Optional<Symbol> admin3() {
    return admin3;
  }

  public Optional<Symbol> admin4() {
    return admin4;
  }

  public Long geoID(){
    return geoID;
  }

  public Symbol countryCode(){
    return countryCode;
  }

  private final Optional<Symbol> admin1;
  private final Optional<Symbol> admin2;
  private final Optional<Symbol> admin3;
  private final Optional<Symbol> admin4;
  private final Long geoID;
  private final Symbol countryCode;

  @Override
  public int hashCode() {
    return geoID.hashCode();
  }

  @Override
  public boolean equals(Object obj) {
    if (this == obj) {
      return true;
    }
    if (obj == null || getClass() != obj.getClass()) {
      return false;
    }
    final AdministrativeDivisions other = (AdministrativeDivisions) obj;
    return this.geoID.equals(other.geoID);
  }

  public static AdministrativeDivisions from(Long geoID, Symbol countryCode,
      Optional<Symbol> admin1, Optional<Symbol> admin2, Optional<Symbol> admin3,
      Optional<Symbol> admin4) {
    return new AdministrativeDivisions(geoID,countryCode,admin1,admin2,admin3,admin4);
  }

  /**
   * Checks if the administrative divisions represented by this object subsume the ones
   * represented by the object in the argument.<br>
   * For example, [Massachusets, United States] would subsume [Suffolk County, Massachusetts, United States]
   * and [Suffolk County, Massachusetts, United States] would subsume [Boston, Suffolk County, Massachusetts,
   * United States]. However, [Massachusetts, United States] would not subsume [X, United States]
   * since the missing admin division (state's name) in the second object makes it ambigious for comparison.<br>
   * Similarly, [Boston,Massachusetts,United States] would not subsume [Boston,England], since they have different
   * countries.
   *
   * @param that The {@link AdministrativeDivisions} object whose subsumption in this object is to be checked
   * @return true, if that is subsumed by this; false, otherwise
   */
  public boolean subsumes(AdministrativeDivisions that){
    checkNotNull(that);
    if(this.equals(that)){
      return false;
    }
    if(!this.countryCode.equalTo(that.countryCode)){
      return false;
    }
    ImmutableList<Optional<Symbol>> thisAdmins = ImmutableList.of(this.admin1,this.admin2,
        this.admin3,this.admin4);
    ImmutableList<Optional<Symbol>> thatAdmins = ImmutableList.of(that.admin1,that.admin2,
        that.admin3,that.admin4);
    //Admin divisions increase in specificity in the following order admin1,admin2,admin3,admin4
    //If a particular abmin division is absent, all the following more specific ones will be absent too
    for(int i=0;i<thisAdmins.size();i++){
      Optional<Symbol> thisAdmin = thisAdmins.get(i);
      Optional<Symbol> thatAdmin = thatAdmins.get(i);
      if(thisAdmin.isPresent()){
        if(thatAdmin.isPresent()){
          if(!thisAdmin.get().equalTo(thatAdmin.get())){
            return false;
          }
        }else{
          return false;
        }
      }else{
        if(thatAdmin.isPresent()){
          return true;
        }
      }
    }
    return false;
  }
}
