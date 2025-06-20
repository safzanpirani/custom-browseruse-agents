# Goal: Agent to search for documentation across multiple frameworks/libraries and create a personalized reference guide.

import asyncio
import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict

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
DOCS_LIBRARY_FILE = 'technical_docs_library.json'
REFERENCE_GUIDE_FILE = 'reference_guide.md'

class CodeExample(BaseModel):
    title: str
    code: str
    explanation: Optional[str] = None
    source_url: str

class DocEntry(BaseModel):
    framework: str  # Framework or library name
    topic: str  # Topic or function name
    description: str  # Description of the topic
    code_examples: List[CodeExample] = []
    api_reference: Optional[str] = None
    source_url: str
    timestamp: str = datetime.now().isoformat()

class DocsLibrary(BaseModel):
    entries: List[DocEntry] = []
    frameworks: Dict[str, List[str]] = {}  # Framework -> list of topics
    last_updated: str = datetime.now().isoformat()

@controller.action('Load documentation library')
def load_docs_library():
    """Loads the documentation library from file."""
    try:
        if Path(DOCS_LIBRARY_FILE).exists():
            with open(DOCS_LIBRARY_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return json.dumps(data, indent=2)
        else:
            # Create empty library if it doesn't exist
            library = DocsLibrary()
            with open(DOCS_LIBRARY_FILE, 'w', encoding='utf-8') as f:
                json.dump(library.model_dump(), f, indent=2)
            return "Created new empty documentation library."
    except Exception as e:
        return f"Error loading documentation library: {e}"

@controller.action('Add documentation entry')
def add_doc_entry(entry: DocEntry):
    """Adds a new documentation entry to the library."""
    try:
        if Path(DOCS_LIBRARY_FILE).exists():
            with open(DOCS_LIBRARY_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = DocsLibrary().model_dump()
        
        # Add the new entry
        entry_dict = entry.model_dump()
        data["entries"].append(entry_dict)
        
        # Update frameworks index
        if entry.framework not in data["frameworks"]:
            data["frameworks"][entry.framework] = []
        
        if entry.topic not in data["frameworks"][entry.framework]:
            data["frameworks"][entry.framework].append(entry.topic)
        
        data["last_updated"] = datetime.now().isoformat()
        
        # Save updated library
        with open(DOCS_LIBRARY_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        return f"Successfully added documentation for {entry.framework} - {entry.topic}"
    except Exception as e:
        return f"Error adding documentation entry: {e}"

@controller.action('Generate reference guide')
def generate_reference_guide(frameworks: Optional[List[str]] = None, topics: Optional[List[str]] = None):
    """Generates a Markdown reference guide from the documentation library."""
    try:
        if not Path(DOCS_LIBRARY_FILE).exists():
            return "Documentation library doesn't exist."
        
        with open(DOCS_LIBRARY_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        entries = data["entries"]
        
        # Filter by frameworks if specified
        if frameworks:
            entries = [e for e in entries if e["framework"] in frameworks]
        
        # Filter by topics if specified
        if topics:
            entries = [e for e in entries if e["topic"] in topics]
        
        if not entries:
            return "No matching entries found for the specified filters."
        
        # Generate the markdown content
        md_content = "# Technical Reference Guide\n\n"
        md_content += f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
        
        # Table of contents
        md_content += "## Table of Contents\n\n"
        framework_groups = {}
        
        # Group entries by framework
        for entry in entries:
            framework = entry["framework"]
            if framework not in framework_groups:
                framework_groups[framework] = []
            framework_groups[framework].append(entry)
        
        # Generate TOC
        for framework, framework_entries in framework_groups.items():
            md_content += f"- [{framework}](#{framework.lower().replace(' ', '-')})\n"
            for entry in framework_entries:
                topic = entry["topic"]
                md_content += f"  - [{topic}](#{topic.lower().replace(' ', '-')})\n"
        
        md_content += "\n"
        
        # Generate content by framework
        for framework, framework_entries in framework_groups.items():
            md_content += f"## {framework}\n\n"
            
            for entry in framework_entries:
                topic = entry["topic"]
                md_content += f"### {topic}\n\n"
                md_content += f"{entry['description']}\n\n"
                
                if entry["api_reference"]:
                    md_content += "**API Reference:**\n\n"
                    md_content += f"{entry['api_reference']}\n\n"
                
                if entry["code_examples"]:
                    md_content += "**Code Examples:**\n\n"
                    for example in entry["code_examples"]:
                        md_content += f"#### {example['title']}\n\n"
                        md_content += "```\n"
                        md_content += f"{example['code']}\n"
                        md_content += "```\n\n"
                        
                        if example["explanation"]:
                            md_content += f"{example['explanation']}\n\n"
                        
                        md_content += f"*Source: [{example['source_url']}]({example['source_url']})*\n\n"
                
                md_content += f"*Source: [{entry['source_url']}]({entry['source_url']})*\n\n"
                md_content += "---\n\n"
        
        # Write to file
        with open(REFERENCE_GUIDE_FILE, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        return f"Successfully generated reference guide to {REFERENCE_GUIDE_FILE}"
    except Exception as e:
        return f"Error generating reference guide: {e}"

@controller.action('Search documentation')
def search_documentation(query: str):
    """Searches the documentation library for matching entries."""
    try:
        if not Path(DOCS_LIBRARY_FILE).exists():
            return "Documentation library doesn't exist."
        
        with open(DOCS_LIBRARY_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        entries = data["entries"]
        results = []
        
        # Simple search implementation - can be improved with better text matching
        query = query.lower()
        for entry in entries:
            if (query in entry["framework"].lower() or 
                query in entry["topic"].lower() or 
                query in entry["description"].lower()):
                results.append(entry)
        
        if not results:
            return "No matching entries found."
        
        # Format results
        result_text = f"Found {len(results)} matching entries:\n\n"
        for i, entry in enumerate(results, 1):
            result_text += f"{i}. {entry['framework']} - {entry['topic']}\n"
            result_text += f"   {entry['description'][:100]}...\n"
        
        return result_text
    except Exception as e:
        return f"Error searching documentation: {e}"

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
You are a technical documentation aggregator. Your task is to search for documentation across multiple frameworks or libraries specified below, extract relevant code examples, and create a personalized reference guide. Follow these steps:

1. Use the 'Load documentation library' action to check the current state of the documentation library.
2. For each of the frameworks/libraries in this list, search and aggregate documentation:
   - React.js (specifically hooks and state management)
   - Python FastAPI (API endpoints and authentication)
   - TensorFlow (model creation and training)

3. For each framework/library and topic:
   a. Navigate to the official documentation website
   b. Find the relevant documentation pages
   c. Extract:
      - Clear descriptions of functions/methods/concepts
      - Code examples with their explanations
      - API references
   d. Use the 'Add documentation entry' action to save each entry

4. After gathering documentation for all frameworks:
   a. Use the 'Generate reference guide' action to create a comprehensive reference guide
   b. The guide should include all code examples, descriptions, and links back to the original sources

Focus on finding practical, working code examples rather than just theoretical explanations. Look for both basic and advanced usage patterns. Ensure that each code example is complete enough to be useful on its own.

Notes:
- Format code examples with proper syntax highlighting where possible
- Include source URLs for all information to allow for future reference
- If you encounter multiple examples for the same concept, choose the clearest and most comprehensive one
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