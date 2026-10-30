## AI-Powered Medical Intake & Escalation Workflow
 
**GitHub:** https://github.com/Roobika06/ai-medical-intake-workflow  
**Tone:** Professional, articulate, safety-first, software engineering focus  

---

## 🎬 [0:00 - 0:25] The Problem & Motivation

**[Visual: Web browser showing Streamlit App header "Medical Intake & Escalation", Safety Banner, and 4 metric cards]**

> **Speaker:**  
> "Hello everyone. Today I'm presenting my AI-powered medical intake and escalation workflow prototype.  
> 
> In real-world digital health clinics, hundreds of patient intake forms arrive daily. Some patients clearly want routine checkups; others submit vague questions; but critically, some describe life-threatening symptoms casually in the middle of a routine message.  
> 
> The core engineering challenge is: **How can software safely assist clinical intake desks without ever treating the absence of an emergency keyword as medical clearance?**"

---

## 🏗️ [0:25 - 0:50] Architecture & Core Technologies

**[Visual: Switching briefly to the Mermaid diagram or scrolling through System Overview]**

> **Speaker:**  
> "To solve this, I designed a resilient hybrid architecture using:
> - **Python 3.11** with a clean **Streamlit** user interface.
> - **Google Gemini 2.5 Flash** for structured JSON message summarization and intent extraction.
> - An offline **Conservative Rule-Based Fallback Engine** that guarantees zero-downtime and safe escalation even when offline or without an API key.
> - **SQLite** with parameterized queries for HIPAA-mindful local data persistence.
> - **Pandas** for live filtering, metric counters, and CSV reporting.
> - And **Pytest** for deterministic unit testing covering 19 test cases."

---

## 🤖 [0:50 - 1:20] The AI Prompt & Two-Stage Routing Logic

**[Visual: Navigating to Patient Intake Form and highlighting Prompt Details]**

> **Speaker:**  
> "Notice the design of our AI prompt. Rather than asking a generic model to diagnose or triage, we force the AI to return a strict JSON schema that decouples two vital questions:
> 1. What was the patient's **stated request** — `EMERGENCY_REQUEST`, `ROUTINE_APPOINTMENT`, or `OTHER_OR_UNCLEAR`?
> 2. Separately, does the text contain **potentially concerning content** requiring priority human review?
> 
> Downstream, deterministic Python rules evaluate these outputs:
> - **Rule A:** An explicit emergency routes immediately to the **Priority Human-Review Queue**.
> - **Rule B:** If a clinical red flag is flagged, it *overrides* any routine intent and escalates to Priority Review.
> - **Rule C:** Only clear appointment requests with zero detected concerns go to the **Routine Appointment Queue**.
> - **Rule D:** Any ambiguity or system failure safely routes to **General Review**, never defaulting to routine."

---

## 🧪 [1:20 - 2:05] Live Demonstration of Test Scenarios

**[Visual: Selecting presets from the dropdown and clicking 'Submit Intake']**

> **Speaker:**  
> "Let's demonstrate three critical scenarios using our pre-configured test fixtures:
> 
> **Case 1: Explicit Emergency.**  
> David Miller reports severe crushing chest pain and asks to call 911.  
> *[Clicks submit]*  
> The system immediately flags priority escalation, generates a simulated SMS dispatch to On-Call Nurse Triage, and posts a high-priority alert card to Slack `#clinical-escalations`. No actual SMS is sent — all notifications are safely simulated.
> 
> **Case 2: Subtle Concerning Red Flags.**  
> Here, Robert Evans writes: *'Can I book a regular appointment next Tuesday? My face feels numb and I'm slurring words.'*  
> *[Submits]*  
> Notice what happened: The patient's *stated intent* was a routine appointment, but our safety rule intercepted the acute neurological symptoms (facial droop, slurred speech). It **overrode** routine scheduling and routed directly to the Priority Queue!
> 
> **Case 3: Negation Awareness.**  
> Elena Rostova writes: *'This is definitely NOT an emergency, but I need an inhaler refill.'*  
> *[Submits]*  
> A naive keyword search would see the word 'emergency' and trigger false alarms. Our system understands linguistic negation, correctly recognizing it as a routine maintenance inquiry."

---

## 📊 [2:05 - 2:30] Dashboard, Database & Iterative Improvements

**[Visual: Clicking 'Triage Queues & Reviewer Dashboard' tab, showing table, filtering, and inspector]**

> **Speaker:**  
> "Every submission is stored in SQLite. Reviewers can filter between Priority, Routine, and General queues, inspect raw patient messages alongside the AI summary, and update status from 'Pending' to 'Actioned'.  
> 
> Reviewers can also export the full audit trail as a clean CSV file with one click.
> 
> During development and automated testing, I specifically hardened the fallback regex to handle complex linguistic patterns like 'weakness in left arm' and negated phrases, ensuring our 19 automated Pytest cases achieve a 100% pass rate."

---

## 🛡️ [2:30 - 3:00] Safety Disclaimers & Future Roadmap

**[Visual: Highlighting the prominent disclaimer banner and conclusion slide]**

> **Speaker:**  
> "To conclude with clinical safety: This is strictly an educational prototype. It does not provide medical triage, diagnosis, or clearance.  
> 
> In a production environment, future steps would include:
> 1. Integration with certified FHIR/HL7 EHR systems like Epic or Cerner.
> 2. Dual-clinician confirmation workflows for high-risk escalations.
> 3. Rigorous HIPAA security controls, full audit logging, and clinical validation studies.
> 
> Thank you for your time, and I look forward to discussing the architecture further!"
