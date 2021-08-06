import json, os, pymongo
from pymongo import MongoClient
from dateutil import parser

import httpx
import asyncio


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv("dev.env")

# Setup the MongoDB client (outside of handler function, so it doesnt have to reload)
MONGODB_USERNAME = os.environ.get("MONGODB_USERNAME")
MONGODB_PASSWORD = os.environ.get("MONGODB_PASSWORD")
MONGODB_CLUSTER = os.environ.get("MONGODB_CLUSTER")
MONGODB_DATABASE = os.environ.get("MONGODB_DATABASE")
DB_URI = (
    f"mongodb+srv://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@{MONGODB_CLUSTER}.mongodb.net"
)

client = MongoClient(DB_URI)
db = client[MONGODB_DATABASE]

# Import the tracked players from the DB
profiles = []
for profile in db["player_main_profiles"].find({}, {"_id": 0}):
    profiles += [profile]

print(profiles)

# Import the stats to capture from profile data
profile_data_paths = {}
for item in db["point_params"].find(
    {"enabled": True}, {"_id": 0, "display_name": 1, "profile_path": 1}
):
    profile_data_paths[item["display_name"]] = item["profile_path"]

print(profile_data_paths)

# API Fetching Params
BASE_PROFILE_URL = r"https://api.hypixel.net/skyblock/profile"
HYPIXEL_API_KEY = os.environ.get("HYPIXEL_API_KEY")


def nested_get(data, query_path):
    """Recurive query into a nested dict (data)
    Get the data point at then end of the query path given"""
    if query_path and data:
        element = query_path[0]
        if element:
            value = data.get(element)
            return value if len(query_path) == 1 else nested_get(value, query_path[1:])


async def get_player_data():
    """Async function dispatches individual requests for each `profile` in `profiles`
    Then extracts all the required data using nested dict queries
    """

    # Dispatch all reqs at once
    print("Getting All Player Data")
    async with httpx.AsyncClient() as client:
        tasks = (
            client.get(
                BASE_PROFILE_URL,
                params={"key": HYPIXEL_API_KEY, "profile": profile["profileID"]},
            )
            for profile in profiles
        )
        responses = await asyncio.gather(*tasks)

    # Handle all responses
    print("Parsing Responses")
    data = []
    for i, response in enumerate(responses):
        profile = profiles[i]

        username = profile["username"]
        uuid = profile["uuid"]

        # Add uuid to log (and username, but that's for debugging)
        log = {"username": username, "uuid": uuid}

        try:
            if response.status_code == 200:
                profile_data = response.json()["profile"]["members"][uuid]
                print(f"\t[{username}]: Fetch Successfull")

                # Extract useful info as dictated in the required points
                for label, path in profile_data_paths.items():
                    keys = path.split(".")
                    datapoint = nested_get(profile_data, keys)
                    if datapoint:
                        log[label] = float(datapoint)
                    else:
                        log[label] = None

            else:
                print(f"\t[{username}]: API Fetch Failed [code {response.status_code}]")

        except Exception as e:
            print(f"\t[{username}]: API Fetch Failed [{e}]")

        # Add to log dict
        data += [log]

    return data


def lambda_handler(event, context):
    """Handler called when the cloud function is triggered by an event"""

    # Get All player XPs asyncronously
    data = asyncio.run(get_player_data())

    # Add log timestamp
    doc = {"timestamp": parser.parse(event["time"]), "data": data}
    print("[FETCH] Done, Saving logs...")

    # Save log to the database
    db["timedata"].insert_one(doc)

    return "[DONE]"


if __name__ == "__main__":
    from datetime import datetime

    # Test event that would be sent by a cron job activated cloudwatch event
    test = {
        "id": "cdc73f9d-aea9-11e3-9d5a-835b769c0d9c",
        "detail-type": "Scheduled Event",
        "source": "aws.events",
        "account": "123456789012",
        "time": str(datetime.now()),
        "region": "eu-west-2",
        "resources": ["arn:aws:events:eu-west-2:123456789012:rule/ExampleRule"],
        "detail": {},
    }
    lambda_handler(test, "")
