# AI Job Application Assistant

An automated tool to search for jobs and apply to them with human-like behavior, including an AI-powered engine that answers any question an application form throws at you.

## Features

- Scrapes job listings from **LinkedIn, Indeed, and ZipRecruiter**
- Filters jobs based on your preferences (titles, keywords, location, salary, experience level)
- **Intelligently answers application-form questions** using AI + your profile + company research (see `README_QUESTION_ANSWERING.md`)
- Automatically applies to jobs with human-like behavior
- Customizes resumes and cover letters for each job (OpenAI)
- Filters for companies that sponsor **H1B visas** (see `README_H1B_FEATURE.md`)
- Finds hiring-manager contact details (see `README_HIRING_MANAGER_FINDER.md`)
- Simulates human-like interactions (typing, scrolling, delays) to reduce detection

## Requirements

- Python 3.8 or higher
- Google Chrome browser
- ChromeDriver (installed automatically via `webdriver-manager`)
- An OpenAI API key (for resume/cover-letter customization and AI form answers)

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/balaprasannagopalvolisetty/AI_Bot.git
   cd AI_Bot
   ```

2. **(Recommended) create a virtual environment:**

   ```bash
   python -m venv venv
   source venv/bin/activate        # macOS / Linux
   venv\Scripts\activate           # Windows
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Add your resume** to `data_folder/resume.pdf` (or update `USER_INFO["resume_path"]` in `config.py`).

5. **Configure** `config.py`:
   - `USER_INFO` — your name, email, phone, LinkedIn, GitHub, resume path
   - `AI_SETTINGS["api_key"]` — your OpenAI API key (or set the `OPENAI_API_KEY` env var)
   - `LINKEDIN` — your LinkedIn login (only needed for LinkedIn Easy Apply)
   - `QUESTION_ANSWERING` — answers/defaults used for screening questions
   - `JOB_SEARCH` — job titles, locations, keywords, salary, filters

## Usage

Run with the settings from `config.py`:

```bash
python main.py
```

Or override settings from the command line:

```bash
python main.py --linkedin --indeed --job-titles "Security Analyst" "SOC Analyst" \
  --locations "Remote" "New York, NY" --max-applications 10 --headless
```

Common flags: `--linkedin`, `--indeed`, `--ziprecruiter`, `--job-titles`, `--locations`,
`--keywords`, `--exclude-keywords`, `--max-applications`, `--h1b-only`, `--headless`.

You'll be shown a configuration summary and a list of matched jobs, then asked to confirm
before any applications are submitted.

## Configuration reference

| Section | Purpose |
| --- | --- |
| `USER_INFO` | Your contact details and resume path |
| `JOB_SEARCH` | Titles, locations, keywords, salary, daily limit, LinkedIn filters |
| `JOB_BOARDS` | Which boards to search |
| `APPLICATION` | Resume/cover-letter customization, follow-ups, hiring-manager personalization |
| `AI_SETTINGS` | OpenAI model, API key, resume-match threshold |
| `QUESTION_ANSWERING` | Defaults for screening questions (work auth, sponsorship, salary, etc.) |
| `BROWSER` | Headless mode, timeout, user agent |
| `LOGGING` | Log level and log file |
| `EMAIL` / `LINKEDIN` | Credentials for follow-ups and LinkedIn login |

## Project structure

```
main.py                         # Entry point / orchestration
config.py                       # All settings
src/job_boards/                 # LinkedIn, Indeed, ZipRecruiter scrapers
src/application/
  job_applier.py                # Applies to jobs; fills forms
  question_answerer.py          # AI form-question answering engine (NEW)
  cover_letter_generator.py     # AI cover letters
  resume_customizer.py          # AI resume tailoring
src/utils/
  ai_client.py                  # Shared OpenAI (v1+) client (NEW)
  h1b_checker.py                # H1B sponsor detection
  ...
src/filters/                    # Job filtering
```

## Disclaimer

This tool automates interactions with third-party job boards. Automating LinkedIn/Indeed/etc.
may violate their Terms of Service. Use responsibly, at your own risk, and review every
application before relying on automated submission. Always provide truthful information on
applications — the question answerer is configured to never fabricate credentials.

## Troubleshooting

See `TROUBLESHOOTING.md`.
