import com.amazonaws.services.kinesis.producer.KinesisProducer;
import com.amazonaws.services.kinesis.producer.KinesisProducerConfiguration;
import org.json.JSONObject;
import trip.Trip;
import trip.TripReader;

import java.io.File;
import java.nio.ByteBuffer;
import java.util.List;

public class D_Producer_With_ConfigFile {

    public static String streamName = "input-stream";
    public static String region = "us-east-1";

    public static void main(String[] args) throws Exception {
        File tripCsv = new File("data/taxi-trips.csv");

        List<Trip> trips = TripReader.readFile(tripCsv);


        KinesisProducerConfiguration config = KinesisProducerConfiguration.fromPropertiesFile("default_config.properties");
        final KinesisProducer kinesis = new KinesisProducer(config);

        while (true) {
            for (Trip trip : trips) {
                ByteBuffer data = ByteBuffer.wrap(new JSONObject(trip).toString().getBytes("UTF-8"));
                // doesn't block
                kinesis.addUserRecord(streamName, trip.getId(), data);
            }
        }

    }
}
