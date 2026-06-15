"""
Intelligent application-form question answerer.

This module answers *any* question an application form might ask during the
apply flow on LinkedIn, Indeed, ZipRecruiter, or a company ATS (Workday,
Greenhouse, Lever, etc.). It combines three sources of truth, in order:

    1. Deterministic heuristics for common screening questions
       (work authorization, visa sponsorship, years of experience, salary,
        notice period, relocation, start date, EEO/diversity, etc.).
    2. The applicant's own profile, assembled from config.py + resume text.
    3. The OpenAI model, optionally grounded with lightweight web research
       about the company, for open-ended / company-specific questions.

Every answer is cached to disk (data_folder/answer_cache.json) so the same
question is answered consistently across a run and across sessions.

Public API:
    qa = QuestionAnswerer(config, resume_text=..., job=...)
    answer = qa.answer(
        question="How many years of experience do you have with AWS?",
        input_type="text",          # text | textarea | number | select | radio | checkbox | boolean
        options=["0-1", "2-3", "4-5"],  # choices for select/radio, if any
    )
"""

import os
import re
import json
import logging
from typing import Dict, Any, List, Optional

from src.utils.ai_client import AIClient

logger = logging.getLogger(__name__)

CACHE_PATH = os.path.join("data_folder", "answer_cache.json")


class QuestionAnswerer:
    def __init__(
        self,
        config: Dict[str, Any],
        resume_text: str = "",
        job: Optional[Dict[str, Any]] = None,
    ):
        self.config = config or {}
        self.user_info = self.config.get("USER_INFO", {})
        self.job_search = self.config.get("JOB_SEARCH", {})
        self.application = self.config.get("APPLICATION", {})
        self.qa_settings = self.config.get("QUESTION_ANSWERING", {})
        self.resume_text = resume_text or ""
        self.job = job or {}

        self.ai = AIClient(config)
        self._cache = self._load_cache()
        self._company_research: Dict[str, str] = {}

        # Defaults the user can override in config.py -> QUESTION_ANSWERING
        self.defaults = {
            "work_authorized": self.qa_settings.get("authorized_to_work", True),
            "needs_sponsorship": self.qa_settings.get("requires_sponsorship", True),
            "years_experience": self.qa_settings.get("default_years_experience", 3),
            "desired_salary": self.qa_settings.get("desired_salary", self.job_search.get("min_salary", 90000)),
            "willing_to_relocate": self.qa_settings.get("willing_to_relocate", True),
            "notice_period": self.qa_settings.get("notice_period", "2 weeks"),
            "start_date": self.qa_settings.get("start_date", "Immediately / 2 weeks notice"),
            "gender": self.qa_settings.get("gender", "Decline to self-identify"),
            "race": self.qa_settings.get("race", "Decline to self-identify"),
            "veteran": self.qa_settings.get("veteran_status", "I am not a protected veteran"),
            "disability": self.qa_settings.get("disability_status", "I do not wish to answer"),
        }

    # ------------------------------------------------------------------ #
    # Cache
    # ------------------------------------------------------------------ #
    def _load_cache(self) -> Dict[str, str]:
        try:
            if os.path.exists(CACHE_PATH):
                with open(CACHE_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.debug(f"Could not load answer cache: {e}")
        return {}

    def _save_cache(self):
        try:
            os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
            with open(CACHE_PATH, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, indent=2)
        except Exception as e:
            logger.debug(f"Could not save answer cache: {e}")

    @staticmethod
    def _cache_key(question: str, options: Optional[List[str]]) -> str:
        norm = re.sub(r"\s+", " ", (question or "").strip().lower())
        if options:
            norm += " | " + " | ".join(o.strip().lower() for o in options)
        return norm

    # ------------------------------------------------------------------ #
    # Public entry point
    # ------------------------------------------------------------------ #
    def answer(
        self,
        question: str,
        input_type: str = "text",
        options: Optional[List[str]] = None,
    ) -> str:
        """
        Return the best answer for a form question.

        For select/radio with options, the returned string is guaranteed to be
        one of the provided options (best-effort match). For boolean inputs the
        return is "Yes" or "No".
        """
        question = (question or "").strip()
        if not question:
            return ""

        key = self._cache_key(question, options)
        if key in self._cache:
            logger.debug(f"Answer cache hit for: {question[:60]}")
            return self._cache[key]

        # 1) Deterministic heuristics
        answer = self._heuristic_answer(question, input_type, options)

        # 2) Fall back to AI for open-ended questions
        if answer is None:
            answer = self._ai_answer(question, input_type, options)

        # 3) Last-resort safe defaults
        if answer is None or answer == "":
            answer = self._fallback_answer(input_type, options)

        # Constrain to provided options if applicable
        if options:
            answer = self._match_to_option(answer, options)

        self._cache[key] = answer
        self._save_cache()
        logger.info(f"Answered form question '{question[:50]}...' -> '{str(answer)[:50]}'")
        return answer

    # ------------------------------------------------------------------ #
    # Heuristics for common screening questions
    # ------------------------------------------------------------------ #
    def _heuristic_answer(
        self, question: str, input_type: str, options: Optional[List[str]]
    ) -> Optional[str]:
        q = question.lower()
        is_boolean = input_type in ("boolean", "radio", "checkbox") or self._looks_yes_no(options)

        # Work authorization
        if self._any(q, ["authorized to work", "legally authorized", "work authorization",
                          "eligible to work", "right to work"]):
            return self._yes_no(self.defaults["work_authorized"], options)

        # Visa sponsorship
        if self._any(q, ["sponsorship", "sponsor", "require sponsorship", "visa status",
                          "now or in the future require"]):
            # "Will you require sponsorship?" -> answer based on needs_sponsorship
            return self._yes_no(self.defaults["needs_sponsorship"], options)

        # Security clearance
        if self._any(q, ["security clearance", "clearance"]):
            return self._yes_no(False, options)

        # Years of experience
        if self._any(q, ["years of experience", "years experience", "how many years",
                          "years of work experience"]):
            yrs = str(self.defaults["years_experience"])
            if options:
                return self._pick_experience_option(options, self.defaults["years_experience"])
            return yrs

        # Salary expectations
        if self._any(q, ["salary", "compensation", "expected pay", "desired pay",
                          "rate expectation", "pay expectation"]):
            return str(self.defaults["desired_salary"])

        # Relocation
        if self._any(q, ["relocate", "relocation", "willing to move"]):
            return self._yes_no(self.defaults["willing_to_relocate"], options)

        # Notice period / availability / start date
        if self._any(q, ["notice period"]):
            return str(self.defaults["notice_period"])
        if self._any(q, ["start date", "when can you start", "available to start", "availability"]):
            return str(self.defaults["start_date"])

        # Contact / profile fields
        if self._any(q, ["linkedin"]):
            return self.user_info.get("linkedin", "")
        if self._any(q, ["github"]):
            return self.user_info.get("github", "")
        if self._any(q, ["portfolio", "personal website", "your website"]):
            return self.user_info.get("portfolio", "")
        if self._any(q, ["phone"]):
            return self.user_info.get("phone", "")
        if self._any(q, ["email"]):
            return self.user_info.get("email", "")
        if self._any(q, ["full name", "your name", "legal name"]):
            return self.user_info.get("name", "")
        if self._any(q, ["city", "current location", "where are you located", "location"]) \
                and input_type in ("text", "select"):
            locs = self.job_search.get("locations", [])
            return locs[0] if locs else ""

        # EEO / diversity questions -> privacy-preserving defaults
        if self._any(q, ["gender", "what is your gender"]):
            return self.defaults["gender"]
        if self._any(q, ["race", "ethnicity", "hispanic or latino"]):
            return self.defaults["race"]
        if self._any(q, ["veteran", "protected veteran"]):
            return self.defaults["veteran"]
        if self._any(q, ["disability", "disabled"]):
            return self.defaults["disability"]

        # Generic willingness / agreement yes/no questions -> Yes
        if is_boolean and self._any(q, ["are you willing", "do you agree", "can you", "are you able",
                                        "do you consent", "are you comfortable", "have you read"]):
            return self._yes_no(True, options)

        return None

    # ------------------------------------------------------------------ #
    # AI-backed answers for open-ended questions
    # ------------------------------------------------------------------ #
    def _ai_answer(
        self, question: str, input_type: str, options: Optional[List[str]]
    ) -> Optional[str]:
        if not self.ai.available:
            return None

        profile = self._build_profile_context()
        company = self.job.get("company_name", "")
        research = self._research_company(company) if company else ""

        length_hint = (
            "Answer in 2-4 concise sentences."
            if input_type == "textarea"
            else "Answer in one short sentence or phrase suitable for a form field."
        )
        option_hint = (
            "\nChoose the single best answer from these options and reply with that option text exactly:\n- "
            + "\n- ".join(options)
            if options
            else ""
        )

        system = (
            "You are helping a real job applicant fill out an application form. "
            "Answer each question truthfully and professionally in the FIRST PERSON, "
            "as the applicant, using only the facts in their profile. "
            "Never invent credentials, employers, or degrees that are not in the profile. "
            "If a specific fact is unknown, give a reasonable, honest, professional answer "
            "that does not fabricate specifics."
        )
        company_block = ("Company context:\n" + research) if research else ""
        user = f"""Applicant profile:
{profile}

{company_block}

Form question: {question}
Field type: {input_type}
{length_hint}{option_hint}

Provide ONLY the answer text, with no preamble, labels, or quotation marks."""

        answer = self.ai.chat(system=system, user=user, temperature=0.5, max_tokens=400)
        return answer or None

    # ------------------------------------------------------------------ #
    # Lightweight company research (best effort, never fatal)
    # ------------------------------------------------------------------ #
    def _research_company(self, company: str) -> str:
        if not self.qa_settings.get("research_company", True):
            return ""
        if company in self._company_research:
            return self._company_research[company]

        context_parts = []

        # Use the job description we already have — richest free signal.
        desc = self.job.get("description", "")
        if desc:
            context_parts.append(f"Job description excerpt:\n{desc[:1500]}")

        # Optionally fetch the company's public site / a search snippet.
        try:
            import requests
            from bs4 import BeautifulSoup

            url = self.job.get("company_url") or self.job.get("company_website")
            if url:
                resp = requests.get(
                    url,
                    timeout=8,
                    headers={"User-Agent": "Mozilla/5.0 (compatible; JobBot/1.0)"},
                )
                if resp.ok:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    text = " ".join(soup.get_text(" ").split())
                    if text:
                        context_parts.append(f"Company website excerpt:\n{text[:1200]}")
        except Exception as e:
            logger.debug(f"Company research fetch failed for {company}: {e}")

        research = "\n\n".join(context_parts)
        self._company_research[company] = research
        return research

    # ------------------------------------------------------------------ #
    # Profile assembly
    # ------------------------------------------------------------------ #
    def _build_profile_context(self) -> str:
        lines = [
            f"Name: {self.user_info.get('name', '')}",
            f"Email: {self.user_info.get('email', '')}",
            f"Phone: {self.user_info.get('phone', '')}",
            f"LinkedIn: {self.user_info.get('linkedin', '')}",
            f"GitHub: {self.user_info.get('github', '')}",
            f"Target roles: {', '.join(self.job_search.get('job_titles', [])[:6])}",
            f"Key skills/keywords: {', '.join(self.job_search.get('keywords', [])[:20])}",
            f"Preferred locations: {', '.join(self.job_search.get('locations', []))}",
            f"Years of experience: {self.defaults['years_experience']}",
            f"Work authorized in the US: {'Yes' if self.defaults['work_authorized'] else 'No'}",
            f"Requires visa sponsorship: {'Yes' if self.defaults['needs_sponsorship'] else 'No'}",
        ]
        if self.resume_text:
            lines.append(f"\nResume text:\n{self.resume_text[:3500]}")
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _any(text: str, needles: List[str]) -> bool:
        return any(n in text for n in needles)

    @staticmethod
    def _looks_yes_no(options: Optional[List[str]]) -> bool:
        if not options:
            return False
        low = {o.strip().lower() for o in options}
        return low <= {"yes", "no"} and len(low) > 0

    def _yes_no(self, truthy: bool, options: Optional[List[str]]) -> str:
        if options:
            target = "yes" if truthy else "no"
            for o in options:
                if o.strip().lower() == target:
                    return o
        return "Yes" if truthy else "No"

    @staticmethod
    def _pick_experience_option(options: List[str], years: int) -> str:
        """Pick the option whose numeric range best contains `years`."""
        best = options[0]
        best_score = -1
        for o in options:
            nums = [int(n) for n in re.findall(r"\d+", o)]
            if not nums:
                continue
            lo = min(nums)
            hi = max(nums)
            if lo <= years <= hi:
                return o
            # otherwise score by closeness
            score = -min(abs(years - lo), abs(years - hi))
            if score > best_score:
                best_score = score
                best = o
        return best

    def _match_to_option(self, answer: str, options: List[str]) -> str:
        """Constrain a free-text answer to the closest provided option."""
        if not answer:
            return options[0]
        a = answer.strip().lower()
        # exact
        for o in options:
            if o.strip().lower() == a:
                return o
        # substring either direction
        for o in options:
            ol = o.strip().lower()
            if ol and (ol in a or a in ol):
                return o
        # yes/no normalization
        if a.startswith("y"):
            for o in options:
                if o.strip().lower() == "yes":
                    return o
        if a.startswith("n"):
            for o in options:
                if o.strip().lower() == "no":
                    return o
        return options[0]

    def _fallback_answer(self, input_type: str, options: Optional[List[str]]) -> str:
        if options:
            # Prefer a neutral non-placeholder option
            for o in options:
                if o.strip():
                    return o
            return options[0]
        if input_type in ("boolean", "radio", "checkbox"):
            return "Yes"
        if input_type == "number":
            return str(self.defaults["years_experience"])
        return ""
