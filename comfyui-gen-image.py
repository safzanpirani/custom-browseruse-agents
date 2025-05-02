# Goal: Agent to interact with ComfyUI and generate an image, to confirm that ComfyUI is live,  uses Gemini 2.5 Flash.

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
from browser_use import Agent
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

# --- Removed Controller Setup ---
# controller = Controller()
# REPORT_FILENAME = 'crypto_report.md'
# @controller.action(...)
# def save_markdown_report(...):
# ...
# --- End Removed Controller Setup ---


browser = Browser(
	config=BrowserConfig(
		headless=False,
		disable_security=True,
		new_context_config=BrowserContextConfig(
			disable_security=True,
			minimum_wait_page_load_time=1,
			maximum_wait_page_load_time=10,
			browser_window_size=BrowserContextWindowSize(width=1280, height=1100),
		),
	)
)

# --- Updated TASK ---
TASK = """
Navigate to the ComfyUI interface at http://127.0.0.1:8188/ and generate an image, ensuring it completes.

**Instructions:**
1.  Navigate to the ComfyUI URL: http://127.0.0.1:8188/
2.  Locate the default positive prompt input area (usually labeled 'Clip Text Encode (Prompt)').
3.  Enter a simple positive prompt, for example: "`a photorealistic cat sitting on a grassy hill at sunset`".
4.  Locate and click the '**Run**' button to queue the prompt.
5.  **Wait and Verify Completion:** After clicking '**Run**', carefully observe the UI. Wait for up to 60 seconds (or longer if needed for complex generations). Look for specific signs that the generation has finished:
    *   **Primary Check:** An image appears in the final output node (e.g., a node labeled 'Save Image' or 'Preview Image').
    *   **Secondary Check:** Look for any other visual indicators of completion, such as progress bars finishing, status messages changing to 'idle' or 'completed', or nodes changing color/highlighting to indicate they are finished.
6.  Report whether you observed the image appear in the output node and/or other clear visual signs of successful image generation completion within the expected time frame.
"""
# --- End Updated TASK ---


async def main():
	agent = Agent(
		task=TASK,
		llm=llm,
		browser=browser,
		# Removed controller argument
		validate_output=True,
	)
	history = await agent.run(max_steps=50) # Adjust max_steps if needed
	# You might want to print the history to see the agent's final report
	print(history)


if __name__ == '__main__':
	asyncio.run(main())