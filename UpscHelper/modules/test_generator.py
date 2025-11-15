import random
from config import questions_collection

WEIGHTS = {
    "Polity": 0.25,
    "Economy": 0.25,
    "History": 0.20,
    "Geography": 0.15,
    "Environment": 0.15
}

def generate_test(subject=None, difficulty=None, num=10, pattern=None):
    # Fetch all questions from MongoDB
    questions = list(questions_collection.find({}, {"_id": 0}))

    if pattern == "upsc_mixed":
        final_questions = []
        for subj, weight in WEIGHTS.items():
            count = max(1, round(num * weight))
            pool = [q for q in questions if q["subject"].lower() == subj.lower()]
            final_questions.extend(random.sample(pool, min(len(pool), count)))
        random.shuffle(final_questions)
        return {"questions": final_questions[:num]}

    # Normal test (subject/difficulty based)
    filtered = questions
    if subject:
        filtered = [q for q in filtered if q["subject"].lower() == subject.lower()]
    if difficulty:
        filtered = [q for q in filtered if q["difficulty"].lower() == difficulty.lower()]

    return {"questions": random.sample(filtered, min(len(filtered), num))}
