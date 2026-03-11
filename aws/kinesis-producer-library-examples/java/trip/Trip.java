package trip;

import com.fasterxml.jackson.annotation.JsonPropertyOrder;


@JsonPropertyOrder({"id", "vendorId", "pickupDate", "dropoffDate", "passengerCount",
"pickupLongitude", "pickupLatitude", "dropoffLongitude", "dropoffLatitude",
"storeAndFwdFlag", "gcDistance", "tripDuration", "googleDistance", "googleDuration"})
public class Trip {
    
    public String id;
    public int vendorId;
    public String pickupDate;
    public String dropoffDate;
    public int passengerCount;
    public float pickupLongitude;
    public float pickupLatitude;
    public float dropoffLongitude;
    public float dropoffLatitude;
    public char storeAndFwdFlag;
    public float gcDistance;
    public long tripDuration;
    public long googleDistance;
    public long googleDuration;

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public int getVendorId() {
        return vendorId;
    }

    public void setVendorId(int vendorId) {
        this.vendorId = vendorId;
    }

    public int getPassengerCount() {
        return passengerCount;
    }

    public void setPassengerCount(int passengerCount) {
        this.passengerCount = passengerCount;
    }

    public float getPickupLongitude() {
        return pickupLongitude;
    }

    public void setPickupLongitude(float pickupLongitude) {
        this.pickupLongitude = pickupLongitude;
    }

    public float getPickupLatitude() {
        return pickupLatitude;
    }

    public void setPickupLatitude(float pickupLatitude) {
        this.pickupLatitude = pickupLatitude;
    }

    public float getDropoffLongitude() {
        return dropoffLongitude;
    }

    public void setDropoffLongitude(float dropoffLongitude) {
        this.dropoffLongitude = dropoffLongitude;
    }

    public float getDropoffLatitude() {
        return dropoffLatitude;
    }

    public void setDropoffLatitude(float dropoffLatitude) {
        this.dropoffLatitude = dropoffLatitude;
    }

    public char getStoreAndFwdFlag() {
        return storeAndFwdFlag;
    }

    public void setStoreAndFwdFlag(char storeAndFwdFlag) {
        this.storeAndFwdFlag = storeAndFwdFlag;
    }

    public float getGcDistance() {
        return gcDistance;
    }


    public void setGcDistance(float gcDistance) {
        this.gcDistance = gcDistance;
    }

    public long getTripDuration() {
        return tripDuration;
    }

    public void setTripDuration(long tripDuration) {
        this.tripDuration = tripDuration;
    }

    public long getGoogleDistance() {
        return googleDistance;
    }

    public void setGoogleDistance(long googleDistance) {
        this.googleDistance = googleDistance;
    }

    public long getGoogleDuration() {
        return googleDuration;
    }

    public void setGoogleDuration(long googleDuration) {
        this.googleDuration = googleDuration;
    }

    public String getPickupDate() {
        return pickupDate;
    }

    public void setPickupDate(String pickupDate) {
        this.pickupDate = pickupDate;
    }

    public String getDropoffDate() {
        return dropoffDate;
    }

    public void setDropoffDate(String dropoffDate) {
        this.dropoffDate = dropoffDate;
    }


    @Override
    public String toString() {
        return "trip.Trip{" +
                "id='" + id + '\'' +
                ", vendorId=" + vendorId +
                ", pickupDate=" + pickupDate +
                ", dropoffDate=" + dropoffDate +
                ", passengerCount=" + passengerCount +
                ", pickupLongitude=" + pickupLongitude +
                ", pickupLatitude=" + pickupLatitude +
                ", dropoffLongitude=" + dropoffLongitude +
                ", dropoffLatitude=" + dropoffLatitude +
                ", storeAndFwdFlag=" + storeAndFwdFlag +
                ", gcDistance=" + gcDistance +
                ", tripDuration=" + tripDuration +
                ", googleDistance=" + googleDistance +
                ", googleDuration=" + googleDuration +
                '}';
    }

}
