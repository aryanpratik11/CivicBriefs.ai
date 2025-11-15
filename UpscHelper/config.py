from pymongo import MongoClient

MONGO_URI = "mongodb+srv://Deepak:Deepaksharma@upscplanner.puz4hgv.mongodb.net/?appName=UpscPlanner"

client = MongoClient(MONGO_URI)
db = client["upsc_helper"]

# Collections
questions_collection = db["questions"]
tests_collection = db["tests"]
responses_collection = db["responses"]
