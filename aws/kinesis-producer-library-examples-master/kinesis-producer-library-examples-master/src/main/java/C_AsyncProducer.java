import java.io.File;
import java.nio.ByteBuffer;
import java.util.List;
import com.amazonaws.services.kinesis.producer.KinesisProducer;
import com.amazonaws.services.kinesis.producer.KinesisProducerConfiguration;
import com.amazonaws.services.kinesis.producer.UserRecordResult;
import com.google.common.util.concurrent.FutureCallback;
import com.google.common.util.concurrent.Futures;
import com.google.common.util.concurrent.ListenableFuture;
import com.google.common.util.concurrent.MoreExecutors;

import org.json.JSONObject;
import trip.Trip;
import trip.TripReader;

public class C_AsyncProducer {

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
                .setRecordTtl(60000);

        final KinesisProducer kinesis = new KinesisProducer(config);


        FutureCallback<UserRecordResult> myCallback = new FutureCallback<UserRecordResult>() {
            @Override public void onFailure(Throwable t) {
                /* Analyze and respond to the failure  */
                t.printStackTrace();
            };
            @Override public void onSuccess(UserRecordResult result) {
            };
        };

        while(true) {
            for (Trip trip : trips) {
                ByteBuffer data = ByteBuffer.wrap(new JSONObject(trip).toString().getBytes("UTF-8"));
                ListenableFuture<UserRecordResult> f = kinesis.addUserRecord(streamName, trip.getId(), data);
                // If the Future is complete by the time we call addCallback, the callback will be invoked immediately.
                Futures.addCallback(f, myCallback, MoreExecutors.directExecutor());
            }
        }

    }

}
