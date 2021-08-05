# FPF Guild Event Logger

Made for deployment on an AWS Lambda function, called by a cloudwatch event setup with CRON. Will fetch all user profile data from `player_main_profiles`, and extract data as outlined in `point_params` before saving a log entry to `timedata`.

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

# Example data in each setup collection on the DB

## `point_params`

```json
[
  {
    "enabled": true,
    "display_name": "Fishing XP",
    "profile_path": "experience_skill_fishing",
    "weight": 1
  },
  {
    "enabled": true,
    "display_name": "Flaming Worm Kills",
    "profile_path": "stats.kills_flaming_worm",
    "weight": 8.5
  }
]
```

## `player_main_profiles`

```json
[
  {
    "username": "RabidSheep55",
    "uuid": "b4f65141c5dd43939655919a519d957c",
    "profileID": "b4f65141c5dd43939655919a519d957c",
    "cute_name": "Watermelon"
  },
  {
    "username": "Appable",
    "uuid": "59998433ceda41c1b0acffe7d9b33594",
    "profileID": "5d81ccb06c2745e58818c865b01edb69",
    "cute_name": "Orange"
  },
  {
    "username": "COOKIE1799",
    "uuid": "30104365d49a43f4845948b9872c0ea3",
    "profileID": "30104365d49a43f4845948b9872c0ea3",
    "cute_name": "Zucchini"
  }
]
```
