# Intelligent Application-Form Question Answering

A lot of applications die at the screening-questions step: "How many years of X?",
"Why do you want to work here?", "Are you authorized to work in the US?", custom
ATS questions, etc. This feature answers **any** of those questions automatically.

## How it works

`src/application/question_answerer.py` resolves each question through three layers,
in order:

1. **Deterministic heuristics** — fast, consistent answers for the common screening
   questions: work authorization, visa sponsorship, security clearance, years of
   experience, salary expectations, relocation, notice period / start date, contact
   and profile fields (LinkedIn, GitHub, portfolio, phone, email), and EEO/diversity
   questions (answered with privacy-preserving defaults).

2. **Your profile** — assembled from `config.py` (`USER_INFO`, `JOB_SEARCH`,
   `QUESTION_ANSWERING`) plus the extracted text of your resume.

3. **AI (OpenAI) with optional company research** — for open-ended or company-specific
   questions ("Why are you interested in this role?"). The model answers in the first
   person using only facts from your profile, grounded with the job description and
   (optionally) the company's website.

Every answer is **cached** to `data_folder/answer_cache.json` so identical questions
are answered consistently within and across runs.

## Where it runs

The answerer is wired into `JobApplier`:

- **LinkedIn Easy Apply** — `_fill_linkedin_additional_questions` runs an intelligent
  pass first; legacy heuristics only fill anything left over.
- **Indeed / ZipRecruiter** — handled by a generic, board-agnostic multi-step filler
  (`_apply_generic`) that uploads the resume, answers every question on each step, and
  advances through Continue/Next/Submit.

The form scanner detects text inputs, number inputs, textareas, dropdowns, and radio
groups, derives the question text from `<label>`, `aria-label`, placeholder, or the
surrounding form-group, then types/selects the answer with human-like behavior. Fields
that are already filled (e.g. prefilled contact info) are skipped.

## Configuration

Edit the `QUESTION_ANSWERING` block in `config.py`:

```python
QUESTION_ANSWERING = {
  "enabled": True,             # turn the feature on/off
  "research_company": True,    # use job description / company site for open-ended answers
  "authorized_to_work": True,  # legally authorized to work in the US?
  "requires_sponsorship": True,# now or in the future need visa sponsorship?
  "default_years_experience": 3,
  "desired_salary": 90000,
  "willing_to_relocate": True,
  "notice_period": "2 weeks",
  "start_date": "Immediately / 2 weeks notice",
  "gender": "Decline to self-identify",
  "race": "Decline to self-identify",
  "veteran_status": "I am not a protected veteran",
  "disability_status": "I do not wish to answer",
}
```

The AI layer requires an OpenAI API key in `AI_SETTINGS["api_key"]` (or the
`OPENAI_API_KEY` environment variable). Without a key, the heuristic + profile layers
still work; only open-ended AI answers are skipped.

## A note on honesty

The answerer is instructed to **never fabricate** credentials, employers, or degrees.
For open-ended answers it uses only facts present in your profile/resume. Review your
applications — you are responsible for the information submitted.
