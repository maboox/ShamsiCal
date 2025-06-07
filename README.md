# PyQt Shamsi Windows Calendar Widget

A customizable desktop calendar widget, displaying Jalali (Shamsi), Gregorian, and Hijri dates with daily events. Built with Python and PyQt6.

## Features

*   **Multiple Calendar Systems:** Displays Jalali (primary), Gregorian, and Hijri dates.
*   **Event Display:** Shows daily events/holidays for Jalali dates (fetched from an online API).
*   **Navigation:** Easily move to the next/previous day or jump back to today.
*   **Quote Box Widget:**
    *   Movable, translucent widget displaying inspirational quotes.
    *   Configurable update frequency (hourly, daily, weekly).
    *   Full quote management system for adding, editing, and deleting quotes.
    *   Selectable width presets (Narrow, Medium, Wide) with automatic height adjustment.
    *   Shares theme settings with the main widget.
*   **Customizable Appearance:**
    *   Multiple color schemes (Dark, Light, Nordic Blue, Forest Green, Warm Amber).
    *   Toggleable "boxed" style with a 3D/beveled border effect for both main widget and quote box.
    *   Five font size options that apply to both widgets.
    *   Compact mode for a minimalist view.
    *   Hover effects on buttons for better interactivity.
*   **User Preferences:** Remembers your last used theme, style, font size, compact mode, window positions, quote settings (including list, frequency, width), and visibility.
*   **Draggable Interface:** Frameless window that can be moved around the screen.
*   **Cross-Platform:** Built with PyQt6.
*   **Custom Font:** You can easily change the font of the widget. Open the `shamsi_calendar_widget.pyw` file in a text editor, find the line `DEFAULT_FONT_FAMILY = "DanaFaNum"` (or similar), and replace `"DanaFaNum"` with the name of your desired font installed on your system (e.g., `"Arial"`, `"Tahoma"`).

## Requirements

To use this widget, you'll need:

*   Python (version 3.7 or newer).
*   A few Python libraries: PyQt6, jdatetime, requests, hijri-converter. (Don't worry, the setup guide below will help you install these!)

## Installation & Setup (First Time Users)

Welcome! To get the Shamsi Calendar widget running on your computer, follow these steps.

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

## Running the Application

1.  Open your terminal (Command Prompt, PowerShell, etc.).
2.  Make sure you are in the `ShamsiCal` directory where you put the application files. (If you just finished the setup steps, your terminal should still be in this directory. If not, use the `cd` command to navigate to it, e.g., `cd C:\Users\YourName\Desktop\ShamsiCal`).
3.  To start the Shamsi Calendar widget, run the following command:
    ```bash
    python shamsi_calendar_widget.pyw
    ```
    The calendar widget should appear on your screen! You can drag it wherever you like. Right-click on it to see settings.

## Updating the Application (For Existing Users)

If you've previously installed ShamsiCal and want to get the latest features and fixes:

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
