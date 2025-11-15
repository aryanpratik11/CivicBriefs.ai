# app.py
# Main Flask backend for UPSC Helper
# - Serves API endpoints (/generate-test, /submit-test, /user-performance, /generate-planner)
# - Serves the frontend static files from the "frontend" directory (index.html, style.css, script.js)
# ------------------------------------------------------------------------------

from flask import Flask, request, jsonify, send_from_directory  # <-- added send_from_directory
from flask_cors import CORS
from datetime import datetime
import os

# import DB collections from config
from config import questions_collection, tests_collection, responses_collection

# business logic modules
from modules.weak_area import calculate_subject_accuracy, classify_accuracy
from modules.test_generator import generate_test
from modules.planner_agent import build_planner_prompt, parse_llm_response_to_json

# -----------------------------------------------------------------------
# CREATE FLASK APP and point static_folder to the 'frontend' directory
# -----------------------------------------------------------------------
# static_folder is where Flask looks for static files (index.html, css, js)
# static_url_path="" makes the static files available from root (/) path
app = Flask(__name__, static_folder="frontend", static_url_path="")  # <-- changed to serve frontend
CORS(app)  # enable CORS for API calls from frontend

# -----------------------------------------------------------------------
# Serve frontend: when user opens '/', return frontend/index.html
# This is the new code that connects your frontend files to the backend.
# -----------------------------------------------------------------------
@app.route("/")
def serve_frontend():
    """
    Serve the frontend index.html from the frontend directory.
    If you request '/', this sends frontend/index.html.
    """
    return send_from_directory(app.static_folder, "index.html")  # <-- new: serves index.html

# If a static asset is requested (style.css, script.js), Flask will serve it automatically
# because static_folder is set. But, to be safe, add a fallback route to serve any file.
@app.route("/<path:filename>")
def serve_static(filename):
    """
    Serve other frontend files (CSS, JS, images) from the frontend folder.
    Example: /style.css or /script.js
    """
    return send_from_directory(app.static_folder, filename)  # <-- new: serve static assets

# -----------------------------------------------------------------------
# API Endpoints (unchanged logic, just kept here for full view)
# -----------------------------------------------------------------------
@app.route("/generate-test", methods=["GET"])
def api_generate_test():
    subject = request.args.get("subject")
    difficulty = request.args.get("difficulty")
    pattern = request.args.get("pattern")
    num = int(request.args.get("num", 10))

    test_data = generate_test(subject=subject, difficulty=difficulty, num=num, pattern=pattern)
    # Optionally add a test_id here (simple timestamp id)
    test_id = "T_" + datetime.utcnow().strftime("%Y%m%d%H%M%S")
    # return test_id so frontend can send it later
    return jsonify({"test_id": test_id, **test_data})


@app.route("/submit-test", methods=["POST"])
def api_submit_test():
    data = request.json or {}
    user_id = data.get("user_id", "anonymous")
    test_id = data.get("test_id") or ("T_" + datetime.utcnow().strftime("%Y%m%d%H%M%S"))
    responses = data.get("responses", [])

    # 1) fetch correct answers from DB
    qids = [r.get("question_id") for r in responses if r.get("question_id")]
    cursor = list(questions_collection.find({"question_id": {"$in": qids}}, {"_id":0, "question_id":1, "correct_answer":1, "subject":1, "topic":1}))
    answers_map = {q["question_id"]: q for q in cursor}

    # 2) enrich and compute correctness
    enriched = []
    for r in responses:
        qid = r.get("question_id")
        user_ans = r.get("user_answer")
        qdoc = answers_map.get(qid)
        correct_ans = qdoc.get("correct_answer") if qdoc else None
        subj = qdoc.get("subject") if qdoc else r.get("subject", "Unknown")
        topic = qdoc.get("topic") if qdoc else r.get("topic", "Unknown")
        is_correct = (user_ans == correct_ans)
        enriched.append({
            "test_id": test_id,
            "user_id": user_id,
            "question_id": qid,
            "user_answer": user_ans,
            "correct_answer": correct_ans,
            "correct": is_correct,
            "subject": subj,
            "topic": topic,
            "time_taken": r.get("time_taken"),
            "ts": datetime.utcnow()
        })

    # 3) save to DB
    if enriched:
        try:
            responses_collection.insert_many(enriched)
        except Exception as e:
            print("Insert responses error:", e)

    total = len(enriched)
    correct_count = sum(1 for e in enriched if e["correct"])
    score_percent = round((correct_count/total)*100, 2) if total else 0.0

    test_doc = {
        "test_id": test_id,
        "user_id": user_id,
        "total_questions": total,
        "correct_count": correct_count,
        "score_percent": score_percent,
        "ts": datetime.utcnow()
    }
    try:
        tests_collection.insert_one(test_doc)
    except Exception as e:
        print("Insert test summary error:", e)

    # 4) compute subject accuracy
    responses_for_calc = [{"subject": e["subject"], "correct": e["correct"]} for e in enriched]
    accuracy = calculate_subject_accuracy(responses_for_calc)
    classification = {s: classify_accuracy(v) for s, v in accuracy.items()}

    return jsonify({
        "status": "ok",
        "test_id": test_id,
        "score_percent": score_percent,
        "accuracy": accuracy,
        "classification": classification
    })


@app.route("/user-performance/<user_id>", methods=["GET"])
def user_performance(user_id):
    pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {
            "_id": "$subject",
            "attempted": {"$sum": 1},
            "correct": {"$sum": {"$cond": ["$correct", 1, 0]}}
        }},
        {"$project": {
            "subject": "$_id",
            "attempted": 1,
            "correct": 1,
            "accuracy": {"$cond": [{"$eq":["$attempted",0]}, 0, {"$multiply":[{"$divide":["$correct","$attempted"]},100]}]}
        }}
    ]
    res = list(responses_collection.aggregate(pipeline))
    perf = {r["subject"]: round(r["accuracy"],2) for r in res}
    return jsonify({"user_id": user_id, "performance": perf})

@app.route("/performance-by-test/<test_id>", methods=["GET"])
def performance_by_test(test_id):
    """
    Returns subject-wise accuracy ONLY for the given test.
    """
    pipeline = [
        {"$match": {"test_id": test_id}},
        {"$group": {
            "_id": "$subject",
            "attempted": {"$sum": 1},
            "correct": {"$sum": {"$cond": ["$correct", 1, 0]}}
        }},
        {"$project": {
            "subject": "$_id",
            "accuracy": {
                "$cond": [
                    {"$eq": ["$attempted", 0]},
                    0,
                    {"$multiply": [{"$divide": ["$correct", "$attempted"]}, 100]}
                ]
            }
        }}
    ]

    res = list(responses_collection.aggregate(pipeline))
    performance = {r["subject"]: round(r["accuracy"], 2) for r in res}

    return jsonify({"test_id": test_id, "performance": performance})



@app.route("/get-test-summary/<test_id>")
def get_test_summary(test_id):
    doc = tests_collection.find_one({"test_id": test_id}, {"_id":0})
    if not doc:
        return jsonify({"error": "Test not found"}), 404
    return jsonify(doc)
    
@app.route("/generate-planner", methods=["POST"])
def api_generate_planner():
    data = request.json or {}
    performance = data.get("performance", {})
    prompt = build_planner_prompt(performance)
    plan = parse_llm_response_to_json(performance)
    return jsonify({"prompt": prompt, "plan": plan})


if __name__ == "__main__":
    # Run dev server
    # If you want to expose externally for testing on other devices, change host to '0.0.0.0'
    app.run(debug=True)
