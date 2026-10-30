"""flask_app.py 
AI-Powered Medical Intake & Escalation Workflow (Flask Edition)

Production-ready Flask application for healthcare automation demonstration.
Run locally: python flask_app.py
Deploy with Gunicorn: gunicorn flask_app:app
"""

from __future__ import annotations
import csv
import io
import json
import os
from datetime import datetime
from flask import Flask, request, render_template_string, redirect, url_for, Response, jsonify

from triage_engine import (
    init_db,
    seed_sample_records,
    get_all_submissions,
    get_submission_by_id,
    validate_intake_form,
    analyze_intake_message,
    route_submission,
    generate_simulated_notifications,
    save_submission,
    update_review_status,
    ROUTE_PRIORITY,
    ROUTE_ROUTINE,
    ROUTE_GENERAL
)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "medical-intake-secret-key-2026")

# Initialize SQLite database and seed records
init_db()
if not get_all_submissions():
    seed_sample_records()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Medical Intake & Escalation Workflow</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Plus Jakarta Sans', system-ui, sans-serif; }
        .font-mono { font-family: 'JetBrains Mono', monospace; }
    </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen antialiased flex flex-col">
    <!-- Navbar -->
    <header class="bg-slate-900/90 border-b border-slate-800 sticky top-0 z-50 backdrop-blur">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <div class="flex items-center space-x-3">
                <div class="w-10 h-10 rounded-xl bg-teal-600 flex items-center justify-center text-white shadow-md font-bold text-xl">
                    🩺
                </div>
                <div>
                    <a href="/" class="font-bold text-lg text-white tracking-tight hover:text-teal-400 transition">Roobi Health Intake</a>
            
                </div>
            </div>
            <div class="flex items-center space-x-4 text-sm font-medium">
                <a href="#intake" class="text-slate-300 hover:text-white px-3 py-1.5 rounded-lg hover:bg-slate-800 transition">Intake Portal</a>
                <a href="#dashboard" class="text-slate-300 hover:text-white px-3 py-1.5 rounded-lg hover:bg-slate-800 transition">Triage Dashboard</a>
                <a href="/export/csv" class="bg-slate-800 hover:bg-slate-700 text-teal-300 border border-teal-500/30 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition">Export CSV</a>
            </div>
        </div>
    </header>

    <!-- Main Container -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1 w-full space-y-8">
        
        <!-- Safety Banner -->
        <div class="bg-amber-500/10 border border-amber-500/30 rounded-2xl p-5 text-amber-200 text-sm leading-relaxed shadow-lg">
            <div class="flex items-start gap-3">
                <span class="text-2xl">⚠️</span>
                <div>
                    <strong class="font-semibold text-amber-100 uppercase tracking-wide">Demonstration & Clinical Safety Invariant:</strong>
                    This application is an educational software prototype developed for the <strong>Health Project</strong>.
                    All patient records and clinical scenarios are <strong>strictly fictional</strong>. The system <strong>does not diagnose or provide clinical advice</strong>, and <strong>never treats the absence of emergency keywords as medical clearance</strong>. In an actual medical emergency, call 911 or visit the nearest emergency room immediately.
                </div>
            </div>
        </div>

        <!-- Metric Cards -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div class="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-sm">
                <div class="text-xs uppercase tracking-wider font-semibold text-slate-400">Total Cases</div>
                <div class="text-3xl font-bold text-white mt-1">{{ total_count }}</div>
                <div class="text-xs text-slate-500 mt-1">Processed intakes</div>
            </div>
            <div class="bg-red-950/40 border border-red-500/30 rounded-2xl p-5 shadow-sm">
                <div class="text-xs uppercase tracking-wider font-semibold text-red-400">🚨 Priority Review</div>
                <div class="text-3xl font-bold text-red-200 mt-1">{{ priority_count }}</div>
                <div class="text-xs text-red-400/80 mt-1">Requires urgent provider action</div>
            </div>
            <div class="bg-emerald-950/40 border border-emerald-500/30 rounded-2xl p-5 shadow-sm">
                <div class="text-xs uppercase tracking-wider font-semibold text-emerald-400">📅 Routine Bookings</div>
                <div class="text-3xl font-bold text-emerald-200 mt-1">{{ routine_count }}</div>
                <div class="text-xs text-emerald-400/80 mt-1">Standard clinical queue</div>
            </div>
            <div class="bg-amber-950/40 border border-amber-500/30 rounded-2xl p-5 shadow-sm">
                <div class="text-xs uppercase tracking-wider font-semibold text-amber-400">📋 General Review</div>
                <div class="text-3xl font-bold text-amber-200 mt-1">{{ general_count }}</div>
                <div class="text-xs text-amber-400/80 mt-1">Ambiguous / admin inquiries</div>
            </div>
        </div>

        {% if success_submission %}
        <!-- Recent Triage Result Banner -->
        <div class="bg-slate-900 border-2 {% if success_submission.route_destination == 'Priority Human Review' %}border-red-500/80 bg-red-950/20{% elif success_submission.route_destination == 'Routine Appointments' %}border-emerald-500/80 bg-emerald-950/20{% else %}border-amber-500/80 bg-amber-950/20{% endif %} rounded-2xl p-6 shadow-xl space-y-4">
            <div class="flex items-center justify-between flex-wrap gap-4">
                <div class="flex items-center gap-3">
                    <span class="text-3xl">
                        {% if success_submission.route_destination == 'Priority Human Review' %}🚨{% elif success_submission.route_destination == 'Routine Appointments' %}✅{% else %}📋{% endif %}
                    </span>
                    <div>
                        <h2 class="text-xl font-bold text-white">Intake Triage Completed: Case #{{ success_submission.id }}</h2>
                        <p class="text-sm text-slate-300">Patient: <strong class="text-white">{{ success_submission.patient_name }}</strong> (DOB: {{ success_submission.dob }})</p>
                    </div>
                </div>
                <div class="flex items-center gap-2">
                    <span class="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider {% if success_submission.route_destination == 'Priority Human Review' %}bg-red-500/20 text-red-300 border border-red-500/40{% elif success_submission.route_destination == 'Routine Appointments' %}bg-emerald-500/20 text-emerald-300 border border-emerald-500/40{% else %}bg-amber-500/20 text-amber-300 border border-amber-500/40{% endif %}">
                        {{ success_submission.route_destination }}
                    </span>
                    <span class="px-3 py-1 rounded-full text-xs font-semibold bg-slate-800 text-slate-300">
                        Risk Score: {{ success_submission.risk_score }}/100
                    </span>
                </div>
            </div>

            <div class="bg-slate-950/80 p-4 rounded-xl border border-slate-800">
                <div class="text-xs uppercase tracking-wider font-semibold text-slate-400 mb-1">Clinical Routing Rationale</div>
                <div class="text-sm text-slate-200">{{ success_submission.route_rationale }}</div>
                <div class="text-xs uppercase tracking-wider font-semibold text-slate-400 mt-3 mb-1">Provider SBAR Summary</div>
                <div class="text-sm text-slate-300 font-mono bg-slate-900 p-3 rounded-lg border border-slate-800">{{ success_submission.ai_summary }}</div>
            </div>

            <!-- Simulated Alerts -->
            <div class="text-xs uppercase tracking-wider font-semibold text-slate-400">Automated Simulated Provider Escalations</div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="bg-slate-950 p-4 rounded-xl border border-slate-800 text-xs font-mono space-y-1">
                    <div class="text-teal-400 font-semibold uppercase">📧 Provider Clinical Email Notification</div>
                    <div class="text-slate-400">Subject: {{ success_submission.notifications.email.subject }}</div>
                    <div class="text-slate-300 mt-2 whitespace-pre-wrap">{{ success_submission.notifications.email.body }}</div>
                </div>
                <div class="bg-slate-950 p-4 rounded-xl border border-slate-800 text-xs font-mono space-y-1">
                    <div class="text-teal-400 font-semibold uppercase">💬 On-Call Emergency Escalation (Slack / SMS)</div>
                    <div class="text-slate-400">Channel: #emergency-triage-desk</div>
                    <div class="text-slate-300 mt-2 whitespace-pre-wrap">{{ success_submission.notifications.slack.message }}</div>
                </div>
            </div>
        </div>
        {% endif %}

        <div class="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            <!-- Left Column: Patient Intake Form -->
            <div id="intake" class="lg:col-span-5 bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-5">
                <div>
                    <h2 class="text-xl font-bold text-white flex items-center gap-2">
                        <span>📝</span> Patient Medical Intake Form
                    </h2>
                    <p class="text-xs text-slate-400 mt-1">Submit patient details for safety-first algorithmic triage routing.</p>
                </div>

                {% if error_msg %}
                <div class="bg-red-950/60 border border-red-500/40 text-red-200 p-3.5 rounded-xl text-sm">
                    <strong>Validation Error:</strong> {{ error_msg }}
                </div>
                {% endif %}

                <form action="/submit" method="POST" class="space-y-4">
                    <div>
                        <label class="block text-xs uppercase font-semibold text-slate-400 mb-1">Full Legal Name *</label>
                        <input type="text" name="patient_name" required placeholder="e.g. Jordan Miller" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-teal-500 transition">
                    </div>

                    <div class="grid grid-cols-2 gap-3">
                        <div>
                            <label class="block text-xs uppercase font-semibold text-slate-400 mb-1">Date of Birth *</label>
                            <input type="date" name="dob" required value="1988-04-12" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2 text-sm text-white focus:outline-none focus:border-teal-500 transition">
                        </div>
                        <div>
                            <label class="block text-xs uppercase font-semibold text-slate-400 mb-1">Contact Phone</label>
                            <input type="tel" name="contact_phone" placeholder="555-0199" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2 text-sm text-white focus:outline-none focus:border-teal-500 transition">
                        </div>
                    </div>

                    <div>
                        <label class="block text-xs uppercase font-semibold text-slate-400 mb-1">Chief Complaint & Detailed Message *</label>
                        <textarea name="message" rows="4" required placeholder="Describe your symptoms, how long you have had them, and what brings you in today..." class="w-full bg-slate-950 border border-slate-800 rounded-xl p-4 text-sm text-white focus:outline-none focus:border-teal-500 transition"></textarea>
                    </div>

                    <div class="grid grid-cols-2 gap-3">
                        <div>
                            <label class="block text-xs uppercase font-semibold text-slate-400 mb-1">Symptom Duration</label>
                            <select name="duration" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-teal-500">
                                <option>Less than 1 hour</option>
                                <option>1 to 6 hours</option>
                                <option>1 to 3 days</option>
                                <option selected>3 to 7 days</option>
                                <option>More than 1 week</option>
                            </select>
                        </div>
                        <div>
                            <label class="block text-xs uppercase font-semibold text-slate-400 mb-1">Pain Severity (0-10)</label>
                            <select name="pain_scale" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-teal-500">
                                <option>0 - No pain</option>
                                <option>1 - Very mild</option>
                                <option>3 - Mild discomfort</option>
                                <option selected>5 - Moderate pain</option>
                                <option>7 - Severe pain</option>
                                <option>9 - Incapacitating</option>
                                <option>10 - Worst pain ever</option>
                            </select>
                        </div>
                    </div>

                    <div class="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2">
                        <div class="text-xs font-semibold uppercase text-slate-400 tracking-wider">Clinical Red Flag Checkbox:</div>
                        <label class="flex items-center gap-2 text-xs text-slate-300 cursor-pointer">
                            <input type="checkbox" name="red_flag_chest_pain" class="rounded bg-slate-900 border-slate-700 text-teal-500 focus:ring-0">
                            <span>Chest tightness, pressure, or radiating pain</span>
                        </label>
                        <label class="flex items-center gap-2 text-xs text-slate-300 cursor-pointer">
                            <input type="checkbox" name="red_flag_shortness_breath" class="rounded bg-slate-900 border-slate-700 text-teal-500 focus:ring-0">
                            <span>Severe difficulty breathing or gasping for air</span>
                        </label>
                        <label class="flex items-center gap-2 text-xs text-slate-300 cursor-pointer">
                            <input type="checkbox" name="red_flag_neuro" class="rounded bg-slate-900 border-slate-700 text-teal-500 focus:ring-0">
                            <span>Sudden numbness, facial droop, or speech trouble</span>
                        </label>
                    </div>

                    <button type="submit" class="w-full bg-gradient-to-r from-teal-500 to-teal-600 hover:from-teal-400 hover:to-teal-500 text-white font-bold py-3 px-4 rounded-xl shadow-lg transition transform active:scale-98">
                        ⚡ Submit for Clinical Triage
                    </button>
                </form>
            </div>

            <!-- Right Column: Live Triage Dashboard -->
            <div id="dashboard" class="lg:col-span-7 bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-5">
                <div class="flex items-center justify-between flex-wrap gap-2">
                    <div>
                        <h2 class="text-xl font-bold text-white flex items-center gap-2">
                            <span>📋</span> Clinical Triage Review Queues
                        </h2>
                        <p class="text-xs text-slate-400 mt-1">Live queue of incoming patient submissions categorized by urgency.</p>
                    </div>
                </div>

                <!-- Submissions Table -->
                <div class="overflow-x-auto">
                    <table class="w-full text-left text-sm border-collapse">
                        <thead>
                            <tr class="border-b border-slate-800 text-xs uppercase tracking-wider text-slate-400">
                                <th class="py-3 px-3">Case ID</th>
                                <th class="py-3 px-3">Patient</th>
                                <th class="py-3 px-3">Urgency Queue</th>
                                <th class="py-3 px-3">Risk</th>
                                <th class="py-3 px-3">Status</th>
                                <th class="py-3 px-3 text-right">Action</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-800/60">
                            {% for sub in submissions %}
                            <tr class="hover:bg-slate-800/40 transition">
                                <td class="py-3.5 px-3 font-mono text-xs text-slate-400">#{{ sub.id }}</td>
                                <td class="py-3.5 px-3 font-medium text-white">
                                    {{ sub.patient_name }}
                                    <span class="block text-xs text-slate-400 font-normal truncate max-w-xs">{{ sub.raw_message }}</span>
                                </td>
                                <td class="py-3.5 px-3">
                                    <span class="px-2.5 py-1 rounded-full text-xs font-semibold whitespace-nowrap {% if sub.route_destination == 'Priority Human Review' %}bg-red-500/20 text-red-300 border border-red-500/40{% elif sub.route_destination == 'Routine Appointments' %}bg-emerald-500/20 text-emerald-300 border border-emerald-500/40{% else %}bg-amber-500/20 text-amber-300 border border-amber-500/40{% endif %}">
                                        {{ sub.route_destination }}
                                    </span>
                                </td>
                                <td class="py-3.5 px-3 font-mono text-xs text-slate-300">{{ sub.risk_score }}/100</td>
                                <td class="py-3.5 px-3">
                                    <span class="text-xs px-2 py-0.5 rounded {% if sub.reviewed_by_human %}bg-teal-500/20 text-teal-300{% else %}bg-slate-800 text-slate-400{% endif %}">
                                        {{ 'Reviewed' if sub.reviewed_by_human else 'Pending' }}
                                    </span>
                                </td>
                                <td class="py-3.5 px-3 text-right">
                                    <form action="/review/{{ sub.id }}" method="POST" class="inline">
                                        <button type="submit" class="text-xs font-semibold text-teal-400 hover:text-teal-300 underline">
                                            {{ 'Mark Pending' if sub.reviewed_by_human else 'Mark Reviewed' }}
                                        </button>
                                    </form>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </main>

    <!-- Footer -->
    <footer class="bg-slate-900 border-t border-slate-800 py-6 text-center text-xs text-slate-400">
        <p>Roobi Health Intake Workflow Prototype · Author: Roobika (@Roobika06)</p>
        <p class="mt-1 text-slate-500">Repository: <a href="https://github.com/Roobika06/ai-medical-intake-workflow" target="_blank" class="text-teal-400 hover:underline">Roobika06/ai-medical-intake-workflow</a></p>
    </footer>
</body>
</html>
"""

@app.route("/")
def index():
    all_subs = get_all_submissions()
    total_count = len(all_subs)
    priority_count = sum(1 for s in all_subs if s["route_destination"] == ROUTE_PRIORITY)
    routine_count = sum(1 for s in all_subs if s["route_destination"] == ROUTE_ROUTINE)
    general_count = sum(1 for s in all_subs if s["route_destination"] == ROUTE_GENERAL)
    return render_template_string(
        HTML_TEMPLATE,
        submissions=all_subs,
        total_count=total_count,
        priority_count=priority_count,
        routine_count=routine_count,
        general_count=general_count,
        success_submission=None,
        error_msg=None
    )

@app.route("/submit", methods=["POST"])
def submit_intake():
    patient_name = request.form.get("patient_name", "").strip()
    dob = request.form.get("dob", "").strip()
    contact_phone = request.form.get("contact_phone", "").strip()
    message = request.form.get("message", "").strip()
    duration = request.form.get("duration", "3 to 7 days")
    pain_scale = request.form.get("pain_scale", "5 - Moderate pain")

    red_flags = []
    if request.form.get("red_flag_chest_pain"):
        red_flags.append("chest_tightness_or_radiating_pain")
    if request.form.get("red_flag_shortness_breath"):
        red_flags.append("severe_shortness_of_breath")
    if request.form.get("red_flag_neuro"):
        red_flags.append("sudden_neurological_symptoms")

    # Validate
    validation_err = validate_intake_form(patient_name, dob, message)
    if validation_err:
        all_subs = get_all_submissions()
        return render_template_string(
            HTML_TEMPLATE,
            submissions=all_subs,
            total_count=len(all_subs),
            priority_count=sum(1 for s in all_subs if s["route_destination"] == ROUTE_PRIORITY),
            routine_count=sum(1 for s in all_subs if s["route_destination"] == ROUTE_ROUTINE),
            general_count=sum(1 for s in all_subs if s["route_destination"] == ROUTE_GENERAL),
            success_submission=None,
            error_msg=validation_err
        ), 400

    # Analyze with triage engine
    analysis = analyze_intake_message(message, {
        "duration": duration,
        "pain_scale": pain_scale,
        "red_flag_checkboxes": red_flags
    })

    # Route submission
    route_dest, route_reason = route_submission(analysis)

    # Generate provider simulated alerts
    notifications = generate_simulated_notifications(
        patient_name=patient_name,
        route_dest=route_dest,
        summary=analysis["summary"],
        risk_score=analysis["risk_score"]
    )

    # Persist in SQLite
    new_sub_id = save_submission(
        patient_name=patient_name,
        dob=dob,
        contact_phone=contact_phone,
        raw_message=message,
        analysis=analysis,
        route_dest=route_dest,
        route_reason=route_reason,
        notifications=notifications
    )

    created_sub = get_submission_by_id(new_sub_id)
    all_subs = get_all_submissions()
    return render_template_string(
        HTML_TEMPLATE,
        submissions=all_subs,
        total_count=len(all_subs),
        priority_count=sum(1 for s in all_subs if s["route_destination"] == ROUTE_PRIORITY),
        routine_count=sum(1 for s in all_subs if s["route_destination"] == ROUTE_ROUTINE),
        general_count=sum(1 for s in all_subs if s["route_destination"] == ROUTE_GENERAL),
        success_submission=created_sub,
        error_msg=None
    )

@app.route("/review/<int:sub_id>", methods=["POST"])
def toggle_review(sub_id: int):
    sub = get_submission_by_id(sub_id)
    if sub:
        new_status = not sub["reviewed_by_human"]
        reviewer_name = "Dr. Reviewer (Staff Clinician)" if new_status else ""
        update_review_status(sub_id, new_status, reviewer_name)
    return redirect(url_for("index") + "#dashboard")

@app.route("/export/csv")
def export_csv():
    all_subs = get_all_submissions()
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow([
        "Submission ID", "Timestamp", "Patient Name", "DOB",
        "Route Destination", "Risk Score", "Reviewed", "Rationale", "Raw Message"
    ])
    for s in all_subs:
        cw.writerow([
            s["id"], s["created_at"], s["patient_name"], s["dob"],
            s["route_destination"], s["risk_score"],
            "Yes" if s["reviewed_by_human"] else "No",
            s["route_rationale"], s["raw_message"]
        ])
    return Response(
        si.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=medical_intake_export.csv"}
    )

@app.route("/api/submissions", methods=["GET"])
def api_submissions():
    return jsonify({"submissions": get_all_submissions()})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
