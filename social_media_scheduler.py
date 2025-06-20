# Goal: Agent to schedule and publish content across multiple social media platforms and track engagement.

import asyncio
import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional

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
CONTENT_CALENDAR_FILE = 'content_calendar.json'
ENGAGEMENT_REPORT_FILE = 'engagement_report.json'

class SocialMediaPost(BaseModel):
    platform: str  # e.g., "Twitter", "LinkedIn", "Instagram", "Facebook"
    content: str  # The post text
    image_url: Optional[str] = None  # Optional image URL
    scheduled_time: str  # ISO format datetime string
    status: str = "scheduled"  # "scheduled", "published", "failed"
    post_url: Optional[str] = None  # URL of the published post
    engagement: Optional[dict] = None  # Engagement metrics

class ContentCalendar(BaseModel):
    posts: List[SocialMediaPost] = []
    last_updated: str = datetime.now().isoformat()

@controller.action('Load content calendar')
def load_content_calendar():
    """Loads the content calendar from file."""
    try:
        if Path(CONTENT_CALENDAR_FILE).exists():
            with open(CONTENT_CALENDAR_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return json.dumps(data, indent=2)
        else:
            # Create empty calendar if it doesn't exist
            calendar = ContentCalendar()
            with open(CONTENT_CALENDAR_FILE, 'w', encoding='utf-8') as f:
                json.dump(calendar.model_dump(), f, indent=2)
            return "Created new empty content calendar."
    except Exception as e:
        return f"Error loading content calendar: {e}"

@controller.action('Add post to calendar')
def add_post_to_calendar(post: SocialMediaPost):
    """Adds a new post to the content calendar."""
    try:
        if Path(CONTENT_CALENDAR_FILE).exists():
            with open(CONTENT_CALENDAR_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = ContentCalendar().model_dump()
        
        # Add the new post
        data["posts"].append(post.model_dump())
        data["last_updated"] = datetime.now().isoformat()
        
        # Save updated calendar
        with open(CONTENT_CALENDAR_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        return f"Successfully added post to calendar for {post.platform} scheduled at {post.scheduled_time}"
    except Exception as e:
        return f"Error adding post to calendar: {e}"

@controller.action('Update post status')
def update_post_status(platform: str, scheduled_time: str, status: str, post_url: Optional[str] = None):
    """Updates the status of a post after publishing attempt."""
    try:
        if Path(CONTENT_CALENDAR_FILE).exists():
            with open(CONTENT_CALENDAR_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            return "Content calendar doesn't exist."
        
        # Find and update the post
        updated = False
        for post in data["posts"]:
            if post["platform"] == platform and post["scheduled_time"] == scheduled_time:
                post["status"] = status
                if post_url:
                    post["post_url"] = post_url
                updated = True
                break
        
        if not updated:
            return f"No matching post found for {platform} at {scheduled_time}"
        
        # Save updated calendar
        data["last_updated"] = datetime.now().isoformat()
        with open(CONTENT_CALENDAR_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        return f"Successfully updated post status to {status}"
    except Exception as e:
        return f"Error updating post status: {e}"

@controller.action('Save engagement metrics')
def save_engagement_metrics(platform: str, post_url: str, metrics: dict):
    """Saves engagement metrics for a published post."""
    try:
        if Path(CONTENT_CALENDAR_FILE).exists():
            with open(CONTENT_CALENDAR_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            return "Content calendar doesn't exist."
        
        # Find and update the post
        updated = False
        for post in data["posts"]:
            if post["platform"] == platform and post.get("post_url") == post_url:
                post["engagement"] = metrics
                updated = True
                break
        
        if not updated:
            return f"No matching post found for {platform} at URL {post_url}"
        
        # Save updated calendar
        data["last_updated"] = datetime.now().isoformat()
        with open(CONTENT_CALENDAR_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        # Also update engagement report file
        update_engagement_report(platform, post_url, metrics)
        
        return f"Successfully saved engagement metrics for {platform} post"
    except Exception as e:
        return f"Error saving engagement metrics: {e}"

def update_engagement_report(platform: str, post_url: str, metrics: dict):
    """Internal function to update the engagement report file."""
    try:
        if Path(ENGAGEMENT_REPORT_FILE).exists():
            with open(ENGAGEMENT_REPORT_FILE, 'r', encoding='utf-8') as f:
                report = json.load(f)
        else:
            report = {"platforms": {}, "last_updated": ""}
        
        # Initialize platform if it doesn't exist
        if platform not in report["platforms"]:
            report["platforms"][platform] = {}
        
        # Add or update metrics for this post
        report["platforms"][platform][post_url] = {
            "metrics": metrics,
            "timestamp": datetime.now().isoformat()
        }
        
        report["last_updated"] = datetime.now().isoformat()
        
        # Save updated report
        with open(ENGAGEMENT_REPORT_FILE, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
    except Exception as e:
        print(f"Error updating engagement report: {e}")

# --- End Controller Setup ---

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

TASK = """
You are a social media content scheduler and publisher. Your task is to schedule and publish content across multiple platforms and track engagement. Follow these steps:

1. Use the 'Load content calendar' action to check if there are any scheduled posts.
2. For each platform (Twitter, LinkedIn, Facebook), check if there are posts scheduled that need to be published.
3. For each post that needs to be published:
   a. Navigate to the platform's login page
   b. Log in with the provided credentials
   c. Navigate to the post creation page
   d. Create and schedule the post according to the calendar
   e. Get the URL of the scheduled/published post
   f. Use the 'Update post status' action to mark the post as published or failed
4. For posts that were previously published:
   a. Navigate to each post
   b. Extract engagement metrics (likes, comments, shares, etc.)
   c. Use the 'Save engagement metrics' action to store this data

If there are no posts in the calendar, create some example posts by:
1. Thinking of 3 different posts suitable for different platforms
2. Using the 'Add post to calendar' action to add them to the calendar
3. Schedule them for appropriate times within the next week

Note: For security purposes, use these test accounts:
- Twitter: @test_account / testpassword123
- LinkedIn: test@example.com / testpassword123
- Facebook: test@example.com / testpassword123

Always respect each platform's posting guidelines and rate limits.
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