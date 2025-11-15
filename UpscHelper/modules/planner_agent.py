# modules/planner_agent.py

def build_planner_prompt(performance):
    """
    Build prompt — but not used right now.
    Only kept for future LLM use.
    """
    prompt = "You are a UPSC mentor.\nUser Performance:\n\n"
    for subject, accuracy in performance.items():
        prompt += f"- {subject}: {accuracy}%\n"

    prompt += "\nGenerate a custom UPSC plan."
    return prompt


def parse_llm_response_to_json(performance):
    """
    Create dynamic plan based ONLY on performance sent by frontend.
    No hardcoded weak/strong subjects.
    """
    weak = []
    moderate = []
    strong = []

    for subject, acc in performance.items():
        if acc < 40:
            weak.append(subject)
        elif acc < 70:
            moderate.append(subject)
        else:
            strong.append(subject)

    # Build a 7-day plan dynamically
    seven_day_plan = []
    for w in weak:
        seven_day_plan.append(f"Day: Study basics of {w} from NCERT + practice PYQs")

    for m in moderate:
        seven_day_plan.append(f"Day: Revise {m} and solve 20 MCQs")

    for s in strong:
        seven_day_plan.append(f"Day: Just revise {s} briefly + attempt 10 MCQs")

    if not seven_day_plan:
        seven_day_plan.append("Day: Light revision of all subjects")

    # 30-day plan (dynamic)
    thirty_day_plan = []
    for w in weak:
        thirty_day_plan.append(f"Week: Improve {w} — read NCERT + Laxmikanth (if polity) + MCQs")

    for m in moderate:
        thirty_day_plan.append(f"Week: Strengthen {m} — revision + test series")

    for s in strong:
        thirty_day_plan.append(f"Week: Maintain {s} — quick revision + current affairs link")

    if not thirty_day_plan:
        thirty_day_plan.append("General revision plan for all subjects")

    return {
        "weak_subjects": weak,
        "moderate_subjects": moderate,
        "strong_subjects": strong,
        "7_day_plan": seven_day_plan,
        "30_day_plan": thirty_day_plan
    }
