# Goal: Web agent using Gemini 2.5 Flash to research cryptocurrencies and generate a short-term investment report.

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
REPORT_FILENAME = 'crypto_report.md'

@controller.action('Save crypto analysis report to Markdown file')
def save_markdown_report(report_content: str):
	"""Saves the full crypto analysis report content to a Markdown file."""
	# Define the target directory using an absolute path
	target_directory = Path(r'C:\Users\Admin\Documents\Obsidian\studyexp\Agent')
	# Ensure the directory exists
	target_directory.mkdir(parents=True, exist_ok=True)
	report_path = target_directory / REPORT_FILENAME
	try:
		with open(report_path, 'w', encoding='utf-8') as f:
			f.write(report_content)
		return f"Successfully saved crypto report to {REPORT_FILENAME}"
	except Exception as e:
		return f"Error saving report to {REPORT_FILENAME}: {e}"

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

TASK = """
You are a crypto analyst. Your goal is to research the top cryptocurrencies and produce a detailed short-term investment comparison report in Markdown format.

Follow these steps meticulously:
1.  **Identify Top Coins:** Search the web (e.g., CoinMarketCap, CoinGecko, reputable financial news sites) to identify the current top 10 cryptocurrencies by market capitalization.
2.  **Gather Data (Last 30 Days):** For each of the top 10 coins, find and summarize their price performance over the **last 30 days**. Note key trends, significant price changes (percentage), and any major news impacting them during this period.
3.  **Select Top 3 Contenders:** Based *only* on the **last 30 days** performance data and recent news/trends gathered, select the **top 3 cryptocurrencies** that appear most promising for *good short-term returns* (next 1-3 months).
4.  **Detailed Analysis & Comparison:** Generate a detailed report in **Markdown format** comparing these 3 selected coins. For each coin, include:
    *   **Name and Symbol:** (e.g., Bitcoin (BTC))
    *   **30-Day Performance Summary:** A detailed paragraph summarizing the trends, percentage changes, and key events/news found in step 2 for the **last 30 days**.
    *   **Short-Term Outlook (1-3 Months):** Your analysis of its potential, considering the recent **30-day** performance and news. Explain the factors supporting this outlook (e.g., technical indicators if found, upcoming events, market sentiment).
    *   **Rationale/Justification:** Clearly explain *why* this coin was selected as a top contender based on the **30-day** data.
5.  **Comparative Conclusion:** Add a concluding section to the report that directly compares the 3 coins, highlighting their relative strengths and weaknesses for short-term investment based on the **30-day** analysis. Briefly state which one, if any, appears slightly more favorable and why, or if they present similar risk/reward profiles.
6.  **Save Report:** Use the 'Save crypto analysis report to Markdown file' action, passing the **entire generated Markdown content** as the 'report_content' argument to save the complete report.
"""


async def main():
	agent = Agent(
		task=TASK,
		llm=llm,
		browser=browser,
		controller=controller,
		validate_output=True,
	)
	history = await agent.run(max_steps=100)


if __name__ == '__main__':
	asyncio.run(main())