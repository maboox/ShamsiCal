# PyQt Shamsi Windows Calendar Widget

A customizable desktop calendar widget, displaying Jalali (Shamsi), Gregorian, and Hijri dates with daily events. Built with Python and PyQt6.

## Features

* **Multiple Calendar Systems:** Displays Jalali (primary), Gregorian, and Hijri dates.
* **Event Display:** Shows daily events/holidays for Jalali dates (fetched from an online API).
* **Navigation:** Easily move to the next/previous day or jump back to today.
* **Customizable Appearance:**
    * Multiple color schemes (Dark, Light, Nordic Blue, Forest Green, Warm Amber).
    * Toggleable "boxed" style with a 3D/beveled border effect for date elements.
    * Five font size options.
    * Compact mode for a minimalist view.
    * Hover effects on buttons for better interactivity.
* **User Preferences:** Remembers your last used theme, style, font size, compact mode, and window position.
* **Draggable Interface:** Frameless window that can be moved around the screen.
* **Cross-Platform:** Built with PyQt6.

## Requirements

* Python 3.7 or newer
* PyQt6
* jdatetime
* requests
* hijri-converter

## Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/maboox/ShamsiCal.git
    cd ShamsiCal
    ```

2.  **Create a virtual environment (optional):**
    ```bash
    python -m venv venv
    ```
    Activate it:
    * Windows: `.\venv\Scripts\activate`
    * macOS/Linux: `source venv/bin/activate`

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Running the Application

Once the setup is complete, run the widget using:

```bash
python shamsi_calendar_widget.pyw
```

## AutoStart

You can put the pyw file inside the %Startup% folder of windows so it'll be autorun whenever you start your pc
