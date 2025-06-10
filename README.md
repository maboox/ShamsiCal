# ShamsiCal Persian Desktop Widgets

A customizable desktop widget suite centered around a multi-calendar display (Jalali, Gregorian, Hijri) with daily events. It also includes an optional RSS feed reader with AI-powered summarization/translation and a quote display widget. Built with Python and PyQt6.

## Core Features

*   **Multi-Calendar Display:**
    *   Primary Jalali calendar with corresponding Gregorian and Hijri dates.
    *   Displays daily events and holidays for Jalali dates (events are fetched online and cached for offline use).
    *   Easy navigation: next/previous day, jump to today.
*   **Customizable Appearance:**
    *   Multiple color schemes and font size options.
    *   Toggleable "boxed" style for a 3D effect.
    *   Compact mode for a minimalist view.
    *   Draggable, frameless windows.
    *   All preferences (theme, positions, etc.) are saved.
    *   **Change Application Font:** To change the font used throughout the application, open the `shamsi_calendar_widget.pyw` file in a text editor. Find the line `DEFAULT_FONT_FAMILY = "DanaFaNum"` (or similar) and replace `"DanaFaNum"` with the name of your desired font installed on your system (e.g., `"Arial"`, `"Tahoma"`).

## Additional Widgets (Optional)

*   **RSS Feed Reader:**
    *   Display news from your favorite RSS feeds.
    *   Manage multiple feeds with per-feed text direction (RTL/LTR).
    *   **AI-Powered Summarization & Translation (via Together.AI):** Optionally summarize and translate (to Persian) full article content. Requires a Together.AI API key (see setup).
*   **Quote Display Widget:**
    *   Shows inspirational quotes with configurable update frequency and width.

## Requirements

*   Python 3.7+
*   Dependencies listed in `requirements.txt`

## Installation

1.  **Get the Code:**
    *   Clone: `git clone https://github.com/maboox/ShamsiCal.git`
    *   Or download and extract the ZIP from the GitHub project page.
2.  **Navigate to Directory:** `cd ShamsiCal`
3.  **Install Python (if needed):**
    *   Download from [python.org](https://www.python.org/). Ensure Python is added to PATH.
4.  **Install Dependencies:** `pip install -r requirements.txt`

## AI Feature Setup (for RSS Reader - Optional)

The AI summarization/translation for the RSS reader uses the Together.AI API.

1.  **Sign Up & Get API Key:** Visit [together.ai](https://www.together.ai/), create an account, and generate an API key.
2.  **Add Key to Application:**
    *   You'll be prompted for the key when first using the AI feature in the RSS widget.
    *   Or, add/update it via the "Manage RSS Feeds" dialog (from RSS widget's context menu).
    *   The key is stored locally.

## Running the Application

In the `ShamsiCal` directory, run:
```bash
python shamsi_calendar_widget.pyw
```
The main calendar widget will appear. Right-click it for settings and to show/hide other widgets.

## Auto-Start on Windows (Optional)

1.  Press `Windows Key + R`, type `shell:startup`, press Enter.
2.  Create a shortcut to `shamsi_calendar_widget.pyw` (in your `ShamsiCal` folder) and place it in the Startup folder.

---
