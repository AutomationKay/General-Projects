# Twitch Activity Automation

This Python script demonstrates automation of browser interactions through Google Chrome using pyautogui. It refreshes pages, switches tabs, moves the mouse randomly, clicks at specified coordinates, and types randomized emotes in a continuous loop. 


## Features
Randomized delays between actions to simulate human behavior.

Page refresh via hotkey (Ctrl+R).

Tab switching via hotkey (Ctrl+Tab).

Random mouse movements across the screen.

Clicking at defined coordinates (e.g., a chat box).

Typing randomized text (selecting from a list of “emotes”), with per-character randomized delays.

Logging of each step (with timestamps) into a log file (chrome_script.log) for debugging and audit.

Infinite loop structure to run continuously until manually stopped.

## Prerequisites
Python 3.9+

The following Python packages:

pyautogui

Operating system where pyautogui can control the mouse/keyboard (Windows/macOS/Linux with GUI).

Appropriate permissions/settings to allow automated control of mouse/keyboard.

Terminal or environment for running the script.

## Installation
Clone or download this repository to your local machine.

Create a virtual environment:

bash
Copy
Edit
python3 -m venv venv
source venv/bin/activate     # macOS/Linux
venv\Scripts\activate        # Windows
Install dependencies:

bash
Copy
Edit
pip install pyautogui
Note: On some systems, pyautogui may require additional dependencies (e.g., python3-tk on Linux). Follow any prompts or refer to the PyAutoGUI documentation as needed.

## Configuration
1. Coordinates:
* The script uses hard-coded coordinates for clicking (e.g., chat_box_x = 2322, chat_box_y = 1322).
* Adjust these to match your display and target element. You can use tools like screenshot with cursor position or a small helper script that prints mouse position.

2. Emotes list:
* By default, the script uses a list of strings (e.g., "Dancingdragon", "Eazy", etc.).
* Modify the emotes list to include any words or phrases you want the script to type.

3. Delay ranges:
* random_delay(min_ms, max_ms) is called with millisecond ranges (e.g., 2000, 4000 for 2–4 seconds).
* Tune these ranges depending on desired pacing and system performance.

4. Log file:
*Default log file is chrome_script.log in the working directory.
* You can change filename or log level in the logging.basicConfig(...) call at the top.

5. Loop control:
* The script runs in an infinite while True loop.
* To stop, you can press Ctrl+C in the terminal or otherwise terminate the process.

## Usage
Open your browser (e.g., Google Chrome) and navigate to the page where you want automation (e.g., a chat interface).

Position the window so that the target elements align with the configured coordinates.

Run the script:

bash
Copy
Edit
python chrome_automation.py

The script will:
* Wait a random delay.
* Refresh the page.
* Wait for page load (randomized).
* Move mouse randomly.
* Click at the chat box coordinates (twice to ensure focus).
* Select a random set of emotes and type them with human-like delays.
* Wait again, then switch to next tab, etc.
* Monitor chrome_script.log for detailed timestamps and action records. This helps verify that actions occurred as expected or troubleshoot issues.

## Logging
All key actions and chosen delays/coordinates are logged with timestamps:

File: chrome_script.log

Format: YYYY-MM-DD HH:MM:SS,fff - message

Use the log to:
* Verify correct timing and order.
* Debug coordinate mismatches.
* Audit script behavior over time.
