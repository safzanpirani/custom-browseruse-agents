"""
Goal: Searches for job listings, evaluates relevance based on a CV, and applies 

@dev You need to add GOOGLE_API_KEY to your environment variables.
Also you have to install PyPDF2 to read pdf files: pip install PyPDF2
"""

import csv
import os
import sys
from pathlib import Path
import logging
from typing import List, Optional
import asyncio

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from PyPDF2 import PdfReader
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, SecretStr

from browser_use import ActionResult, Agent, Controller
from browser_use.browser.context import BrowserContext
from browser_use.browser.browser import Browser, BrowserConfig

# Validate required environment variables
load_dotenv()
required_env_vars = ["GOOGLE_API_KEY"]
for var in required_env_vars:
    if not os.getenv(var):
        raise ValueError(f"{var} is not set. Please add it to your environment variables.")

logger = logging.getLogger(__name__)
# full screen mode
controller = Controller()

# NOTE: This is the path to your cv file
# Allow specifying CV path through environment variable
cv_path = os.getenv("CV_PATH")
if cv_path:
    CV = Path(cv_path)
else:
    CV = Path.cwd() / "resume.pdf"

if not CV.exists():
	raise FileNotFoundError(f'You need to set the path to your cv file in the CV variable or CV_PATH environment variable. CV file not found at {CV}')


class Job(BaseModel):
	title: str
	link: str
	company: str
	fit_score: float
	location: Optional[str] = None
	salary: Optional[str] = None


@controller.action('Save jobs to file - with a score how well it fits to my profile', param_model=Job)
def save_jobs(job: Job):
	# Create jobs.csv if it doesn't exist
	csv_path = Path.cwd() / 'jobs.csv'
	if not csv_path.exists():
		with open(csv_path, 'w', newline='') as f:
			writer = csv.writer(f)
			writer.writerow(['Title', 'Company', 'Link', 'Salary', 'Location'])
	
	with open('jobs.csv', 'a', newline='') as f:
		writer = csv.writer(f)
		writer.writerow([job.title, job.company, job.link, job.salary, job.location])

	return 'Saved job to file'


@controller.action('Read jobs from file')
def read_jobs():
	csv_path = Path.cwd() / 'jobs.csv'
	if not csv_path.exists():
		return "No jobs file exists yet."
	
	with open('jobs.csv', 'r') as f:
		return f.read()


@controller.action('Read my cv for context to fill forms')
def read_cv():
	pdf = PdfReader(CV)
	text = ''
	for page in pdf.pages:
		text += page.extract_text() or ''
	logger.info(f'Read cv with {len(text)} characters')
	return ActionResult(extracted_content=text, include_in_memory=True)


@controller.action('Navigate to a specific URL')
async def navigate_to_url(url: str, browser: BrowserContext):
	try:
		logger.info(f"Navigating to {url}")
		await browser.goto(url)
		logger.info(f"Successfully navigated to {url}")
		return ActionResult(extracted_content=f"Successfully navigated to {url}")
	except Exception as e:
		error_msg = f"Failed to navigate to {url}: {str(e)}"
		logger.error(error_msg)
		return ActionResult(error=error_msg)


@controller.action(
	'Upload cv to element - call this function to upload if element is not found, try with different index of the same upload element',
)
async def upload_cv(index: int, browser: BrowserContext):
	path = str(CV.absolute())
	dom_el = await browser.get_dom_element_by_index(index)

	if dom_el is None:
		return ActionResult(error=f'No element found at index {index}')

	file_upload_dom_el = dom_el.get_file_upload_element()

	if file_upload_dom_el is None:
		logger.info(f'No file upload element found at index {index}')
		return ActionResult(error=f'No file upload element found at index {index}')

	file_upload_el = await browser.get_locate_element(file_upload_dom_el)

	if file_upload_el is None:
		logger.info(f'No file upload element found at index {index}')
		return ActionResult(error=f'No file upload element found at index {index}')

	try:
		await file_upload_el.set_input_files(path)
		msg = f'Successfully uploaded file "{path}" to index {index}'
		logger.info(msg)
		return ActionResult(extracted_content=msg)
	except Exception as e:
		logger.debug(f'Error in set_input_files: {str(e)}')
		return ActionResult(error=f'Failed to upload file to index {index}')


browser = Browser(
	config=BrowserConfig(
		# Use default browser path for Windows (let Playwright find Chrome)
		chrome_instance_path=None,
		disable_security=True,
		headless=False,  # Set to False to see the browser window
	)
)


async def main():
	ground_task = (
		'You are a professional job finder. Follow these exact steps in order:\n'
		'1. Use the "Navigate to a specific URL" function to go to https://careers.google.com/\n'
		'2. Use the "Read my cv for context to fill forms" function to read my resume\n'
		'3. Search for ML internships on the page\n'
		'4. For each relevant position found, save it to the jobs file with a fit score\n'
	)
	tasks = [
		ground_task,
		# Add other companies as separate tasks if needed
		# 'Navigate to https://jobs.apple.com/ and search for ML internships'
	]
	model = ChatGoogleGenerativeAI(
		model="gemini-2.5-flash-preview-04-17",
		google_api_key=SecretStr(os.getenv('GOOGLE_API_KEY', '')),
		temperature=0.2,  # Lower temperature for more consistent responses
	)

	# Initialize browser properly
	try:
		logger.info("Initializing browser...")
		# Browser is already initialized - don't use async with
		
		agents = []
		for task in tasks:
			agent = Agent(task=task, llm=model, controller=controller, browser=browser)
			agents.append(agent)
		
		logger.info("Starting agents...")
		await asyncio.gather(*[agent.run() for agent in agents])
	except Exception as e:
		logger.error(f"Error during execution: {str(e)}")
		raise


if __name__ == "__main__":
	asyncio.run(main())