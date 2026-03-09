"""
Social Work Education Platform — Backend API
Supports: static scenarios, Claude API integration, cost tracking, image upload, simulation mode
"""
import os
import json
import time
import uuid
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder="/app/frontend", static_url_path="")
CORS(app)

# ── Configuration ────────────────────────────────────────────────────
CLAUDE_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-20250514")
SIMULATION_MODE = os.environ.get("SIMULATION_MODE", "true").lower() == "true"
UPLOAD_FOLDER = "/app/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "pdf"}
DATA_DIR = "/app/data"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ── In-memory stores ────────────────────────────────────────────────
cost_ledger = []          # [{id, timestamp, action, model, input_tokens, output_tokens, cost_usd}]
session_store = {}        # session_id -> {history, scenario_id, started_at, ...}

# ── Cost constants (per 1M tokens, USD) ─────────────────────────────
PRICING = {
    "claude-sonnet-4-20250514":  {"input": 3.00,  "output": 15.00},
    "claude-opus-4-20250514":    {"input": 15.00, "output": 75.00},
    "claude-haiku-4-5-20251001": {"input": 0.80,  "output": 4.00},
}

# ── Helpers ──────────────────────────────────────────────────────────
def load_scenarios():
    with open(os.path.join(DATA_DIR, "scenarios.json")) as f:
        return json.load(f)

def calc_cost(model, input_tokens, output_tokens):
    p = PRICING.get(model, PRICING["claude-sonnet-4-20250514"])
    return round((input_tokens * p["input"] + output_tokens * p["output"]) / 1_000_000, 6)

def record_cost(action, model, input_tokens, output_tokens):
    cost = calc_cost(model, input_tokens, output_tokens)
    entry = {
        "id": str(uuid.uuid4())[:8],
        "timestamp": datetime.utcnow().isoformat(),
        "action": action,
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": cost,
    }
    cost_ledger.append(entry)
    return entry

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def simulate_claude_response(action, prompt, scenario=None):
    """Return a realistic mock response when in simulation mode."""
    time.sleep(0.3)  # Simulate latency

    mock_input_tokens = len(prompt.split()) * 2
    mock_output_tokens = 450

    if action == "evaluate_writing":
        response_text = (
            "## Writing Evaluation (Simulation Mode)\n\n"
            "**Overall Score: 78/100**\n\n"
            "### Strengths\n"
            "- You demonstrated a solid understanding of the ethical principles involved.\n"
            "- Good use of the NASW Code of Ethics to support your reasoning.\n"
            "- Your proposed action plan is practical and client-centered.\n\n"
            "### Areas for Improvement\n"
            "- Consider expanding your analysis of the competing ethical obligations.\n"
            "- Include more specific references to relevant theories (e.g., Kantian ethics vs. utilitarianism).\n"
            "- Your documentation section could benefit from more concrete examples of boundary-setting language.\n\n"
            "### Exam Tip\n"
            "On the ASWB exam, when faced with ethical dilemmas, always look for the answer that prioritizes client safety while maintaining professional boundaries. "
            "The 'best' answer is usually the one that involves consultation and follows agency protocol.\n\n"
            "### Key Points You Addressed Well\n"
            "- Identification of the ethical dilemma ✓\n"
            "- Reference to relevant NASW sections ✓\n"
            "- Client self-determination ✓\n\n"
            "### Key Points to Add\n"
            "- Discuss the role of supervision in managing the situation\n"
            "- Address how cultural factors might influence your approach\n"
            "- Include a plan for ongoing boundary monitoring\n"
        )
    elif action == "generate_feedback":
        response_text = (
            "## Detailed Feedback (Simulation Mode)\n\n"
            "Your writing shows a developing understanding of social work documentation standards. "
            "Here are specific suggestions for strengthening your response:\n\n"
            "**Structure:** Your response follows a logical progression. Consider using the framework taught in your program "
            "(e.g., problem identification → analysis → plan) more explicitly.\n\n"
            "**Professional Language:** Good use of clinical terminology. Remember to avoid colloquial expressions in formal documentation.\n\n"
            "**Critical Thinking:** You've identified the surface-level issues well. Push yourself to explore the underlying systemic factors "
            "that contribute to the client's situation.\n\n"
            "**Exam Relevance:** This type of scenario commonly appears on the ASWB exam. Practice identifying the 'best' answer among "
            "several 'good' answers — the key differentiator is usually the answer that is most comprehensive AND prioritizes safety.\n"
        )
    elif action == "practice_question":
        response_text = (
            "## Practice Exam Question (Simulation Mode)\n\n"
            "**Question:** A social worker at a community mental health center discovers that a client's insurance has been "
            "terminated. The client is in the middle of trauma-focused therapy and is making significant progress. "
            "The client cannot afford to pay out-of-pocket. What should the social worker do FIRST?\n\n"
            "A) Terminate services immediately as required by agency policy\n"
            "B) Continue providing services pro bono indefinitely\n"
            "C) Discuss the situation with the client and explore all available options\n"
            "D) Refer the client to a free clinic without further discussion\n\n"
            "**Correct Answer: C**\n\n"
            "**Rationale:** The NASW Code of Ethics (Section 1.16) requires that termination be handled with care and that "
            "the client's needs are prioritized. The first step is always to discuss the situation openly with the client "
            "and explore options together, which may include sliding scale fees, payment plans, insurance advocacy, "
            "referral to other agencies, or pro bono arrangements. Options A and D fail to involve the client in the decision. "
            "Option B, while generous, may not be sustainable and doesn't address the systemic issue.\n"
        )
    else:
        response_text = (
            "## AI Response (Simulation Mode)\n\n"
            "This is a simulated response. In production mode with a valid API key, "
            "Claude would provide personalized, detailed feedback on your writing, "
            "evaluate your responses against professional rubrics, and generate "
            "practice questions tailored to your learning level.\n\n"
            "**To enable live AI features:**\n"
            "1. Set your ANTHROPIC_API_KEY in the .env file\n"
            "2. Set SIMULATION_MODE=false\n"
            "3. Restart the containers\n"
        )

    cost_entry = record_cost(action + " (simulated)", CLAUDE_MODEL, mock_input_tokens, mock_output_tokens)
    return {"response": response_text, "cost": cost_entry, "simulated": True}

def call_claude(system_prompt, user_message, action="general"):
    """Call the Claude API (or simulate if in simulation mode)."""
    if SIMULATION_MODE or not CLAUDE_API_KEY:
        return simulate_claude_response(action, user_message)

    import requests
    headers = {
        "x-api-key": CLAUDE_API_KEY,
        "content-type": "application/json",
        "anthropic-version": "2023-06-01",
    }
    body = {
        "model": CLAUDE_MODEL,
        "max_tokens": 2048,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_message}],
    }
    try:
        r = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=body, timeout=60)
        r.raise_for_status()
        data = r.json()
        input_tokens = data.get("usage", {}).get("input_tokens", 0)
        output_tokens = data.get("usage", {}).get("output_tokens", 0)
        text = "\n".join(b["text"] for b in data["content"] if b["type"] == "text")
        cost_entry = record_cost(action, CLAUDE_MODEL, input_tokens, output_tokens)
        return {"response": text, "cost": cost_entry, "simulated": False}
    except Exception as e:
        return {"response": f"API Error: {str(e)}", "cost": None, "simulated": False, "error": True}


# ══════════════════════════════════════════════════════════════════════
#  ROUTES
# ══════════════════════════════════════════════════════════════════════

# ── Static frontend ──────────────────────────────────────────────────
@app.route("/")
def serve_index():
    return send_from_directory("/app/frontend", "index.html")

# ── Health / config ──────────────────────────────────────────────────
@app.route("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "simulation_mode": SIMULATION_MODE,
        "api_key_set": bool(CLAUDE_API_KEY),
        "model": CLAUDE_MODEL,
        "timestamp": datetime.utcnow().isoformat(),
    })

# ── Scenarios ────────────────────────────────────────────────────────
@app.route("/api/scenarios")
def get_scenarios():
    data = load_scenarios()
    category = request.args.get("category")
    year = request.args.get("year", type=int)
    difficulty = request.args.get("difficulty")

    scenarios = data["scenarios"]
    if category:
        scenarios = [s for s in scenarios if s["category"] == category]
    if year:
        scenarios = [s for s in scenarios if s["year"] == year]
    if difficulty:
        scenarios = [s for s in scenarios if s["difficulty"] == difficulty]

    return jsonify({"scenarios": scenarios, "total": len(scenarios)})

@app.route("/api/scenarios/<scenario_id>")
def get_scenario(scenario_id):
    data = load_scenarios()
    for s in data["scenarios"]:
        if s["id"] == scenario_id:
            return jsonify(s)
    return jsonify({"error": "Scenario not found"}), 404

@app.route("/api/categories")
def get_categories():
    data = load_scenarios()
    return jsonify(data["categories"])

@app.route("/api/exam-info")
def get_exam_info():
    data = load_scenarios()
    return jsonify(data["exam_prep"])

@app.route("/api/writing-guides")
def get_writing_guides():
    data = load_scenarios()
    return jsonify(data["writing_guides"])

@app.route("/api/quick-reference")
def get_quick_reference():
    data = load_scenarios()
    return jsonify(data["quick_reference"])

# ── AI Evaluation ────────────────────────────────────────────────────
@app.route("/api/evaluate", methods=["POST"])
def evaluate_writing():
    body = request.json or {}
    scenario_id = body.get("scenario_id", "")
    student_writing = body.get("writing", "")
    year_level = body.get("year_level", 1)

    if not student_writing.strip():
        return jsonify({"error": "No writing provided"}), 400

    # Load scenario for context
    scenario_context = ""
    rubric_context = ""
    data = load_scenarios()
    for s in data["scenarios"]:
        if s["id"] == scenario_id:
            scenario_context = f"Scenario: {s['title']}\n{s['scenario']}\nPrompt: {s['writing_prompt']}"
            rubric_context = json.dumps(s.get("rubric", {}), indent=2)
            break

    system_prompt = f"""You are an experienced social work professor and licensing exam coach evaluating a {'first' if year_level == 1 else 'second'}-year social work student's written response.

Evaluate against this rubric:
{rubric_context}

Provide:
1. A numerical score for each rubric category
2. Overall score out of 100
3. Specific strengths (with quotes from their writing)
4. Areas for improvement with concrete suggestions
5. Exam tips relevant to this topic area
6. Model response key points they may have missed

Be encouraging but honest. Use professional social work terminology.
Format your response in clear Markdown sections."""

    user_msg = f"""{scenario_context}

--- STUDENT RESPONSE ---
{student_writing}
--- END RESPONSE ---

Please evaluate this response thoroughly."""

    result = call_claude(system_prompt, user_msg, action="evaluate_writing")
    return jsonify(result)

@app.route("/api/feedback", methods=["POST"])
def get_feedback():
    body = request.json or {}
    writing = body.get("writing", "")
    focus_area = body.get("focus_area", "general")
    year_level = body.get("year_level", 1)

    if not writing.strip():
        return jsonify({"error": "No writing provided"}), 400

    system_prompt = f"""You are a social work writing coach for {'first' if year_level == 1 else 'second'}-year students.
Focus area: {focus_area}
Provide detailed, constructive feedback on the student's writing.
Address: structure, professional language, critical thinking, theoretical grounding, and exam readiness.
Be specific with examples and suggestions. Format in Markdown."""

    result = call_claude(system_prompt, writing, action="generate_feedback")
    return jsonify(result)

@app.route("/api/practice-question", methods=["POST"])
def practice_question():
    body = request.json or {}
    category = body.get("category", "ethics")
    difficulty = body.get("difficulty", "intermediate")
    year_level = body.get("year_level", 1)
    exam_type = body.get("exam_type", "aswb_bachelors")

    system_prompt = f"""You are an ASWB exam prep tutor. Generate a practice multiple-choice question for the {exam_type.replace('_', ' ').upper()} exam.

Category: {category}
Difficulty: {difficulty}
Student level: Year {year_level}

Provide:
1. A realistic exam-style question with a brief scenario
2. Four answer choices (A-D)
3. The correct answer
4. Detailed rationale explaining why the correct answer is best AND why each incorrect answer is wrong
5. The relevant NASW Code of Ethics section or theory
6. A study tip for this topic area

Format in clear Markdown."""

    result = call_claude(system_prompt, f"Generate a {difficulty} {category} question", action="practice_question")
    return jsonify(result)

# ── Cost tracking ────────────────────────────────────────────────────
@app.route("/api/costs")
def get_costs():
    total = sum(e["cost_usd"] for e in cost_ledger)
    return jsonify({
        "entries": cost_ledger[-50:],  # last 50
        "total_cost_usd": round(total, 6),
        "total_requests": len(cost_ledger),
        "simulation_mode": SIMULATION_MODE,
    })

@app.route("/api/costs/reset", methods=["POST"])
def reset_costs():
    cost_ledger.clear()
    return jsonify({"status": "reset", "total_cost_usd": 0})

# ── Image upload ─────────────────────────────────────────────────────
@app.route("/api/upload", methods=["POST"])
def upload_image():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No filename"}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": f"File type not allowed. Allowed: {ALLOWED_EXTENSIONS}"}), 400

    filename = secure_filename(f"{uuid.uuid4().hex[:8]}_{file.filename}")
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    return jsonify({
        "filename": filename,
        "path": filepath,
        "url": f"/api/uploads/{filename}",
        "message": "File uploaded successfully. In production, this would be stored in cloud storage (S3, GCS, etc.).",
        "cloud_ready": True,
    })

@app.route("/api/uploads/<filename>")
def serve_upload(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# ── Simulation mode toggle ───────────────────────────────────────────
@app.route("/api/simulation", methods=["GET"])
def get_simulation_status():
    return jsonify({"simulation_mode": SIMULATION_MODE})

@app.route("/api/simulation/toggle", methods=["POST"])
def toggle_simulation():
    global SIMULATION_MODE
    SIMULATION_MODE = not SIMULATION_MODE
    return jsonify({"simulation_mode": SIMULATION_MODE})


# ══════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
