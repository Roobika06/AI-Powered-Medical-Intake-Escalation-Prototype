"""
app.py - AI-Powered Medical Intake & Escalation Workflow
Educational Prototype for Healthcare Automation Assessment

Run with: streamlit run app.py
DISCLAIMER: Educational demonstration only. Fictional data only. Not clinical triage.
"""

from __future__ import annotations
import os
import streamlit as st
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Load local environment variables if available
load_dotenv()

from triage_engine import (
    validate_intake_form,
    analyze_intake_message,
    route_submission,
    generate_simulated_notifications,
    save_submission,
    get_all_submissions,
    get_submission_by_id,
    update_review_status,
    reset_database,
    seed_sample_records,
    init_db,
    ROUTE_PRIORITY,
    ROUTE_ROUTINE,
    ROUTE_GENERAL
)

# Streamlit page setup
st.set_page_config(
    page_title="Medical Intake & Escalation",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database on startup
init_db()

# Auto-seed sample records on first run if database is empty
current_records = get_all_submissions()
if not current_records:
    seed_sample_records()
    current_records = get_all_submissions()

# Custom CSS for clean healthcare UI with background image & larger comfortable typography
# Custom CSS for high-contrast, crystal-clear healthcare UI
st.markdown("""
<style>
    /* Global Base Font Size Scale & Colors */
    html, body, [class*="css"] {
        font-size: 16px;
        font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif;
    }

    /* Clean, bright, professional healthcare background */
    .stApp {
        background-color: #F8FAFC !important;
        background-image: none !important;
        color: #0F172A !important;
    }

    /* Sidebar Clean Styling */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E2E8F0 !important;
    }
    section[data-testid="stSidebar"] * {
        color: #0F172A !important;
    }

    /* Main Typography - Deep Navy/Slate for maximum readability */
    .main-header {
        font-size: 2.35rem;
        font-weight: 800;
        color: #0F172A !important;
        margin-bottom: 0.35rem;
        letter-spacing: -0.02em;
    }
    .sub-header {
        font-size: 1.15rem;
        color: #334155 !important;
        font-weight: 500;
        margin-bottom: 1.5rem;
    }
    h1, h2, h3, h4, h5, h6, .stMarkdown, p, span, label, div[data-testid="stMarkdownContainer"] p {
        color: #0F172A !important;
    }
    .stCaption, caption, p[data-testid="stCaption"] {
        color: #475569 !important;
        font-size: 0.95rem !important;
        font-weight: 500 !important;
    }

    /* Tab headers high contrast styling */
    button[data-baseweb="tab"] {
        color: #334155 !important;
        font-weight: 600 !important;
        font-size: 1.05rem !important;
        padding-top: 0.6rem !important;
        padding-bottom: 0.6rem !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #0D9488 !important;
        border-bottom: 3px solid #0D9488 !important;
        font-weight: 700 !important;
    }

    /* Metric counter cards */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF !important;
        border: 1.5px solid #E2E8F0 !important;
        border-radius: 12px !important;
        padding: 1rem 1.25rem !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
    }
    div[data-testid="stMetricValue"] {
        color: #0F172A !important;
        font-weight: 800 !important;
        font-size: 2rem !important;
    }
    div[data-testid="stMetricLabel"] {
        color: #334155 !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
    }

    /* Form Inputs & Textareas */
    div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border: 1.5px solid #CBD5E1 !important;
        border-radius: 8px !important;
        font-size: 1.05rem !important;
        font-weight: 500 !important;
    }
    div[data-baseweb="input"] input:focus, div[data-baseweb="textarea"] textarea:focus {
        border-color: #0D9488 !important;
        box-shadow: 0 0 0 2px rgba(13, 148, 136, 0.2) !important;
    }
    div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border: 1.5px solid #CBD5E1 !important;
        border-radius: 8px !important;
    }

    /* Safety banner */
    .safety-banner {
        background-color: #FFFBEB !important;
        border: 2px solid #F59E0B !important;
        padding: 1.1rem 1.4rem;
        border-radius: 12px;
        margin-bottom: 1.8rem;
        font-size: 1.02rem;
        color: #92400E !important;
        line-height: 1.55;
        box-shadow: 0 1px 3px rgba(245, 158, 11, 0.1);
    }
    .safety-banner strong {
        color: #78350F !important;
    }

    /* Triage Cards */
    .priority-card {
        background-color: #FEF2F2 !important;
        border: 2px solid #EF4444 !important;
        border-radius: 12px;
        padding: 1.3rem;
        margin-top: 1rem;
        color: #991B1B !important;
    }
    .priority-card * {
        color: #991B1B !important;
    }
    .routine-card {
        background-color: #F0FDF4 !important;
        border: 2px solid #22C55E !important;
        border-radius: 12px;
        padding: 1.3rem;
        margin-top: 1rem;
        color: #166534 !important;
    }
    .routine-card * {
        color: #166534 !important;
    }
    .general-card {
        background-color: #FFFBEB !important;
        border: 2px solid #F59E0B !important;
        border-radius: 12px;
        padding: 1.3rem;
        margin-top: 1rem;
        color: #92400E !important;
    }
    .general-card * {
        color: #92400E !important;
    }

    /* Notification Simulation Preview Boxes */
    .slack-box {
        background-color: #0F172A !important;
        color: #F8FAFC !important;
        padding: 1.3rem;
        border-radius: 12px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.95rem;
        border: 1px solid #334155 !important;
    }
    .sms-box {
        background-color: #090D16 !important;
        color: #38BDF8 !important;
        padding: 1.3rem;
        border-radius: 12px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.95rem;
        border: 1px solid #1E293B !important;
    }
    .email-box {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1.5px solid #CBD5E1 !important;
        font-size: 1.02rem;
        line-height: 1.6;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }

    /* Badges */
    .status-badge-ai {
        background-color: #DCFCE7 !important;
        color: #166534 !important;
        font-weight: 700 !important;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.85rem;
        border: 1px solid #86EFAC !important;
        display: inline-block;
    }
    .status-badge-fallback {
        background-color: #FEF3C7 !important;
        color: #92400E !important;
        font-weight: 700 !important;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.85rem;
        border: 1px solid #FCD34D !important;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# Determine active Gemini mode
api_key_env = os.environ.get("GEMINI_API_KEY", "").strip()
has_active_gemini = bool(api_key_env and api_key_env != "MY_GEMINI_API_KEY")

# Sidebar Configuration and Info
with st.sidebar:
    local_img_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public", "assets", "ai_automation_img", "woman-typing-on-laptop-office-260nw-2267871941_d4a823c3.webp")
    if os.path.exists(local_img_path):
        st.image(local_img_path, use_container_width=True)
    st.markdown("### 🩺 Workflow Control Center")
    
    if has_active_gemini:
        st.markdown('<span class="status-badge-ai">● Gemini 2.5 Flash Active</span>', unsafe_allow_html=True)
        st.caption("AI-powered summarization and intent extraction enabled.")
    else:
        st.markdown('<span class="status-badge-fallback">● Conservative Fallback Mode</span>', unsafe_allow_html=True)
        st.caption("No Gemini API key detected. Running offline rule-based safety heuristics.")
        
    st.divider()
    st.markdown("**Routing Logic Rules:**")
    st.markdown("""
    - **Queue 1 (Priority Review):** Explicit emergency requests OR concerning symptoms detected.
    - **Queue 2 (Routine Appointment):** Explicit routine requests with NO concerning content.
    - **Queue 3 (General Review):** Ambiguous, unclear, or administrative questions.
    """)
    st.info("💡 **Core Safety Principle:** The system never treats absence of emergency keywords as medical clearance.")

# Main Page Header
st.markdown('<div class="main-header">🏥 Medical Intake & Escalation</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Healthcare Automation & Safety Routing • Author: roobika (@roobika06)</div>', unsafe_allow_html=True)

# Mandatory Safety Disclaimer Banner
st.markdown("""
<div class="safety-banner">
    <strong>⚠️ DEMONSTRATION & PROTOTYPE DISCLAIMER:</strong> This application is an educational software prototype designed solely for workflow demonstration and candidate evaluation. All patient names and messages are <strong>strictly fictional</strong>. The AI and heuristic logic <strong>do not diagnose, prescribe, triage clinically, or provide medical advice</strong>. Real clinical deployments require rigorous medical validation, HIPAA compliance, and professional oversight. In an actual medical emergency, call 911 or visit the nearest emergency room immediately.
</div>
""", unsafe_allow_html=True)

# Top Metric Counters
all_records = get_all_submissions()
total_count = len(all_records)
priority_count = sum(1 for r in all_records if r["route_destination"] == ROUTE_PRIORITY)
routine_count = sum(1 for r in all_records if r["route_destination"] == ROUTE_ROUTINE)
general_count = sum(1 for r in all_records if r["route_destination"] == ROUTE_GENERAL)

col_m1, col_m2, col_m3, col_m4 = st.columns(4)
with col_m1:
    st.metric("Total Submissions", total_count)
with col_m2:
    st.metric("🚨 Priority Human Review", priority_count, delta=f"{priority_count} critical" if priority_count else None, delta_color="inverse")
with col_m3:
    st.metric("📅 Routine Appointments", routine_count)
with col_m4:
    st.metric("📋 General Human Review", general_count)

st.markdown("<br>", unsafe_allow_html=True)

# Navigation Tabs
tab_intake, tab_dashboard, tab_settings = st.tabs([
    "📝 Patient Intake Form",
    "📊 Triage Queues & Reviewer Dashboard",
    "⚙️ System Management & CSV Export"
])

# ==============================================================================
# TAB 1: PATIENT INTAKE FORM
# ==============================================================================
with tab_intake:
    st.markdown("### 📝 New Fictional Patient Intake Submission")
    st.caption("Submit a new intake message or load one of the educational test scenarios to verify escalation routing.")
    
    # Preset Scenario Selector for rapid assessment
    scenario_options = [
        "Select a pre-configured test scenario...",
        "Scenario 1: Explicit Emergency (Severe chest pain, calling 911)",
        "Scenario 2: Routine Checkup (Annual physical & bloodwork)",
        "Scenario 3: Subtle Red Flags (Facial droop & slurred speech, asks for checkup)",
        "Scenario 4: Ambiguous Request (Insurance & nutritionist inquiry)",
        "Scenario 5: Negated Emergency Keyword ('This is NOT an emergency, need inhaler refill')"
    ]
    selected_scenario = st.selectbox("⚡ Quick-load Test Scenarios (Recommended for demo):", scenario_options)
    
    preset_data = {
        "name": "",
        "contact": "",
        "symptoms": "",
        "message": ""
    }
    
    if selected_scenario.startswith("Scenario 1"):
        preset_data = {
            "name": "David Miller (Fictional)",
            "contact": "david.m.fictional@example.com | (555) 019-8822",
            "symptoms": "Severe crushing chest pain radiating to left arm and jaw, sweating heavily, cannot catch breath.",
            "message": "Please send an ambulance or call 911 immediately, I am having severe chest pain and can barely breathe!"
        }
    elif selected_scenario.startswith("Scenario 2"):
        preset_data = {
            "name": "Sophia Martinez (Fictional)",
            "contact": "sophia.m.fictional@example.com | (555) 012-3344",
            "symptoms": "No acute pain or illness. Routine annual wellness checkup requested.",
            "message": "Hi, I would like to schedule my regular annual physical exam and routine cholesterol panel for next month."
        }
    elif selected_scenario.startswith("Scenario 3"):
        preset_data = {
            "name": "Robert Evans (Fictional)",
            "contact": "robert.e.fictional@example.com | (555) 017-5511",
            "symptoms": "Sudden facial drooping on right side and mild slurred speech starting this morning.",
            "message": "Good morning. Can I get a regular appointment sometime next Tuesday? My face feels numb and I'm slurring some words."
        }
    elif selected_scenario.startswith("Scenario 4"):
        preset_data = {
            "name": "Taylor Quinn (Fictional)",
            "contact": "taylor.q.fictional@example.com | (555) 013-9900",
            "symptoms": "Occasional mild fatigue and slight seasonal allergies.",
            "message": "Do you accept Delta Dental insurance, and do you also have a nutritionist on staff at the main clinic?"
        }
    elif selected_scenario.startswith("Scenario 5"):
        preset_data = {
            "name": "Clara Oswald (Fictional)",
            "contact": "clara.o.fictional@example.com | (555) 014-2277",
            "symptoms": "Mild dry cough for 3 days, no fever, no shortness of breath.",
            "message": "This is definitely NOT an emergency at all, but I ran out of my Albuterol inhaler and need a routine prescription refill."
        }

    # Intake Form
    with st.form("patient_intake_form"):
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            form_name = st.text_input("Patient Full Name *", value=preset_data["name"], placeholder="e.g. Jane Doe (Fictional)")
        with col_f2:
            form_contact = st.text_input("Contact Details (Fictional email / phone)", value=preset_data["contact"], placeholder="e.g. jane.doe.fictional@example.com | 555-0100")
            
        form_symptoms = st.text_area(
            "Symptoms or Symptom Description *",
            value=preset_data["symptoms"],
            placeholder="Describe symptoms, duration, and severity...",
            help="Required field. Used by the AI and heuristic safety rules to evaluate potential red flags."
        )
        
        form_message = st.text_area(
            "Patient Free-Text Message *",
            value=preset_data["message"],
            placeholder="Enter the patient's full inquiry or stated request...",
            help="Required field. Evaluated for stated intent (Emergency, Routine, or Unclear) and context."
        )
        
        submit_btn = st.form_submit_button("🚀 Submit Intake for AI Analysis & Routing", use_container_width=True, type="primary")

    if submit_btn:
        # Step 1: Form Validation
        is_valid, error_msg = validate_intake_form(form_name, form_contact, form_symptoms, form_message)
        
        if not is_valid:
            st.error(f"❌ Form Validation Error: {error_msg}")
        else:
            with st.spinner("🤖 Analyzing symptoms and message context..."):
                # Step 2: AI Analysis with Fallback
                analysis = analyze_intake_message(form_symptoms, form_message)
                
                # Step 3: Deterministic Routing Rules
                route = route_submission(
                    stated_intent=analysis["stated_intent"],
                    priority_human_review=analysis["priority_human_review"],
                    is_valid_analysis=True
                )
                
                # Step 4: Save to SQLite Database
                sub_id = save_submission(
                    patient_name=form_name,
                    contact_info=form_contact,
                    symptoms=form_symptoms,
                    patient_message=form_message,
                    analysis=analysis,
                    route=route
                )
                
                # Step 5: Generate Simulated Notifications & Previews
                notifications = generate_simulated_notifications(
                    submission_id=sub_id,
                    patient_name=form_name,
                    contact_info=form_contact,
                    symptoms=form_symptoms,
                    stated_intent=analysis["stated_intent"],
                    route=route,
                    review_reason=analysis["review_reason"],
                    summary=analysis["summary"]
                )

            # Display Instant Routing Results
            st.success(f"✅ Intake submission successfully processed and logged as **{sub_id}**!")
            
            st.markdown("#### 🔍 Processing Results & Routing Decision")
            res_col1, res_col2 = st.columns([1, 1])
            
            with res_col1:
                st.markdown("**AI / Heuristic Analysis:**")
                st.markdown(f"- **Analysis Engine:** `{analysis.get('mode', 'FALLBACK')}`")
                st.markdown(f"- **Stated Intent:** `{analysis['stated_intent']}`")
                
                priority_badge = "🔴 YES (High Priority)" if analysis["priority_human_review"] else "🟢 NO (Routine/Standard)"
                st.markdown(f"- **Priority Human Review Flag:** {priority_badge}")
                st.markdown(f"- **Factual Summary:** {analysis['summary']}")
                st.markdown(f"- **Clinical Rationale:** {analysis['review_reason']}")

            with res_col2:
                st.markdown("**Routing Destination:**")
                if route == ROUTE_PRIORITY:
                    st.markdown("""
                    <div class="priority-card">
                        <h4 style="color: #DC2626; margin: 0 0 6px 0;">🚨 PRIORITY HUMAN-REVIEW QUEUE</h4>
                        <p style="margin: 0; font-size: 0.9rem; color: #7F1D1D;">
                            Triggered by explicit emergency request or detected potential clinical red flags. Requires immediate clinician triage.
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                elif route == ROUTE_ROUTINE:
                    st.markdown("""
                    <div class="routine-card">
                        <h4 style="color: #16A34A; margin: 0 0 6px 0;">📅 ROUTINE APPOINTMENT QUEUE</h4>
                        <p style="margin: 0; font-size: 0.9rem; color: #14532D;">
                            Clear routine scheduling inquiry with no detected high-risk clinical concerns. Queued for standard clinic scheduling.
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="general-card">
                        <h4 style="color: #D97706; margin: 0 0 6px 0;">📋 GENERAL HUMAN-REVIEW QUEUE</h4>
                        <p style="margin: 0; font-size: 0.9rem; color: #78350F;">
                            Ambiguous, administrative, or unclear message. Queued for staff desk clarification and follow-up.
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

            st.divider()
            
            # Workflow Action Previews
            st.markdown("#### 📨 Simulated Workflow Actions & Notification Previews")
            st.info(notifications["disclaimer"])
            
            if route == ROUTE_PRIORITY:
                p_col1, p_col2 = st.columns(2)
                with p_col1:
                    st.markdown("**Simulated SMS Escalation Preview:**")
                    st.markdown(f'<div class="sms-box"><pre style="margin:0; white-space:pre-wrap;">{notifications["sms_preview"]}</pre></div>', unsafe_allow_html=True)
                with p_col2:
                    st.markdown("**Simulated Slack Clinical Channel Preview:**")
                    slack_data = notifications["slack_preview"]
                    st.markdown(f"""
                    <div class="slack-box">
                        <div style="font-size: 0.8rem; color: #94A3B8;">Channel: {slack_data['channel']} | From: {slack_data['bot_name']}</div>
                        <div style="font-weight: bold; font-size: 1rem; color: #F87171; margin: 4px 0;">{slack_data['title']}</div>
                        <hr style="border-color: #334155; margin: 6px 0;">
                        <div><strong>Reason:</strong> {slack_data['fields'][4]['value']}</div>
                        <div><strong>Symptoms:</strong> {slack_data['fields'][5]['value']}</div>
                        <div style="margin-top: 8px; font-size: 0.75rem; color: #64748B;">{slack_data['footer']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
            elif route == ROUTE_ROUTINE:
                draft = notifications["email_draft"]
                st.markdown("**Simulated Empathetic Appointment Acknowledgment Draft:**")
                st.markdown(f"""
                <div class="email-box">
                    <div><strong>To:</strong> {draft['to']}</div>
                    <div><strong>Subject:</strong> {draft['subject']}</div>
                    <div><strong>Status:</strong> <span style="color:#2563EB; font-weight:600;">{draft['status']}</span></div>
                    <hr style="margin: 8px 0;">
                    <div style="white-space: pre-wrap; font-family: sans-serif; font-size: 0.95rem; line-height: 1.5;">{draft['body']}</div>
                </div>
                """, unsafe_allow_html=True)
                
            else:  # GENERAL
                st.markdown("**Simulated Staff Clarification Notice:**")
                st.markdown(f'<div class="sms-box"><pre style="margin:0; white-space:pre-wrap;">{notifications["general_notice"]}</pre></div>', unsafe_allow_html=True)
                
                slack_data = notifications["slack_preview"]
                st.markdown("**Simulated Slack Intake Channel Post:**")
                st.markdown(f"""
                <div class="slack-box" style="border-left-color: #F59E0B;">
                    <div style="font-size: 0.8rem; color: #94A3B8;">Channel: {slack_data['channel']} | From: {slack_data['bot_name']}</div>
                    <div style="font-weight: bold; font-size: 1rem; color: #FBBF24; margin: 4px 0;">{slack_data['title']}</div>
                    <hr style="border-color: #334155; margin: 6px 0;">
                    <div><strong>Review Reason:</strong> {slack_data['fields'][2]['value']}</div>
                    <div style="margin-top: 8px; font-size: 0.75rem; color: #64748B;">{slack_data['footer']}</div>
                </div>
                """, unsafe_allow_html=True)


# ==============================================================================
# TAB 2: TRIAGE QUEUES & REVIEWER DASHBOARD
# ==============================================================================
with tab_dashboard:
    st.markdown("### 📊 Clinical & Staff Reviewer Dashboard")
    st.caption("Inspect queued patient submissions, review AI analysis summaries, and update triage status.")
    
    # Filter Controls
    f_col1, f_col2, f_col3 = st.columns([1, 1, 1])
    with f_col1:
        queue_filter = st.selectbox(
            "Filter by Workflow Queue:",
            ["All Queues", "🚨 Priority Human-Review Queue", "📅 Routine Appointment Queue", "📋 General Human-Review Queue"]
        )
    with f_col2:
        status_filter = st.selectbox(
            "Filter by Review Status:",
            ["All Statuses", "Pending Review", "Under Review", "Actioned", "Dismissed"]
        )
    with f_col3:
        search_query = st.text_input("🔍 Search by Patient Name or ID:", "")

    # Retrieve and filter records
    raw_submissions = get_all_submissions()
    filtered = raw_submissions
    
    if queue_filter.startswith("🚨"):
        filtered = [r for r in filtered if r["route_destination"] == ROUTE_PRIORITY]
    elif queue_filter.startswith("📅"):
        filtered = [r for r in filtered if r["route_destination"] == ROUTE_ROUTINE]
    elif queue_filter.startswith("📋"):
        filtered = [r for r in filtered if r["route_destination"] == ROUTE_GENERAL]
        
    if status_filter != "All Statuses":
        filtered = [r for r in filtered if r["review_status"] == status_filter]
        
    if search_query.strip():
        q = search_query.strip().lower()
        filtered = [r for r in filtered if q in r["patient_name"].lower() or q in r["id"].lower()]

    st.markdown(f"**Showing {len(filtered)} submission(s):**")
    
    if not filtered:
        st.info("No submissions match the selected filters.")
    else:
        # Display as a clean pandas table
        table_rows = []
        for r in filtered:
            route_label = "🚨 PRIORITY" if r["route_destination"] == ROUTE_PRIORITY else ("📅 ROUTINE" if r["route_destination"] == ROUTE_ROUTINE else "📋 GENERAL")
            table_rows.append({
                "ID": r["id"],
                "Patient Name": r["patient_name"],
                "Queue": route_label,
                "Stated Intent": r["stated_intent"],
                "Priority Flag": "YES" if r["priority_human_review"] else "NO",
                "Review Status": r["review_status"],
                "Engine": r["analysis_mode"],
                "Timestamp": r["timestamp"][:19]
            })
            
        df_display = pd.DataFrame(table_rows)
        st.dataframe(df_display, use_container_width=True, hide_index=True)

        st.divider()
        
        # Detailed Record Inspector
        st.markdown("#### 🔬 Detailed Submission Inspector")
        selected_id = st.selectbox("Select a submission ID to review details:", [r["id"] for r in filtered])
        
        if selected_id:
            record = get_submission_by_id(selected_id)
            if record:
                rec_col1, rec_col2 = st.columns([1, 1])
                with rec_col1:
                    st.markdown(f"**Patient Name:** {record['patient_name']}")
                    st.markdown(f"**Contact Information:** `{record['contact_info']}`")
                    st.markdown(f"**Reported Symptoms:**")
                    st.info(record["symptoms"])
                    st.markdown(f"**Original Patient Message:**")
                    st.code(record["patient_message"], language="text")

                with rec_col2:
                    st.markdown(f"**Assigned Queue:** `{record['route_destination']}`")
                    st.markdown(f"**Stated Intent:** `{record['stated_intent']}`")
                    st.markdown(f"**Analysis Engine:** `{record['analysis_mode']}`")
                    st.markdown(f"**AI/Heuristic Summary:** {record['ai_summary']}")
                    st.markdown(f"**Review Reason:** {record['review_reason']}")
                    
                    st.markdown("**Update Review Status:**")
                    u_col1, u_col2 = st.columns([2, 1])
                    with u_col1:
                        new_status = st.selectbox(
                            "Status",
                            ["Pending Review", "Under Review", "Actioned", "Dismissed"],
                            index=["Pending Review", "Under Review", "Actioned", "Dismissed"].index(record["review_status"]) if record["review_status"] in ["Pending Review", "Under Review", "Actioned", "Dismissed"] else 0,
                            key=f"status_select_{record['id']}"
                        )
                    with u_col2:
                        st.write("")
                        st.write("")
                        if st.button("Save Status", key=f"btn_save_{record['id']}"):
                            update_review_status(record["id"], new_status)
                            st.success(f"Status updated to '{new_status}'!")
                            st.rerun()


# ==============================================================================
# TAB 3: SYSTEM MANAGEMENT & EXPORT
# ==============================================================================
with tab_settings:
    st.markdown("### ⚙️ System Management, CSV Export & Demo Controls")
    
    col_s1, col_s2 = st.columns(2)
    
    with col_s1:
        st.markdown("#### 📥 Export Submissions to CSV")
        st.caption("Download all SQLite patient intake records formatted for reporting and offline analysis.")
        
        all_data = get_all_submissions()
        if all_data:
            df_export = pd.DataFrame(all_data)
            csv_bytes = df_export.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📄 Download All Submissions (CSV)",
                data=csv_bytes,
                file_name=f"medical_intake_submissions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.warning("Database is currently empty. No records to export.")

    with col_s2:
        st.markdown("#### 🔄 Demo Data Controls")
        st.caption("Reset the local SQLite database or reload standard test fixtures for demonstration.")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("🌱 Load 5 Educational Preset Scenarios", use_container_width=True):
                seed_sample_records()
                st.success("Loaded 5 standard educational test records into SQLite!")
                st.rerun()
                
        with col_btn2:
            confirm_reset = st.checkbox("Confirm database reset")
            if st.button("🗑️ Wipe All Database Records", use_container_width=True, disabled=not confirm_reset):
                reset_database()
                st.warning("All records wiped from local SQLite database.")
                st.rerun()

    st.divider()
    st.markdown("#### 📐 Workflow Architecture Summary")
    st.markdown("""
    ```
    [Patient Intake Submission]
                │
                ▼
    [Validation: Name, Symptoms, Message]
                │
                ▼
    [AI Analysis or Conservative Safety Fallback]
    ├── Factual Summary
    ├── Stated Intent: EMERGENCY_REQUEST | ROUTINE_APPOINTMENT | OTHER_OR_UNCLEAR
    └── Priority Flag: True | False (Detects acute red flags regardless of intent)
                │
                ▼
    [Deterministic Python Routing Engine]
    ├── EMERGENCY_REQUEST or Flagged Concern?  ──> [🚨 Priority Human-Review Queue]
    │                                              └── (Simulated SMS & Slack Escalation Previews)
    ├── Routine & NOT Flagged Concern?        ──> [📅 Routine Appointment Queue]
    │                                              └── (Empathetic Email Acknowledgment Draft)
    └── Ambiguous / Unclear / Administrative? ──> [📋 General Human-Review Queue]
                                                   └── (Staff Clarification Ticket & Slack Post)
    ```
    """)

