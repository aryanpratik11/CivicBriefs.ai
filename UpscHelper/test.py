from pymongo import MongoClient

client = MongoClient("mongodb+srv://Deepak:Deepaksharma@upscplanner.puz4hgv.mongodb.net/?appName=UpscPlanner")

try:
    db = client["test_db"]
    db.test.insert_one({"check": "ok"})
    print("MongoDB Connected!")
except Exception as e:
    print("Error:", e)
