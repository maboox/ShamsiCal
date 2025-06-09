# Persian Desktop Widgets

A suite of customizable desktop widgets including a multi-calendar display (Jalali, Gregorian, Hijri) with events, a quote display, and an RSS feed reader with AI-powered summarization and translation. Built with Python and PyQt6.

## Features

*   **AI-Powered RSS Summarization & Translation (via Together.AI):**
    *   Summarize full article content fetched from RSS item links using advanced AI models.
    *   Translate the generated summary into Persian.
    *   Requires a Together.AI API key (see setup instructions below).

*   **Multiple Calendar Systems:** Displays Jalali (primary), Gregorian, and Hijri dates.
*   **Event Display:** Shows daily events/holidays for Jalali dates. Events are fetched from an online API and cached locally for offline access.
    *   **Offline Caching:** Automatically caches events for ±7 days around the current date when an internet connection is available, ensuring events are viewable offline. A manual cache update option is also available in the settings menu to refresh this range on demand.
*   **Navigation:** Easily move to the next/previous day or jump back to today.
*   **Quote Box Widget:**
    *   Movable widget displaying inspirational quotes with proper transparency and rounded corners, ensuring it integrates smoothly with your desktop theme.
    *   Configurable update frequency (hourly, daily, weekly).
    *   Full quote management system for adding, editing, and deleting quotes.
    *   Selectable width presets (Narrow, Medium, Wide) with automatic height adjustment.
    *   Shares theme settings with the main widget and updates its appearance (colors, font) in real-time when the main widget's theme is changed.
*   **RSS Reader Widget:**
    *   Movable and resizable widget to display news and updates from your favorite RSS feeds.
    *   Fetches and displays RSS feed items, including title and a summary/content snippet.
    *   Easy navigation to view previous/next items within a feed, and to cycle through different added feeds.
    *   Link to open the full article in a web browser.
    *   Comprehensive feed management: Add new feeds with a name and URL, edit existing ones, or delete them.
    *   **Per-Feed Text Direction:** Select text direction (Right-to-Left or Left-to-Right) for each feed individually, ensuring correct alignment for languages like Persian and English.
    *   Configurable display width (Narrow, Medium, Wide) with automatic height adjustment.
    *   Seamlessly integrates with the main calendar's theme and font size settings, updating its appearance in real-time.
    *   All feed configurations, widget position, size, current feed, and item index are saved and restored.
*   **Customizable Appearance:**
    *   Multiple color schemes (Dark, Light, Nordic Blue, Forest Green, Warm Amber).
    *   Toggleable "boxed" style with a 3D/beveled border effect for both main widget and quote box.
    *   Five font size options that apply to both widgets.
    *   Compact mode for a minimalist view.
    *   Hover effects on buttons for better interactivity.
    *   **User Preferences:** Remembers your last used theme, style, font size, compact mode, window positions, quote settings (including list, frequency, width), RSS feed settings (including list, directions, width, current feed/item, Together.AI API token), and the visibility state of the main calendar, quote widget, and RSS widget.
*   **Draggable Interface:** Frameless window that can be moved around the screen.
*   **Cross-Platform:** Built with PyQt6.
*   **Custom Font:** You can easily change the font of the widget. Open the `shamsi_calendar_widget.pyw` file in a text editor, find the line `DEFAULT_FONT_FAMILY = "DanaFaNum"` (or similar), and replace `"DanaFaNum"` with the name of your desired font installed on your system (e.g., `"Arial"`, `"Tahoma"`).

## Requirements

To use this widget, you'll need:

*   Python (version 3.7 or newer).
*   Python libraries: `PyQt6`, `jdatetime`, `requests`, `hijri-converter`, `feedparser`, `openai`, `beautifulsoup4`, `newspaper3k`, `lxml[html_clean]`. (The setup guide below will help you install these!)

## Installation & Setup (First Time Users)

Welcome! To get the Persian Desktop Widgets running on your computer, follow these steps.

**Step 1: Get the Application Files**

You have two main ways to get the files:

*   **Option A: Using Git (Recommended for easier updates)**
    1.  If you don't have Git, you can download it from [git-scm.com](https://git-scm.com/). Git is a tool that helps manage code versions.
    2.  Open a terminal. On Windows, this can be Command Prompt, PowerShell, or Git Bash (if you installed Git with it).
    3.  Decide where you want to save the application files (e.g., your Desktop or Documents folder). Use the `cd` (change directory) command in the terminal to go to that location. For example, to go to your Desktop, you might type `cd Desktop`.
    4.  Once in your desired folder, run this command to copy (or "clone") the application files from GitHub:
        ```bash
        git clone https://github.com/maboox/ShamsiCal.git
        ```
    5.  This command creates a new folder named `ShamsiCal` containing all the application files. Now, go into this new folder by typing:
        ```bash
        cd ShamsiCal
        ```

*   **Option B: Downloading a ZIP File (Simpler if you don't know Git)**
    1.  Go to the [ShamsiCal GitHub page](https://github.com/maboox/ShamsiCal).
    2.  Click the green "<> Code" button.
    3.  In the dropdown menu, click "Download ZIP".
    4.  Save the ZIP file to your computer (e.g., in your Downloads folder).
    5.  Find the downloaded ZIP file and extract its contents. (On Windows, you can usually right-click the file and choose "Extract All...".) This will create a new folder, probably named `ShamsiCal-main`. You can rename this folder to just `ShamsiCal` if you like.
    6.  Open a terminal and use the `cd` command to navigate into this `ShamsiCal` folder. For example, if you extracted it to your Desktop and renamed it, you'd type `cd Desktop\ShamsiCal`.

**Step 2: Install Python (If you don't have it already)**

1.  This application is written in Python, so you need Python installed on your computer.
2.  To check if you have Python, open a terminal and type `python --version` or `py --version`. If you see a version number (like Python 3.9.5), and it's 3.7 or newer, you're good!
3.  If you don't have Python, or have an older version, download the latest version for Windows from the official Python website: [python.org/downloads/windows/](https://www.python.org/downloads/windows/).
4.  When installing Python, **make sure to check the box that says "Add Python to PATH" or "Add python.exe to Path"** on the first page of the installer. This is important!

**Step 3: Install Required Libraries**

1.  Make sure your terminal is still open and you are inside the `ShamsiCal` folder (from Step 1).
2.  This application uses some extra Python tools (called libraries or packages) that don't come with Python by default. The file `requirements.txt` in the `ShamsiCal` folder lists all of them.
3.  You can install all these required libraries at once by running the following command in your terminal:
    ```bash
    pip install -r requirements.txt
    ```
    (`pip` is Python's package installer. This command tells pip to read `requirements.txt` and install everything listed.)

You're all set up! Now you can run the application.

## Setting up AI Features (Together.AI API Key)

The RSS summarization and translation feature uses the Together.AI API. To use this feature, you'll need a free or paid API key from Together.AI.

1.  **Create an Account:** Go to [https://www.together.ai/](https://www.together.ai/) and sign up.
2.  **Get API Key:** Once logged in, navigate to your account settings or API keys section (usually found by clicking your profile icon or an "API Keys" link in the dashboard).
3.  **Generate Key:** Create a new API key. Make sure to copy it somewhere safe immediately, as it might not be shown again.
4.  **Add Key to Application:** When you first try to use the summarize/translate feature in the RSS widget, the application will prompt you to enter your Together.AI API key. You can also add or update it later via the "Manage RSS Feeds" dialog (accessible from the RSS widget's settings menu).

**Note:** Your API key is stored locally in the application's settings and is not shared elsewhere.

## Running the Application

1.  Open your terminal (Command Prompt, PowerShell, etc.).
2.  Make sure you are in the `ShamsiCal` directory where you put the application files. (If you just finished the setup steps, your terminal should still be in this directory. If not, use the `cd` command to navigate to it, e.g., `cd C:\Users\YourName\Desktop\ShamsiCal`).
3.  To start the Persian Desktop Widgets, run the following command:
    ```bash
    python shamsi_calendar_widget.pyw
    ```
    The calendar widget should appear on your screen! You can drag it wherever you like. Right-click on it to see settings.

## Updating the Application (For Existing Users)

If you've previously installed the widgets and want to get the latest features and fixes:

*   **If you used Git to get the files (Option A during setup):**
    1.  Open a terminal.
    2.  Navigate into your existing `ShamsiCal` folder using the `cd` command.
    3.  Run this command to download the latest changes from GitHub:
        ```bash
        git pull
        ```
    4.  After pulling the changes, it's a good idea to update the libraries too, in case new ones were added or versions changed. Run:
        ```bash
        pip install -r requirements.txt
        ```

*   **If you downloaded a ZIP file (Option B during setup):**
    1.  The easiest way is to first delete your old `ShamsiCal` folder.
        *   **Important:** Your settings (like theme, window position, custom quotes) are usually saved separately by the application in a system location, so they *should* be safe and automatically used by the new version. However, if you're concerned, you could back up the `ShamsiCal` folder before deleting it.
    2.  Follow "Step 1: Get the Application Files (Option B)" and "Step 3: Install Required Libraries" from the "Installation & Setup" section above to download and set up the new version.

After updating, you can run the application as usual with `python shamsi_calendar_widget.pyw`.

## AutoStart on Windows (Optional)

Want the calendar to start automatically when you turn on your PC?

1.  Press the `Windows Key + R` on your keyboard at the same time. This opens the Run dialog.
2.  In the Run dialog, type `shell:startup` and press Enter or click OK. This will open your Windows Startup folder in File Explorer.
3.  Now, find the `shamsi_calendar_widget.pyw` file. This is inside your `ShamsiCal` folder.
4.  You need to create a shortcut to this `shamsi_calendar_widget.pyw` file and place that shortcut into the Startup folder you just opened.
    *   One way: Right-click on `shamsi_calendar_widget.pyw` and choose "Show more options" (if on Windows 11) then "Send to > Desktop (create shortcut)". This puts a shortcut on your Desktop. Then, drag this shortcut from your Desktop into the Startup folder.
    *   Another way: With both the `ShamsiCal` folder and the Startup folder open, right-click and drag the `shamsi_calendar_widget.pyw` file from the `ShamsiCal` folder into the Startup folder. When you release the mouse button, choose "Create shortcuts here".
5.  That's it! The calendar should now launch automatically every time you log into Windows. If you want to stop it from auto-starting, just delete the shortcut from the Startup folder.
