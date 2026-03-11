import com.amazonaws.services.kinesis.producer.Attempt;
import com.amazonaws.services.kinesis.producer.KinesisProducer;
import com.amazonaws.services.kinesis.producer.KinesisProducerConfiguration;
import com.amazonaws.services.kinesis.producer.UserRecordResult;
import org.json.JSONObject;
import trip.Trip;
import trip.TripReader;

import java.io.File;
import java.nio.ByteBuffer;
import java.util.LinkedList;
import java.util.List;
import java.util.concurrent.Future;

public class B_Producer_withErrorAnalysis {

    public static String streamName = "input-stream";
    public static String region = "us-east-1";

    public static void main(String[] args) throws Exception {
        File tripCsv = new File("data/taxi-trips.csv");

        List<Trip> trips = TripReader.readFile(tripCsv);


        KinesisProducerConfiguration config = new KinesisProducerConfiguration()
                .setRecordMaxBufferedTime(3000)
                .setMaxConnections(1)
                .setRequestTimeout(60000)
                .setRegion(region)
                .setRecordTtl(30000);

        final KinesisProducer kinesis = new KinesisProducer(config);

        // adding a future handler to analyze results
        List<Future<UserRecordResult>> putFutures = new LinkedList<Future<UserRecordResult>>();

        while (true) {
            for (Trip trip : trips) {
                ByteBuffer data = ByteBuffer.wrap(new JSONObject(trip).toString().getBytes("UTF-8"));
                // doesn't block
                putFutures.add(kinesis.addUserRecord(streamName, trip.getId(), data));
            }
            // Wait for puts to finish and check the results
            for (Future<UserRecordResult> f : putFutures) {
                UserRecordResult result = f.get(); // this does block
                if (result.isSuccessful()) {
                    System.out.println("Put record into shard " +
                            result.getShardId());
                } else {
                    for (Attempt attempt : result.getAttempts()) {
                        System.out.println(attempt);
                    }
                }
            }
        }



    }
}
