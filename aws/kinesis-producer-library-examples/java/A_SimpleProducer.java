import com.amazonaws.services.kinesis.producer.KinesisProducer;
import com.amazonaws.services.kinesis.producer.KinesisProducerConfiguration;
import org.json.JSONObject;
import trip.Trip;
import trip.TripReader;

import java.io.File;
import java.nio.ByteBuffer;
import java.util.List;

public class A_SimpleProducer {

    public static String streamName = "input-stream";
    public static String region = "us-east-1";

    public static void main(String[] args) throws Exception {
        File tripCsv = new File("data/taxi-trips.csv");

        List<Trip> trips = TripReader.readFile(tripCsv);


        KinesisProducerConfiguration config = new KinesisProducerConfiguration()
                .setRecordMaxBufferedTime(3000)
                .setMaxConnections(1)
                .setRequestTimeout(60000)
                .setRegion(region);

        final KinesisProducer kinesis = new KinesisProducer(config);

        System.out.println("Starting to produce data to " + streamName + " in the " + region + " region.");

        while (true) {
            for (Trip trip : trips) {
                ByteBuffer data = ByteBuffer.wrap(new JSONObject(trip).toString().getBytes("UTF-8"));
                // doesn't block
                kinesis.addUserRecord(streamName, trip.getId(), data);
            }
        }

    }
}
