# Hiring Manager Finder

To make applications more personal (and to enable optional direct follow-up emails),
the tool can try to identify the hiring manager or recruiter for a role and their
likely email address.

## How it works

The relevant utilities are:

- `src/utils/company_contact_finder.py` — locates likely hiring-manager / recruiter
  contacts for a company and role.
- `src/utils/email_pattern_finder.py` — infers a company's email pattern
  (e.g. `first.last@company.com`) and builds a probable address.

When a contact is found, `JobApplier` stores it on the job and uses it to:

- Personalize the application / cover letter to the hiring manager.
- Record the contact in `data_folder/applications/applications.csv`.
- Schedule a follow-up in `data_folder/follow_ups/follow_ups.csv`.
- Optionally send a direct email (see `EMAIL` config and `_send_direct_email`).

## Enabling / disabling

Controlled by `APPLICATION["personalize_to_hiring_manager"]` in `config.py`
(default `True`). Follow-up timing is set by `APPLICATION["follow_up_days"]`.

For direct emails, fill in the `EMAIL` section of `config.py`:

```python
EMAIL = {
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587,
  "email_address": "you@example.com",
  "email_password": "your_app_password",  # use an app password, not your main password
}
```

## A note on etiquette and privacy

Inferred emails are best-effort guesses and may be wrong. Don't spam. Respect
unsubscribe requests and local anti-spam / privacy laws (CAN-SPAM, GDPR, etc.).
