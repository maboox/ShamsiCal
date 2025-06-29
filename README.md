# ShamsiCal Persian Desktop Widgets

A customizable desktop widget suite centered around a multi-calendar display (Jalali, Gregorian, Hijri) with daily events. It also includes an optional RSS feed reader with AI-powered summarization/translation, a quote display widget, and a note-taking system. Built with Python and PyQt6.

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

*   **Note Manager:**
    *   Tabbed note-taking interface with rich text formatting.
    *   Create to-do lists with interactive checkboxes.
    *   Format text (bold, italic, underline) and create bulleted or numbered lists.
    *   Notes are automatically saved and persist between sessions.
    *   Consistent theming with the main application.
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

### Option 1: Standalone Executable (Recommended for most users)

1. **Download the Executable:**
   * Go to the [Releases](https://github.com/maboox/ShamsiCal/releases) page on GitHub
   * Download the latest `ShamsiCalendar.zip` file
   * Extract the ZIP file to a location of your choice
   * Double-click `ShamsiCalendar.exe` to run the application

### Option 2: From Source Code (For developers or advanced users)

1. **Get the Code:**
   * Clone: `git clone https://github.com/maboox/ShamsiCal.git`
   * Or download and extract the ZIP from the GitHub project page
2. **Navigate to Directory:** `cd ShamsiCal`
3. **Install Python (if needed):**
   * Download from [python.org](https://www.python.org/). Ensure Python is added to PATH
4. **Install Dependencies:** `pip install -r requirements.txt`
5. **Run the Application:** `python shamsi_calendar_widget.pyw`

## AI Feature Setup (for RSS Reader - Optional)

The AI summarization/translation for the RSS reader uses the Together.AI API.

1.  **Sign Up & Get API Key:** Visit [together.ai](https://www.together.ai/), create an account, and generate an API key.
2.  **Add Key to Application:**
    *   You'll be prompted for the key when first using the AI feature in the RSS widget.
    *   Or, add/update it via the "Manage RSS Feeds" dialog (from RSS widget's context menu).
    *   The key is stored locally.

## Running the Application

### For Standalone Executable Users
Simply double-click the `ShamsiCalendar.exe` file you extracted from the ZIP file. The main calendar widget will appear.

### For Source Code Users
In the `ShamsiCal` directory, run:
```bash
python shamsi_calendar_widget.pyw
```

Once running, right-click on the calendar widget to access settings and to show/hide other widgets (notes, RSS reader, quotes).

## Auto-Start on Windows (Optional)

### For Standalone Executable Users
1. Press `Windows Key + R`, type `shell:startup`, press Enter.
2. Create a shortcut to `ShamsiCalendar.exe` and place it in the Startup folder.

### For Source Code Users
1. Press `Windows Key + R`, type `shell:startup`, press Enter.
2. Create a shortcut to `shamsi_calendar_widget.pyw` (in your `ShamsiCal` folder) and place it in the Startup folder.
3. Alternatively, create a batch file (`.bat`) with the command `python path\to\shamsi_calendar_widget.pyw` and place it in the Startup folder.

## Customization Limitations with Executable Version

While the standalone executable provides full functionality, some deep customizations require access to the source code:

- **Font Family**: The executable uses the default font family. To change it, you need the source code version.
- **Custom Icons**: Adding or changing icons requires rebuilding from source.
- **Code-Level Changes**: Any modifications to the underlying code require the source version.

If you need these customizations, please use the source code installation method described above.

## Building the Executable (For Developers)

If you want to build the standalone executable yourself:

1. Make sure you have PyInstaller installed: `pip install pyinstaller`
2. Run the build script: `python build_exe.py`
3. The executable will be created in the `dist` folder
4. To create a release:
   * Compress the executable into a ZIP file
   * Go to your GitHub repository
   * Click on 'Releases' > 'Create a new release'
   * Upload the ZIP file as a release asset

---
