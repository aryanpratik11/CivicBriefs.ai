import json
from config import questions_collection

with open("questions.json", "r") as f:
    data = json.load(f)

questions_collection.insert_many(data)
print("Uploaded questions successfully!")
