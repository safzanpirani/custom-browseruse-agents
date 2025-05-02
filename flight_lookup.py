# Goal: Agent to search Goibibo for flight prices using Gemini 2.5 Flash and save the report.

import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

# Adjust Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, SecretStr
from browser_use import Agent, Controller, ActionResult
from browser_use.browser.browser import Browser, BrowserConfig, BrowserContextConfig
from browser_use.browser.context import BrowserContextWindowSize

# Load environment variables
load_dotenv()

# Validate required environment variables
required_env_vars = ["GOOGLE_API_KEY"]
for var in required_env_vars:
	if not os.getenv(var):
		raise ValueError(f"{var} is not set. Please add it to your environment variables.")

# Set LLM to Google Generative AI
llm = ChatGoogleGenerativeAI(
	model="gemini-2.5-flash-preview-04-17",
	google_api_key=SecretStr(os.getenv('GOOGLE_API_KEY', '')),
	temperature=0.2,
	reasoning_effort=None
)

# --- Controller Setup ---
controller = Controller()
# Save the report in the same directory as the script
REPORT_FILENAME = 'flight_report.md'

@controller.action('Save flight search results to Markdown file')
def save_flight_report(report_content: str):
	"""Saves the flight search results report content (including title) to a Markdown file."""
	# Calculate the path relative to the current script file
	report_path = Path(__file__).parent / REPORT_FILENAME
	try:
		# Ensure the directory exists (parent directory will be the script's directory)
		report_path.parent.mkdir(parents=True, exist_ok=True)
		with open(report_path, 'w', encoding='utf-8') as f:
			f.write(report_content)
		return f"Successfully saved flight report to {report_path.resolve()}"
	except Exception as e:
		return f"Error saving report to {report_path.resolve()}: {e}"

# --- End Controller Setup ---

browser = Browser(
	config=BrowserConfig(
		headless=False,  # This is True in production
		disable_security=True,
		new_context_config=BrowserContextConfig(
			disable_security=True,
			minimum_wait_page_load_time=1,  # 3 on prod
			maximum_wait_page_load_time=10,  # 20 on prod
			# no_viewport=True,
			browser_window_size=BrowserContextWindowSize(width=1280, height=1100),
			# trace_path='./tmp/web_voyager_agent',
		),
	)
)

# --- Updated TASK ---
TASK = """
Use goibibo.com to find the price for a one-way flight from Hyderabad (HYD) to Bangalore (BLR) for 1 adult departing on May 5th, 2025.

**Instructions:**
1.  Navigate to https://www.goibibo.com/flights/
2.  Input 'Hyderabad' as the origin city and select it.
3.  Input 'Bangalore' as the destination city and select it.
4.  Select the departure date as May 5th, 2025. Ensure you navigate the calendar correctly to select this future date.
5.  Verify that the traveler count is set to 1 adult.
6.  Initiate the flight search.
7.  Once the results load, identify the lowest price listed for a one-way flight on May 5th, 2025.
8.  Create a brief report stating the origin, destination, date, number of adults, and the lowest flight price found.
9.  Use the 'Save flight search results to Markdown file' action to save this report.
"""
# --- End Updated TASK ---

async def main():
	agent = Agent(
		task=TASK,
		llm=llm,
		browser=browser,
		controller=controller,
		validate_output=True,
	)
	history = await agent.run(max_steps=50)
	# history.save_to_file('./tmp/history.json') # Optional: keep saving history

if __name__ == '__main__':
	asyncio.run(main())