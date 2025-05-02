 # Custom browser-use Scripts

This project utilizes the [browser-use](https://github.com/browser-use/browser-use) library to automate various browser tasks using AI agents.

## Scripts

This repository contains the following scripts:

*   `crypto_agent.py`: An agent that researches the top cryptocurrencies, analyzes their 30-day performance, and generates a short-term investment comparison report saved as `crypto_report.md` in a specified directory.
*   `comfyui-gen-image.py`: An agent that interacts with a local ComfyUI instance (http://127.0.0.1:8188/) to generate an image based on a prompt and confirms completion.
*   `flight_lookup.py`: An agent that searches Goibibo.com for flight prices (specifically Hyderabad to Bangalore on May 5th, 2025) and saves the results to `flight_report.md` in the script's directory.
*   `general_web_agent.py`: A general-purpose web agent, currently configured to find and book a hotel on Booking.com according to specified criteria (family size, dates, free cancellation).
*   `lookup_jobs.py`: An agent designed to search Google Careers, read a local CV (`resume.pdf` or path from `CV_PATH`), evaluate job relevance, save findings to `jobs.csv`.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/safzanpirani/custom-browseruse-agents
    cd custom-browseruse-agents
    ```
2.  **Create a virtual environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
    ```
3.  **Install dependencies:**
    *(Assuming you have a requirements.txt file. If not, you might want to create one based on the imports in your scripts)*
    ```bash
    pip install -r requirements.txt # Or install manually: pip install browser-use langchain-google-genai python-dotenv pydantic
    ```
4.  **Set up environment variables:**
    Create a `.env` file in the root directory and add your API keys:
    ```dotenv
    GOOGLE_API_KEY=your_google_api_key_here
    # Add any other required API keys (e.g., OPENAI_API_KEY, ANTHROPIC_API_KEY if used elsewhere)
    ```
5.  **Install Playwright browsers:**
    The `browser-use` library requires Playwright browsers. Install them if you haven't already:
    ```bash
    playwright install chromium # Or other browsers as needed
    ```

## Running the Scripts

Execute the Python scripts directly:

```bash
python crypto_agent_gemini.py
python comfyui-gen-image.py
python flight_lookup.py
# etc.
```
