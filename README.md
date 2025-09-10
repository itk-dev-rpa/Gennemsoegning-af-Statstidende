# Gennemsøgning af Statstidende

This robot fetches the newest data from Statstidende.dk, OPUS SAP and KMD Boliglån and checks if any Statstidende cases could be of relevance. Two lists of cases are created, one for OPUS and one for Boliglån which are sent to the defined receivers by email.

## Arguments

The robot expects the following arguments as a json string:

```json
{
    "opus_receivers": ["hello@email.com"],
    "boliglaan_receivers": ["hello@email.com"]
}
```

Both arguments are lists of emails to send the results to.

## Known issues

### Statstidende

These issues are taking into account in the code and shouldn't be a problem:

- Statstidende's API only supports searching 7 days back in time. If you try to search further you get an error.
- If you search for a Sunday or Monday you get an error.
- Statstidende's API only allow one query per 10 seconds and will return a 429 status code if requests are too frequent.

### Boliglån

KMD Boliglån tends to be really slow when searching for a large number of cases. This might cause problems.

### OPUS

Data from OPUS is delivered by email as multiple Excel sheets split up over multiple emails. Sometimes the delivery of this
data is delayed and won't be there when the robot runs.