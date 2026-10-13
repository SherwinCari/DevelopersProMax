# Kiro Spec: UMak CCIS Smart Admission Advisor Prototype

## 1. Executive Summary & Pitch Setup

* **Project Name:** UMak CCIS Smart Admission Advisor (`HeronGuide`)
* **Core Problem:** Prospective students and shifters struggle to navigate complex PDF requirements across degrees and diplomas. On enrollment day, they receive their entrance exam (UMCET) score on the spot, creating high friction, wrong long queues, and anxiety when determining eligibility.
* **Solution:** A privacy-first, offline-ready AI decision-support tool that combines deterministic rule evaluation (GWA, Math, English, SHS Track, UMCET score) with a local LLM to deliver instant eligibility checks and smart alternative program routing (e.g., fallback to Diplomas).

### Pitch Hook Strategy ("Who Here?")
1. **Hook:** *"Who here has spent hours digging through static university PDFs, or waited in line on enrollment day, only to realize you missed a single Math requirement by 1%?"*
2. **Pivot:** *"Instead of panicking or walking away, what if an AI instantly checked your criteria in 2 seconds and gave you an immediate alternative path?"*
3. **Value:** Instant clarity for students, reduced administrative load for admissions offices, and 100% offline data privacy.

---

## 2. Requirements (`requirements.md`)

### User Stories & Acceptance Criteria

#### Story 1: Pre-Screening Evaluation (High School Grades)
* **As a** prospective UMak student
* **I want to** enter my SHS Track, GWA, Math, and English grades[cite: 15]
* **So that** I know which CCIS programs I qualify for before taking or receiving my entrance exam results[cite: 15].
* **Acceptance Criteria:**
  * System accepts GWA (75–100%), Math (75–100%), English (75–100%), and SHS Strand[cite: 15].
  * System flags exact missing cutoffs (e.g., Math grade < 85% for BS CS)[cite: 15].
  * System allows toggling "UMCET Score Not Received Yet".

#### Story 2: Live Enrollment Day Evaluation (UMCET Score Integration)
* **As an** applicant standing in line on enrollment day
* **I want to** select my newly received UMCET rating tier (`Below Average` to `Excellent`)[cite: 15, 16]
* **So that** my overall qualification status updates in real time[cite: 15, 16].
* **Acceptance Criteria:**
  * If UMCET score is `Low Average` or higher and grades meet criteria, mark BS CS / BS IT / BS IS as **Fully Qualified**[cite: 15].
  * If UMCET score is `Below Average` or grades fall short of degree baseline (85%), automatically recommend **Diploma in Application Development** or **Diploma in Computer Network Administration** (80% baseline)[cite: 15, 16].

#### Story 3: Human-like Guidance & Alternative Pathways
* **As an** applicant who does not qualify for a 4-year degree[cite: 15]
* **I want** the system to explain the gap empathetically and suggest realistic alternatives[cite: 15, 16]
* **So that** I do not abandon my academic application[cite: 15, 16].
* **Acceptance Criteria:**
  * Disqualification reasons must explicitly state the missing requirement[cite: 15, 16].
  * The system must always highlight valid diploma alternatives or next administrative steps[cite: 15, 16].

---

## 3. Technical Architecture & System Design (`design.md`)

┌──────────────────────────────────────────────────────────┐
│              Streamlit Frontend (UI)                      │
│   - SHS Track, GWA %, Math %, English %, UMCET Rating   │
└────────────────────────────┬─────────────────────────────┘
│
▼
┌──────────────────────────────────────────────────────────┐
│        Python Deterministic Evaluation Engine             │
│   - Evaluates inputs against umak_ccis_rules.json       │
│   - Zero hallucination on numeric thresholds              │
└────────────────────────────┬─────────────────────────────┘
│
▼
┌──────────────────────────────────────────────────────────┐
│          Local LLM (Ollama - llama3.2 / mistral)         │
│   - Generates empathetic advice & next steps via local API│
└──────────────────────────────────────────────────────────┘


### Data Schema (`umak_ccis_rules.json`)
```json
{
  "programs": [
    {
      "id": "bscs",
      "name": "Bachelor of Science in Computer Science",
      "track": "Application Development Elective Track",
      "min_gwa": 85,
      "min_math": 85,
      "min_english": 83,
      "preferred_tracks": ["STEM", "ICT"],
      "exam_ratings": ["Low Average", "Average", "High Average", "Excellent"],
      "fallback_program": "dip_appdev"
    },
    {
      "id": "bsit",
      "name": "Bachelor of Science in Information Technology",
      "track": "Information and Network Security Elective Track",
      "min_gwa": 85,
      "min_math": 85,
      "min_english": 83,
      "preferred_tracks": ["STEM", "ICT"],
      "exam_ratings": ["Low Average", "Average", "High Average", "Excellent"],
      "fallback_program": "dip_netadmin"
    },
    {
      "id": "bsis",
      "name": "Bachelor of Science in Information Systems",
      "min_gwa": 85,
      "min_math": 85,
      "min_english": 83,
      "preferred_tracks": ["Any"],
      "exam_ratings": ["Low Average", "Average", "High Average", "Excellent"],
      "fallback_program": "dip_appdev"
    },
    {
      "id": "dip_appdev",
      "name": "Diploma in Application Development",
      "min_gwa": 80,
      "min_math": 0,
      "min_english": 0,
      "preferred_tracks": ["Any"],
      "exam_ratings": ["Below Average", "Low Average", "Average", "High Average", "Excellent"]
    },
    {
      "id": "dip_netadmin",
      "name": "Diploma in Computer Network Administration",
      "min_gwa": 80,
      "min_math": 0,
      "min_english": 0,
      "preferred_tracks": ["Any"],
      "exam_ratings": ["Below Average", "Low Average", "Average", "High Average", "Excellent"]
    }
  ]
}
4. Steering Guidelines (.kiro/steering/)
Technical Steering (tech.md)
Use Python 3.10+ inside an isolated virtual environment (venv).

Ensure all LLM processing runs through local Ollama (llama3.2 or mistral) to guarantee offline capabilities and zero API costs.

Keep rule evaluation strictly deterministic in Python; do not let the LLM guess numeric pass/fail thresholds.

UI & Product Steering (product.md)
UI must be scannable with clear status badges (🟢 Qualified, 🟡 Conditional, 🔴 Alternative Path Suggested).

Provide immediate clear messaging—avoid long walls of text.

5. Execution Plan & Tasks (tasks.md)
[ ] Task 1: Environment Setup

[ ] Initialize python -m venv venv and activate it.

[ ] Install dependencies: pip install streamlit ollama.

[ ] Pull local model: ollama pull llama3.2.

[ ] Task 2: Rule Engine Implementation

[ ] Save umak_ccis_rules.json with exact CCIS requirements[cite: 15, 16].

[ ] Write check_eligibility(user_data, rules) function in Python[cite: 15, 16].

[ ] Task 3: Streamlit Interface Development

[ ] Create form for GWA, Math, English, Strand, and UMCET status inputs[cite: 15, 16].

[ ] Add dynamic UMCET rating dropdown when status is set to "Score Received"[cite: 15, 16].

[ ] Task 4: Local LLM Integration

[ ] Write system prompt instructing Ollama to summarize the qualification results warmly.

[ ] Connect output from decision engine into local Ollama API call.

[ ] Task 5: Demo Simulation & Pitch Practice

[ ] Test Edge Case 1: Student with 86% GWA but 84% Math (triggers Diploma recommendation)[cite: 15, 16].

[ ] Test Edge Case 2: Student with 88% GWA and 90% Math + Low Average UMCET (triggers BS CS qualified status)[cite: 15].

[ ] Practice "Who Here?" live demonstration.