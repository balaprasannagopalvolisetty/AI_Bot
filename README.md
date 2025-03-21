# AI Job Application Assistant

An automated tool that helps you find and apply to jobs that match your skills and preferences, with special features for finding H1B visa sponsors and hiring manager contacts.

## How the Automated Application Works

1. **Direct Application**: The tool uses Selenium (a browser automation tool) to:
   - Log into your LinkedIn account using the credentials in config.py
   - Search for jobs matching your criteria
   - Click the "Apply" button on job listings
   - Fill out application forms with your information
   - Upload your customized resume and cover letter
   - Submit the application

2. **Data Used for Applications**:
   - Your name, email, phone number from the config file
   - Your customized resume (tailored to each job)
   - A generated cover letter specific to each position
   - Any additional information from your USER_INFO section

## Important Limitations

1. **"Easy Apply" Only**: The tool works best with LinkedIn "Easy Apply" jobs where the application process is streamlined. Complex multi-page applications may not work properly.

2. **Form Variations**: LinkedIn application forms vary widely:
   - Some require just a resume upload
   - Others ask additional questions
   - Some have custom fields the tool might not recognize

3. **CAPTCHA Challenges**: LinkedIn may present CAPTCHA challenges or other security measures that can interrupt the automation.

4. **Account Restrictions**: LinkedIn may temporarily restrict accounts that submit too many applications in a short period.

5. **Additional Questions**: The tool cannot reliably answer custom screening questions that require specific responses.

## Recommended Approach

For the most reliable experience:

1. **Start with Supervision**: Run the tool with `"headless": False` in your config so you can see what's happening and intervene if needed.

2. **Start Small**: Begin with a small number of applications (3-5) to test how it works with your account and resume.

3. **Set Reasonable Limits**: Keep `max_applications_per_day` to a reasonable number (10-15) to avoid triggering LinkedIn's automated systems.

4. **Be Ready to Intervene**: For applications that require additional information or custom questions, be prepared to take over manually.

5. **Check Application Status**: Regularly check your LinkedIn account to verify which applications were successfully submitted.

The tool is designed to automate much of the tedious work of job applications, but it's not perfect and works best as a semi-automated assistant rather than a fully hands-off solution. You should monitor its operation, especially during the first few applications, to ensure it's working correctly with your specific data and target jobs.

## Prerequisites

1. **Python Installation**: Make sure you have Python 3.8+ installed
2. **Chrome Browser**: Required for web automation
3. **ChromeDriver**: Required for Selenium (will be installed automatically)
4. **OpenAI API Key**: Required for resume customization and cover letter generation

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/AI_JobApplier.git
cd AI_JobApplier

