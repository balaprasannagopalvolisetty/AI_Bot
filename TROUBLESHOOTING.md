# Troubleshooting Guide

This guide addresses common issues you might encounter when using the AI Job Application Assistant.

## Browser Automation Issues

### Chrome Driver Not Found

**Symptoms:** Error message about ChromeDriver not being found or executable.

**Solutions:**
1. Install the webdriver-manager package: `pip install webdriver-manager`
2. Make sure Chrome is installed and up to date
3. Try running with `"headless": False` in config.py to see what's happening

### Browser Crashes or Freezes

**Symptoms:** The Chrome browser crashes, freezes, or closes unexpectedly.

**Solutions:**
1. Update Chrome to the latest version
2. Increase the timeout value in config.py: `"timeout": 60`
3. Add more memory to the browser: Add `options.add_argument("--disable-dev-shm-usage")` in job_applier.py
4. Reduce the number of applications in one session

## LinkedIn Authentication Issues

### CAPTCHA or Security Verification

**Symptoms:** LinkedIn shows a CAPTCHA or security verification screen.

**Solutions:**
1. Run in supervised mode: `python main.py --supervised`
2. Log in to LinkedIn manually first, then run the application
3. Reduce the frequency of applications
4. Use a different IP address or network

### Login Failures

**Symptoms:** Cannot log in to LinkedIn, or login appears successful but job searches fail.

**Solutions:**
1. Verify your LinkedIn credentials in config.py
2. Check if your LinkedIn account has two-factor authentication enabled
3. Try logging in manually and check for any account restrictions
4. Wait 24 hours and try again (LinkedIn may temporarily restrict automated logins)

## Resume and Cover Letter Issues

### Resume Not Found

**Symptoms:** Error message about resume file not being found.

**Solutions:**
1. Verify the path in config.py: `"resume_path": "data_folder/resume.pdf"`
2. Make sure the resume file exists in the specified location
3. Check file permissions

### Resume Parsing Errors

**Symptoms:** Resume customization fails or produces poor results.

**Solutions:**
1. Make sure your resume is in PDF, DOCX, or TXT format
2. Ensure your resume has clear section headers for skills and projects
3. If using PDF, ensure it's not scanned or image-based
4. Try converting your resume to a different format

## API Key Issues

### OpenAI API Key Errors

**Symptoms:** Resume customization or cover letter generation fails with API key errors.

**Solutions:**
1. Verify your OpenAI API key in config.py
2. Check that you have billing set up on your OpenAI account
3. If you get rate limit errors, reduce the number of applications per day
4. Try using a different model: Change `"model": "gpt-3.5-turbo"` in config.py

## Application Form Issues

### Cannot Find Apply Button

**Symptoms:** The application fails with an error about not finding the Apply button.

**Solutions:**
1. Run in supervised mode: `python main.py --supervised`
2. Check if the job listing is still active
3. Some jobs may require applying on the company website instead of LinkedIn

### Form Fields Not Filled Correctly

**Symptoms:** The application form is not filled out correctly or completely.

**Solutions:**
1. Run in supervised mode to see what's happening: `python main.py --supervised`
2. Some forms have custom fields that the tool may not recognize
3. Be prepared to intervene manually for complex application forms

## H1B Sponsorship Issues

### H1B Data Not Found

**Symptoms:** H1B sponsorship information is not available or inaccurate.

**Solutions:**
1. Update the H1B database: `python update_h1b_database.py`
2. Some companies may sponsor H1B visas but not be in the database
3. Verify sponsorship information on the company's website or career page

## Performance Issues

### Application Process Is Too Slow

**Symptoms:** The application process takes a long time to complete.

**Solutions:**
1. Reduce the number of job boards in config.py
2. Focus on specific job titles and locations
3. Increase the timeout value in config.py: `"timeout": 60`
4. Run the application during off-peak hours

### Too Many Failed Applications

**Symptoms:** Many applications fail to complete successfully.

**Solutions:**
1. Run in supervised mode: `python main.py --supervised`
2. Focus on LinkedIn "Easy Apply" jobs
3. Reduce the complexity of your search criteria
4. Check the application logs for specific error patterns

