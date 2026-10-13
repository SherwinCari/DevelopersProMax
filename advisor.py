"""LLM advisor for HeronGuide (Ollama / llama3.1:8b).

The advisor only *phrases* decisions already made by ``rules.py``. It never
computes or changes a verdict. Every call is wrapped with a timeout and a
deterministic fallback, so a slow or offline Ollama can never break a live demo.
"""
from __future__ import annotations

import os
import threading
from typing import Callable, Optional

from data.programs import Program
from rules import ProgramResult, Status, StudentInput, alternatives

MODEL = "llama3.1:8b"
# Generous enough to cover a cold model load (loading the ~5GB model into memory
# can take up to a minute on first call); subsequent calls are fast.
_DEFAULT_TIMEOUT = 90.0

def _resolve_host() -> str:
    """Pick a host the client can actually CONNECT to.

    Two Windows gotchas are handled here:
    * ``OLLAMA_HOST`` is often set to ``0.0.0.0:11434`` (a server *bind* address);
      you cannot connect to ``0.0.0.0``, so rewrite it to ``127.0.0.1``.
    * Bare ``localhost`` may resolve to IPv6 (::1) first while Ollama listens on
      IPv4, so prefer the explicit loopback IP.
    """
    raw = (os.environ.get("OLLAMA_HOST") or "").strip()
    if not raw:
        return "http://127.0.0.1:11434"
    host = raw if "://" in raw else f"http://{raw}"
    return host.replace("0.0.0.0", "127.0.0.1").replace("localhost", "127.0.0.1")


OLLAMA_HOST = _resolve_host()


def _client():
    """Return an Ollama client bound to the explicit host (imported lazily so
    tests and the fallback path don't require the package)."""
    import ollama

    return ollama.Client(host=OLLAMA_HOST)

# System prompt shared by all advisor calls. The constraint against changing
# verdicts is stated explicitly and repeatedly.
_SYSTEM = (
    "You are HeronGuide, a warm, encouraging admissions assistant for the "
    "University of Makati College of Computing and Information Sciences (CCIS). "
    "You NEVER decide whether a student qualifies. A deterministic rule engine "
    "has already decided that and you will be told the result. Your only job is "
    "to explain the given result kindly and clearly, and to encourage the "
    "student. Keep replies concise (2-4 short sentences unless asked for a list). "
    "Do not invent requirements or numbers beyond what you are given."
)


# ---------------------------------------------------------------------------
# Timeout harness
# ---------------------------------------------------------------------------
def _run_with_timeout(fn: Callable[[], str], timeout: float) -> str:
    """Run ``fn`` on a worker thread; raise TimeoutError if it overruns."""
    box: dict[str, object] = {}

    def worker() -> None:
        try:
            box["value"] = fn()
        except Exception as exc:  # noqa: BLE001 - surfaced below
            box["error"] = exc

    t = threading.Thread(target=worker, daemon=True)
    t.start()
    t.join(timeout)
    if t.is_alive():
        raise TimeoutError(f"LLM call exceeded {timeout}s")
    if "error" in box:
        raise box["error"]  # type: ignore[misc]
    return str(box.get("value", "")).strip()


def _try_model(
    build_prompt: Callable[[], str],
    timeout: float = _DEFAULT_TIMEOUT,
    system: str = _SYSTEM,
) -> Optional[str]:
    """Return the model's text, or None if Ollama is missing/slow/erroring."""

    def call() -> str:
        resp = _client().chat(
            model=MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": build_prompt()},
            ],
            options={"temperature": 0.6},
        )
        return resp["message"]["content"]

    try:
        return _run_with_timeout(call, timeout) or None
    except Exception:  # noqa: BLE001 - demo must never crash
        return None


def _with_fallback(
    build_prompt: Callable[[], str],
    fallback: str,
    timeout: float = _DEFAULT_TIMEOUT,
) -> str:
    """Call the model with ``build_prompt``'s text; return fallback on any failure."""
    return _try_model(build_prompt, timeout) or fallback


def ollama_available() -> bool:
    """Quick check that the Ollama server answers and has MODEL pulled."""

    def probe() -> str:
        names = [m.model for m in _client().list().models]
        return "yes" if any(n and n.split(":")[0] == MODEL.split(":")[0] for n in names) else ""

    try:
        return bool(_run_with_timeout(probe, 3.0))
    except Exception:  # noqa: BLE001
        return False


def warm_up(timeout: float = 120.0) -> bool:
    """Preload the model into memory so later demo responses are fast.

    Returns True if the model answered a trivial prompt. Safe to call once at
    startup; if Ollama is slow or offline it simply returns False.
    """

    def ping() -> str:
        resp = _client().chat(
            model=MODEL,
            messages=[{"role": "user", "content": "Reply with the word READY."}],
            options={"num_predict": 3},
        )
        return resp["message"]["content"]

    try:
        return bool(_run_with_timeout(ping, timeout))
    except Exception:  # noqa: BLE001
        return False


# ---------------------------------------------------------------------------
# Verdict summarisation helpers
# ---------------------------------------------------------------------------
def _summarise_results(results: list[ProgramResult]) -> str:
    lines = []
    for r in results:
        if r.status is Status.QUALIFIED:
            lines.append(f"- {r.program.name}: QUALIFIED")
        elif r.status is Status.PENDING_UMCET:
            lines.append(f"- {r.program.name}: PENDING (grades OK, awaiting UMCET)")
        else:
            gaps = "; ".join(g.message for g in r.gaps) or "requirements not met"
            lines.append(f"- {r.program.name}: NOT QUALIFIED ({gaps})")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public advisor functions
# ---------------------------------------------------------------------------
def explain(student: StudentInput, results: list[ProgramResult]) -> str:
    """Empathetic natural-language summary of the already-decided verdict."""
    qualified = [r for r in results if r.status is Status.QUALIFIED]
    pending = [r for r in results if r.status is Status.PENDING_UMCET]
    alts = alternatives(results)

    def prompt() -> str:
        return (
            "Here is the student's evaluation result (already decided):\n"
            f"{_summarise_results(results)}\n\n"
            f"SHS track: {student.shs_track}. "
            "Write a short, warm message that: (1) tells them clearly where they "
            "stand, (2) if they did not qualify for a degree, names the exact "
            "missing requirement and encourages the diploma alternative, (3) if "
            "they qualified, congratulates them. Do not change any decision."
        )

    return _with_fallback(prompt, _fallback_explain(qualified, pending, alts, results))


def explain_ex(student: StudentInput, results: list[ProgramResult]) -> tuple[str, bool]:
    """Like :func:`explain` but also reports whether the text came from the model
    (True) or from the deterministic fallback (False)."""
    qualified = [r for r in results if r.status is Status.QUALIFIED]
    pending = [r for r in results if r.status is Status.PENDING_UMCET]
    fallback = _fallback_explain(qualified, pending, alternatives(results), results)
    text = explain(student, results)
    return text, text != fallback


_CHAT_SYSTEM = (
    "You are HeronGuide, a friendly assistant for the University of Makati (UMak) "
    "College of Computing and Information Sciences (CCIS). Answer GENERAL questions "
    "about the CCIS programs listed below. Never say whether a specific student "
    "qualifies; tell them to use the eligibility advisor on the Home page. If you do "
    "not know something, say so and suggest the UMak Admissions Office. Do not invent "
    "deadlines, fees, or requirements. Keep answers under 5 sentences."
)


def _catalog_blurb() -> str:
    from data.programs import all_programs

    return "\n".join(
        f"- {p.name} ({p.code}, {p.type.label}): GWA>={p.gwa_min}, Math>={p.math_min}, "
        f"English>={p.english_min}, UMCET>={p.umcet_min_tier.label if p.umcet_min_tier is not None else 'none'}"
        for p in all_programs()
    )


def chat_answer(question: str) -> tuple[str, bool]:
    """General Q&A. Returns (answer, from_model)."""
    text = _try_model(
        lambda: f"Programs (prototype demo data):\n{_catalog_blurb()}\n\nQuestion: {question}",
        timeout=_DEFAULT_TIMEOUT,
        system=_CHAT_SYSTEM,
    )
    if text:
        return text, True
    return (
        "The local AI model isn't reachable right now, so I can't answer that "
        "freely. You can browse the programs and their cutoffs on the CCIS Programs "
        "page, check your own grades on Home, or ask the UMak Admissions Office.",
        False,
    )


def recommend_review(student: StudentInput, program: Program) -> str:
    """Program-specific review recommendations for a qualified student."""

    def prompt() -> str:
        return (
            f"The student qualified for {program.name} at UMak CCIS. "
            "List 4-5 concrete topics they should review to prepare for the "
            "admission interview and first term, tailored to this program, plus "
            "one short line of encouragement. Use a brief bulleted list."
        )

    return _with_fallback(prompt, _fallback_review(program))


def interview_question(program: Program, index: int, asked: Optional[list[str]] = None) -> str:
    """Generate one practice admission-interview question for ``program``."""
    asked = asked or []

    def prompt() -> str:
        prior = ("\nAvoid repeating these: " + " | ".join(asked)) if asked else ""
        return (
            f"You are conducting a friendly mock admission interview for "
            f"{program.name} at UMak CCIS. Ask ONE question (question #{index + 1}). "
            "Return only the question text, no preamble." + prior
        )

    bank = _QUESTION_BANK.get(program.code, _QUESTION_BANK["_default"])
    fallback = bank[index % len(bank)]
    return _with_fallback(prompt, fallback, timeout=20.0)


def interview_feedback(program: Program, question: str, answer: str) -> str:
    """Brief, encouraging feedback on a practice-interview answer."""

    def prompt() -> str:
        return (
            f"Mock interview for {program.name}. Question: {question}\n"
            f"Student answer: {answer}\n"
            "Give 1-2 sentences of warm, constructive feedback. Encourage them."
        )

    return _with_fallback(prompt, _fallback_feedback(answer), timeout=20.0)


# ---------------------------------------------------------------------------
# Deterministic fallbacks (used when Ollama is slow / offline / erroring)
# ---------------------------------------------------------------------------
def _fallback_explain(qualified, pending, alts, results) -> str:
    # Celebrate only when an actual DEGREE is attained or pending. Diploma-only
    # qualifications are handled by the empathetic alternative-path branch below,
    # so a near-miss degree applicant never gets a falsely cheerful message.
    degree_qualified = [r for r in qualified if r.program.is_degree]
    degree_pending = [r for r in pending if r.program.is_degree]

    if degree_qualified:
        names = ", ".join(r.program.name for r in degree_qualified)
        return (
            f"Great news — based on your grades and UMCET rating, you qualify for "
            f"{names}. That's a strong result. Review the recommended topics below "
            "and try the quick practice interview to get ready for enrollment day."
        )
    if degree_pending:
        names = ", ".join(r.program.name for r in degree_pending)
        return (
            f"Your grades meet the requirements for {names}. Once you receive your "
            "UMCET rating, come back and select it to confirm your qualification."
        )

    # No degree is attainable — explain the gap kindly and route to alternatives.
    missing = []
    for r in results:
        if r.program.is_degree and r.gaps:
            missing.extend(g.message for g in r.gaps)
    missing_txt = missing[0] if missing else "a degree requirement was not met"
    if alts:
        alt_names = ", ".join(r.program.name for r in alts)
        return (
            f"You're close. Right now a 4-year degree isn't a match because "
            f"{missing_txt}. Don't give up — you qualify for {alt_names}, a solid "
            "pathway into tech that can also open doors later."
        )
    return (
        f"Right now the degree requirements aren't met ({missing_txt}). Talk to the "
        "CCIS admissions office about the best next step for your situation."
    )


def _fallback_review(program: Program) -> str:
    topics = _REVIEW_TOPICS.get(program.code, _REVIEW_TOPICS["_default"])
    bullets = "\n".join(f"- {t}" for t in topics)
    return f"To prepare for {program.name}, review:\n{bullets}\n\nYou've got this!"


def _fallback_feedback(answer: str) -> str:
    if len(answer.strip()) < 15:
        return (
            "Good start — try to expand your answer with a specific example so the "
            "interviewer sees your reasoning. Keep going!"
        )
    return (
        "Nice, clear answer. Adding a concrete example or result would make it even "
        "stronger. You're doing well!"
    )


_REVIEW_TOPICS = {
    "BSCS": [
        "Logic and problem-solving fundamentals",
        "Basic programming concepts (variables, loops, functions)",
        "Mathematics: algebra and introductory discrete math",
        "Why you want to study Computer Science (motivation)",
        "A simple project or idea you'd like to build",
    ],
    "BSIT": [
        "Computer hardware and networking basics",
        "Introductory programming and troubleshooting",
        "Information security awareness",
        "Why Information Technology fits your goals",
        "A tech problem you solved recently",
    ],
    "BSIS": [
        "How businesses use information systems",
        "Basic data and spreadsheet literacy",
        "Communication and teamwork examples",
        "Why Information Systems interests you",
        "An example of improving a process with technology",
    ],
    "_default": [
        "Your motivation for choosing this program",
        "Basic computer and problem-solving skills",
        "A relevant project or experience",
        "Your study and time-management habits",
    ],
}

_QUESTION_BANK = {
    "BSCS": [
        "Why do you want to study Computer Science?",
        "Tell me about a problem you enjoyed solving. How did you approach it?",
        "What does 'logical thinking' mean to you, and where have you used it?",
        "Is there something you'd like to build with code someday?",
    ],
    "BSIT": [
        "Why Information Technology, and what excites you about it?",
        "Describe a time you fixed a tech or computer problem.",
        "How do you keep yourself updated about technology?",
        "What would you like to learn to do with IT skills?",
    ],
    "BSIS": [
        "Why are you interested in Information Systems?",
        "How can technology improve the way a business or school works?",
        "Tell me about a time you worked well in a team.",
        "What process would you like to make more efficient, and how?",
    ],
    "_default": [
        "Why did you choose this program?",
        "What are your strengths as a learner?",
        "Tell me about a challenge you overcame.",
        "Where do you see yourself after graduating?",
    ],
}
