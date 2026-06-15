# H1B Sponsor Filtering

This tool can restrict applications to companies that are known to sponsor H1B visas,
which is useful if you require visa sponsorship.

## How it works

H1B detection lives in `src/utils/h1b_checker.py` (with supporting logic in
`src/utils/h1b_sponsor_checker.py`). For every scraped job it:

1. Checks the **company name** against a list/dataset of known H1B sponsors.
2. Scans the **job description** for sponsorship signals and for negative signals such
   as "no sponsorship" / "must be authorized without sponsorship".

Jobs that pass are kept; the rest are filtered out before the apply step. In `main.py`
this runs automatically:

```python
h1b_checker = H1BChecker()
if h1b_checker.is_h1b_sponsor(company_name, job_description) or \
   h1b_checker.check_job_for_h1b_keywords(job):
    job["sponsors_h1b"] = True
    h1b_jobs.append(job)
```

## Enabling / disabling

Controlled by `JOB_SEARCH["filter_h1b_sponsors"]` in `config.py` (default `True`).
You can also force it on from the command line:

```bash
python main.py --h1b-only
```

If no H1B-sponsoring jobs are found, the run stops with a message so you can widen your
search parameters.

## Related setting

Make sure `QUESTION_ANSWERING["requires_sponsorship"]` reflects your situation so the
form answerer responds to sponsorship questions consistently with this filter.
