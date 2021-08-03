# FPF Guild Event Logger

Made for deployment on an AWS Lambda function, called by a cloudwatch event setup with CRON. Will fetch all user profile data from `player_main_profiles`, and extract data as outlined in `profile_data_paths` before saving a log entry to `timedata`.

Connects to a mongodb atlas instance where each of the collections above are hosted.

## Env

Required env variables

| key              | value                                 |
| ---------------- | ------------------------------------- |
| MONGODB_CLUSTER  | cluster.123456d                       |
| MONGODB_USERNAME | LoggerRole                            |
| MONGODB_PASSWORD | somerandomlettersandnumbers           |
| MONGODB_DATABASE | EventName                             |
| HYPIXEL_API_KEY  | 18f3446d-059c-4e1b-8235c-d6a1b2341731 |

The idea is that a new database is used for each event, as players and datapoints will vary.
