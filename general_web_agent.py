# Goal: A general-purpose web navigation agent for tasks like flight booking and course searching.

import asyncio
import os
import sys

# Adjust Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import SecretStr

from browser_use.agent.service import Agent
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
)

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

# TASK = """
# Find the lowest-priced one-way flight from Cairo to Montreal on February 21, 2025, including the total travel time and number of stops. on https://www.google.com/travel/flights/
# """
# TASK = """
# Browse Coursera, which universities offer Master of Advanced Study in Engineering degrees? Tell me what is the latest application deadline for this degree? on https://www.coursera.org/"""
TASK = """
Find and book a hotel in Paris with suitable accommodations for a family of four (two adults and two children) offering free cancellation for the dates of February 14-21, 2025. on https://www.booking.com/
"""


async def main():
	agent = Agent(
		task=TASK,
		llm=llm,
		browser=browser,
		validate_output=True,
		enable_memory=False,
	)
	history = await agent.run(max_steps=50)
	history.save_to_file('./tmp/history.json')


if __name__ == '__main__':
	asyncio.run(main())