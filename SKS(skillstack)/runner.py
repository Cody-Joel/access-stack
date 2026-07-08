"""
skillforge/runner.py — Measure skill retention with vs without AI assistance.

WHAT THIS DOES:
  Presents coding tasks to the user in two conditions:
    - AI-assisted: Claude is available to help
    - Solo: No AI, just documentation links
  After each task, a short quiz measures conceptual retention.
  Results reveal whether AI assistance trades speed for understanding.

HYPOTHESIS:
  Users who complete tasks with AI assistance will score lower on conceptual
  quiz questions (debugging, code-reading) than users who completed the same
  tasks without AI assistance — replicating the Shen & Tamkin (2026) finding.

INSPIRED BY:
  "How AI Impacts Skill Formation" — Judy Hanwen Shen & Alex Tamkin (2026)
  Anthropic research output. RCT with 52 software engineers.

NOTE:
  In demo mode, this runs a 3-question mini-session so you can see the
  structure without a full experiment. Full experiments take ~25 minutes.
"""

import json
import os
import time
import datetime
import random
from pathlib import Path


# ── Tasks ──────────────────────────────────────────────────────────────────────

TASKS = [
    {
        "id": "task_async_001",
        "topic": "Python asyncio basics",
        "description": """
Write an async function called `fetch_data` that:
1. Takes a URL string as input
2. Simulates a network delay using asyncio.sleep(0.1)
3. Returns a dict with keys 'url' and 'status' (always 200 for this simulation)

Then write a main() function that runs fetch_data for three different URLs concurrently.
""".strip(),
        "docs_link": "https://docs.python.org/3/library/asyncio.html",
        "quiz": [
            {
                "type": "conceptual",
                "question": "What is the difference between asyncio.sleep() and time.sleep() in an async context?",
                "correct_keywords": ["blocks", "yields", "event loop", "non-blocking", "cooperative"]
            },
            {
                "type": "debugging",
                "question": "This code has a bug — what is wrong?\n\nasync def main():\n    result = fetch_data('http://example.com')\n    print(result)",
                "correct_keywords": ["await", "missing await", "coroutine", "not awaited"]
            },
            {
                "type": "code_reading",
                "question": "What does asyncio.gather() do when one of the coroutines raises an exception?",
                "correct_keywords": ["cancels", "raises", "exception", "propagates", "other tasks"]
            }
        ]
    },
    {
        "id": "task_decorator_001",
        "topic": "Python decorators",
        "description": """
Write a decorator called `retry` that:
1. Takes a parameter `max_attempts` (default 3)
2. Re-runs the decorated function if it raises an exception
3. Raises the original exception after max_attempts
4. Prints which attempt number is running

Apply it to a function that randomly fails 70% of the time.
""".strip(),
        "docs_link": "https://peps.python.org/pep-0318/",
        "quiz": [
            {
                "type": "conceptual",
                "question": "Why do decorators that accept arguments need an extra layer of nesting (a function that returns a function that returns a function)?",
                "correct_keywords": ["closure", "wrapper", "arguments", "called", "returns decorator"]
            },
            {
                "type": "debugging",
                "question": "After applying @retry, calling help(my_function) shows the docstring of 'wrapper' instead of 'my_function'. How do you fix this?",
                "correct_keywords": ["functools.wraps", "wraps", "__wrapped__", "functools"]
            },
            {
                "type": "code_reading",
                "question": "What does @retry(max_attempts=3) mean at the Python interpreter level — what is actually happening when Python processes this decorator syntax?",
                "correct_keywords": ["called first", "returns", "applied to", "callable", "evaluated"]
            }
        ]
    }
]


# ── Claude helper ──────────────────────────────────────────────────────────────

def get_claude_help(task_description: str, user_question: str) -> str:
    """Provide AI assistance for the current task."""
    try:
        import anthropic
    except ImportError:
        return "anthropic package not installed — pip install anthropic"

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return "ANTHROPIC_API_KEY not set"

    client = anthropic.Anthropic(api_key=api_key)
    system = f"""You are a helpful coding tutor. The user is learning the following Python task:

{task_description}

Help them understand — but use the Socratic method. Ask guiding questions rather than 
giving complete solutions directly. Explain concepts clearly when asked."""

    try:
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=600,
            system=system,
            messages=[{"role": "user", "content": user_question}]
        )
        return msg.content[0].text
    except Exception as e:
        return f"Error: {e}"


# ── Quiz scoring ───────────────────────────────────────────────────────────────

def score_answer(answer: str, correct_keywords: list) -> tuple[float, list]:
    """Score an answer by keyword matching. Returns (score 0-1, matched keywords)."""
    answer_lower = answer.lower()
    matched = [kw for kw in correct_keywords if kw.lower() in answer_lower]
    score = len(matched) / len(correct_keywords)
    return score, matched


# ── Experiment runner ──────────────────────────────────────────────────────────

def run_experiment(demo: bool = False, ai_assisted: bool = True):
    """Run a full experiment session. Returns results dict."""
    tasks = TASKS[:1] if demo else TASKS
    condition = "ai_assisted" if ai_assisted else "solo"
    
    print(f"\n{'='*60}")
    print(f"SkillForge — Condition: {condition.upper()}")
    print(f"Tasks: {len(tasks)} | Demo: {demo}")
    print(f"{'='*60}\n")
    
    session_results = {
        "condition": condition,
        "demo": demo,
        "timestamp": datetime.datetime.now().isoformat(),
        "tasks": []
    }

    for task in tasks:
        print(f"\n[TASK: {task['topic']}]")
        print("-" * 40)
        print(task["description"])
        print()

        if ai_assisted:
            print("Claude is available. Type your question, or 'done' when finished.")
            print(f"(Docs also available: {task['docs_link']})\n")
        else:
            print(f"Docs: {task['docs_link']}")
            print("No AI assistance in this condition. Press Enter when you've completed the task.\n")

        task_start = time.time()
        ai_interactions = []

        if ai_assisted:
            while True:
                user_input = input("Your question (or 'done'): ").strip()
                if user_input.lower() in ["done", "exit", "q"]:
                    break
                if user_input:
                    response = get_claude_help(task["description"], user_input)
                    print(f"\nClaude: {response}\n")
                    ai_interactions.append({"question": user_input, "response": response})
        else:
            input("Press Enter when you've completed the task...")

        task_time = time.time() - task_start

        # Quiz
        print(f"\n[QUIZ — {task['topic']}]")
        print("Answer these questions about the task you just completed.\n")

        quiz_results = []
        quiz_questions = task["quiz"][:2] if demo else task["quiz"]

        for i, q in enumerate(quiz_questions, 1):
            print(f"Q{i} [{q['type']}]: {q['question']}")
            answer = input("Your answer: ").strip()
            score, matched = score_answer(answer, q["correct_keywords"])
            print(f"  → Score: {score:.0%} (keywords matched: {matched or 'none'})\n")
            quiz_results.append({
                "type": q["type"],
                "question": q["question"],
                "answer": answer,
                "score": score,
                "matched_keywords": matched
            })

        avg_quiz_score = sum(r["score"] for r in quiz_results) / len(quiz_results)

        task_result = {
            "task_id": task["id"],
            "topic": task["topic"],
            "completion_time_seconds": round(task_time, 1),
            "ai_interactions": len(ai_interactions),
            "ai_interaction_log": ai_interactions,
            "quiz_results": quiz_results,
            "avg_quiz_score": round(avg_quiz_score, 3)
        }
        session_results["tasks"].append(task_result)

        print(f"Task complete — Quiz score: {avg_quiz_score:.0%} | Time: {task_time:.0f}s")

    overall_score = sum(t["avg_quiz_score"] for t in session_results["tasks"]) / len(session_results["tasks"])
    session_results["overall_quiz_score"] = round(overall_score, 3)

    print(f"\n{'='*60}")
    print(f"SESSION COMPLETE")
    print(f"Overall quiz score: {overall_score:.0%}")
    print(f"Condition: {condition}")
    print(f"{'='*60}\n")

    return session_results


def run_skillforge(args):
    """Main entry point called from main.py."""
    demo = getattr(args, "demo", False)

    if args.analyze:
        results_dir = Path("skillforge/results")
        files = list(results_dir.glob("*.json"))
        if not files:
            print("No results found. Run an experiment first.")
            return
        
        all_results = []
        for f in files:
            with open(f) as fp:
                all_results.append(json.load(fp))
        
        ai_scores = [r["overall_quiz_score"] for r in all_results if r["condition"] == "ai_assisted"]
        solo_scores = [r["overall_quiz_score"] for r in all_results if r["condition"] == "solo"]
        
        print(f"\nSkillForge — Analysis")
        print(f"AI-assisted sessions: {len(ai_scores)}, avg score: {sum(ai_scores)/len(ai_scores):.0%}" if ai_scores else "No AI-assisted sessions yet.")
        print(f"Solo sessions: {len(solo_scores)}, avg score: {sum(solo_scores)/len(solo_scores):.0%}" if solo_scores else "No solo sessions yet.")
        return

    # Run experiment
    # Randomly assign condition if not specified, for proper experiment design
    ai_assisted = random.random() > 0.5
    print(f"[Randomly assigned condition: {'AI-assisted' if ai_assisted else 'Solo'}]")
    
    results = run_experiment(demo=demo, ai_assisted=ai_assisted)

    output_path = Path("skillforge/results") / f"session_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Results saved to {output_path}")
    print("Run --analyze to compare across sessions.")
