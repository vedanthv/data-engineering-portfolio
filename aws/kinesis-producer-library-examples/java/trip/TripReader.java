package trip;

import java.io.File;
import java.text.ParseException;
import java.time.Instant;
import java.util.List;
import java.util.stream.Collectors;

import com.fasterxml.jackson.databind.MappingIterator;
import com.fasterxml.jackson.dataformat.csv.CsvMapper;
import com.fasterxml.jackson.dataformat.csv.CsvSchema;

import org.joda.time.DateTime;
import org.joda.time.format.DateTimeFormat;
import org.joda.time.format.DateTimeFormatter;


public class TripReader {

    private static DateTime firstDate = null;
    private static long timeDeltaBetweenFirstDateAndNow = 0;

    public static List<Trip> readFile(File csvFile) throws Exception {
        CsvMapper mapper = new CsvMapper();
        CsvSchema schema = mapper.schemaFor(Trip.class).withSkipFirstDataRow(true);
        MappingIterator<Trip> iterator = mapper.readerFor(Trip.class).with(schema).readValues(csvFile);
        List<Trip> tripsToReturn =  iterator.readAll()
                .stream().map(x -> {
                    try {
                        return modifyIncomingDates(x);
                    } catch (ParseException e) {
                        return null;
                    }
                }).collect(Collectors.toList());

        firstDate = null; // reset
        return tripsToReturn;
    }

    public static Trip modifyIncomingDates(Trip trip) throws ParseException
    {

        // convert strings to dates for manipulation
        DateTimeFormatter sourceFormat = DateTimeFormat.forPattern("MM/dd/yyyy HH:mm");
        DateTimeFormatter outputFormat = DateTimeFormat.forPattern("yyyy-MM-dd'T'HH:mm:ss");


        DateTime pickupDateObject = DateTime.parse(trip.pickupDate, sourceFormat);
        DateTime dropoffDateObject = DateTime.parse(trip.dropoffDate, sourceFormat);


        if(firstDate == null)
        {
            firstDate = pickupDateObject;
            timeDeltaBetweenFirstDateAndNow = Instant.now().getEpochSecond()*1000
                    - firstDate.getMillis();
        }

        trip.pickupDate = outputFormat.print(pickupDateObject.getMillis()
                + timeDeltaBetweenFirstDateAndNow);
        trip.dropoffDate =  outputFormat.print(dropoffDateObject.getMillis()
                + timeDeltaBetweenFirstDateAndNow);

        return trip;
    }
}

