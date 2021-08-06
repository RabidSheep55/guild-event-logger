import os
import json
import requests as rq
from time import sleep
import httpx
import asyncio
from pymongo import MongoClient


BASE_PLAYER_URL = r"https://api.hypixel.net/player"
BASE_PROFILE_URL = r"https://api.hypixel.net/skyblock/profile"

# Fetch API key from key.txt
from dotenv import load_dotenv

load_dotenv("dev.env")
KEY = os.getenv("HYPIXEL_API_KEY")


# Setup the MongoDB client
MONGODB_USERNAME = os.environ.get("MONGODB_USERNAME")
MONGODB_PASSWORD = os.environ.get("MONGODB_PASSWORD")
MONGODB_CLUSTER = os.environ.get("MONGODB_CLUSTER")
MONGODB_DATABASE = os.environ.get("MONGODB_DATABASE")
DB_URI = (
    f"mongodb+srv://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@{MONGODB_CLUSTER}.mongodb.net"
)

client = MongoClient(DB_URI)
db = client[MONGODB_DATABASE]


async def get_main_profiles(usernames):
    """Retrieves the main profile ID and uuids for each player in usernames"""

    # Find all skyblock profiles associated with username
    async with httpx.AsyncClient(timeout=20.0) as client:
        tasks = (
            client.get(BASE_PLAYER_URL, params={"key": KEY, "name": username})
            for username in usernames
        )
        responses = await asyncio.gather(*tasks)

    # Handle Responses
    data = []
    errors = []
    for i, response in enumerate(responses):
        username = usernames[i]
        # If succesful
        if response.status_code == 200:
            try:
                uuid = response.json()["player"]["uuid"]
                profiles = response.json()["player"]["stats"]["SkyBlock"]["profiles"]
                profileIDs = list(profiles.keys())
                cute_names = [profiles[p]["cute_name"] for p in profiles]

                print(
                    f"[{username}] API Fetch success: found {len(profileIDs)} profiles"
                )
                # for cute_name in cute_names: print(f"\t{cute_name}")
            except Exception as e:
                print(f"[{username}] API Fetch failed {str(e)}")
                errors += [username]
                continue

        else:
            error = response.json()
            print(
                f"[{username}] API Fetch failed [code {response.status_code}] [{error}]"
            )
            errors += [username]
            continue

        # Wait a minute for API rate limit to reset
        # sleep(60)

        # Find the profile with the most fishing xp
        maxXP = 0
        mainProfileID = None
        for profileID in profileIDs:
            response = rq.get(
                BASE_PROFILE_URL, params={"key": KEY, "profile": profileID}
            )

            # If succesful
            if response.status_code == 200:
                currXP = response.json()["profile"]["members"][uuid].get(
                    "experience_skill_fishing", 0
                )
                print(f"\t[{profiles[profileID]['cute_name']}]: {currXP} Fishing XP")

                # Record and keep track of the best profile
                if currXP > maxXP:
                    mainProfileID = profileID
                    maxXP = currXP

            else:
                print(f"\t[{profiles[profileID]['cute_name']}]: API Fetch Failed")
                errors += [username]

                if response.status_code == 429:
                    server = response.headers.get("API-Server", None)
                    delay = response.headers.get(
                        "retry-after", response.headers.get("RateLimit-Reset", 0)
                    )

                    print(
                        f"\tRatelimit Error on server {server}, waiting for {delay} seconds"
                    )
                    sleep(int(delay) + 1)

                continue

        if not mainProfileID:
            print(f"\t  Error, no main profile found for this user [{username}]")
            errors += [username]
            continue

        print(f"\t  └── {profiles[mainProfileID]['cute_name']} Profile selected")

        # Save data
        userData = {
            "username": username,
            "uuid": uuid,
            "profileID": mainProfileID,
            "cute_name": profiles[mainProfileID]["cute_name"],
        }

        # Save to mongodb
        dbRes = db["player_main_profiles"].update_one(
            {"uuid": uuid}, {"$set": userData}, upsert=True
        )

        print(dbRes.raw_result)

    print(errors)

    return data


# Load usernames
with open("playerList.json", "r") as file:
    usernames = json.load(file)


data = asyncio.run(get_main_profiles(["Ultwa"]))

# Save dict to file
with open("playerMainProfiles.json", "w") as file:
    json.dump(data, file, indent=2)
