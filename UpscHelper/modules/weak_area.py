# modules/weak_area.py
from collections import defaultdict

def calculate_subject_accuracy(responses):
    """
    responses = [
        { "subject": "Polity", "correct": True },
        { "subject": "Polity", "correct": False },
        { "subject": "Environment", "correct": True },
        ...
    ]
    """
    stats = defaultdict(lambda: {"correct": 0, "attempted": 0})

    # Count total correct & attempted
    for r in responses:
        subj = r["subject"]
        stats[subj]["attempted"] += 1
        if r["correct"]:
            stats[subj]["correct"] += 1

    # Calculate accuracy per subject
    accuracy = {}
    for subj, values in stats.items():
        attempted = values["attempted"]
        correct = values["correct"]

        accuracy[subj] = round((correct / attempted) * 100, 2) if attempted > 0 else 0

    return accuracy


def classify_accuracy(acc):
    """
    Convert accuracy % into a label.
    """
    if acc < 40:  return "Critical Weak"
    if acc < 60:  return "Weak"
    if acc < 75:  return "Average"
    if acc < 90:  return "Strong"
    return "Excellent"
