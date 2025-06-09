from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QPushButton, QMenu, QGraphicsDropShadowEffect, QInputDialog,
    QDialog, QListWidget, QLineEdit, QDialogButtonBox, QListWidgetItem,
    QSizePolicy, QStyle
)
from PyQt6.QtGui import QFont, QIcon, QAction, QColor, QActionGroup, QPainter, QBrush, QPen
from PyQt6.QtCore import Qt, QPoint, QSettings, QTimer, QDateTime # Removed QSize as it's not used
import jdatetime
import random
import time
import requests
from hijri_converter import Gregorian
from rss_reader_widget import RSSReaderWidget, RSS_BOX_WIDTHS, DEFAULT_RSS_BOX_WIDTH_KEY, ManageRSSFeedsDialog
import sys
import json
import os
import types

DEFAULT_FONT_FAMILY = "DanaFaNum"
EVENTS_CACHE_FILE = "events_cache.json"

weekday_fa = {'Saturday':'شنبه','Sunday':'یک‌شنبه','Monday':'دوشنبه','Tuesday':'سه‌شنبه','Wednesday':'چهارشنبه','Thursday':'پنج‌شنبه','Friday':'جمعه'}
months_fa = {'Farvardin':'فروردین','Ordibehesht':'اردیبهشت','Khordad':'خرداد','Tir':'تیر','Mordad':'مرداد','Shahrivar':'شهریور','Mehr':'مهر','Aban':'آبان','Azar':'آذر','Dey':'دی','Bahman':'بهمن','Esfand':'اسفند'}
hijri_months_fa = {1:'محرم',2:'صفر',3:'ربیع‌الاول',4:'ربیع‌الثانی',5:'جمادی‌الاول',6:'جمادی‌الثانی',7:'رجب',8:'شعبان',9:'رمضان',10:'شوال',11:'ذوالقعده',12:'ذوالحجه'}

color_schemes = {
    'Dark': {
        'name_fa': 'تیره', 'widget_bg': QColor(30,30,30,210), 'widget_text': QColor("white"),
        'box_bg': QColor(50,50,50,200), 'box_text': QColor(220,220,220), 'box_border': QColor(80,80,80),
        'box_bg_hover': QColor(70,70,70,210), # Hover for boxed buttons
        'flat_hover_bg': QColor(255,255,255,25), # Hover for flat (non-boxed) buttons
        'menu_bg': QColor(45,45,45,245), 'menu_text': QColor(220,220,220), 'menu_border': QColor(60,60,60),
        'menu_selected_bg': QColor(0,120,215), 'menu_selected_text': QColor("white"),
    },
    'Light': {
        'name_fa': 'روشن', 'widget_bg': QColor(245,245,245,220), 'widget_text': QColor("black"),
        'box_bg': QColor(220,220,220,200), 'box_text': QColor(40,40,40), 'box_border': QColor(180,180,180),
        'box_bg_hover': QColor(205,205,205,210),
        'flat_hover_bg': QColor(0,0,0,20),
        'menu_bg': QColor(245,245,245,245), 'menu_text': QColor(30,30,30), 'menu_border': QColor(200,200,200),
        'menu_selected_bg': QColor(0,120,215), 'menu_selected_text': QColor("white"),
    },
    'Nordic Blue': {
        'name_fa':'آبی نوردیک','widget_bg':QColor(46,52,64,225),'widget_text':QColor(216,222,233),
        'box_bg':QColor(59,66,82,210),'box_text':QColor(229,233,240),'box_border':QColor(76,86,106),
        'box_bg_hover':QColor(76,86,106,220),
        'flat_hover_bg':QColor(216,222,233,25),
        'menu_bg':QColor(59,66,82,245),'menu_text':QColor(216,222,233),'menu_border':QColor(76,86,106),
        'menu_selected_bg':QColor(94,129,172),'menu_selected_text':QColor(230,230,230),
    },
    'Forest Green': {
        'name_fa':'سبز جنگلی','widget_bg':QColor(42,72,46,225),'widget_text':QColor(210,203,185),
        'box_bg':QColor(52,82,56,210),'box_text':QColor(210,203,185),'box_border':QColor(80,110,80),
        'box_bg_hover':QColor(62,92,66,220),
        'flat_hover_bg':QColor(210,203,185,25),
        'menu_bg':QColor(52,82,56,245),'menu_text':QColor(210,203,185),'menu_border':QColor(80,110,80),
        'menu_selected_bg':QColor(100,130,100),'menu_selected_text':QColor(230,230,230),
    },
    'Warm Amber': {
        'name_fa':'کهربایی گرم','widget_bg':QColor(70,40,0,225),'widget_text':QColor(255,210,150),
        'box_bg':QColor(80,50,10,210),'box_text':QColor(255,220,180),'box_border':QColor(120,80,40),
        'box_bg_hover':QColor(100,70,30,220),
        'flat_hover_bg':QColor(255,210,150,25),
        'menu_bg':QColor(80,50,10,245),'menu_text':QColor(255,210,150),'menu_border':QColor(120,80,40),
        'menu_selected_bg':QColor(200,120,50),'menu_selected_text':QColor(255,230,200),
    }
}
font_sizes = {'خیلی کوچک':8,'کوچک':10,'متوسط':15,'بزرگ':20,'خیلی بزرگ':24}
quote_box_widths = {"باریک": 200, "متوسط": 280, "عریض": 360} # Width in pixels
DEFAULT_QUOTE_BOX_WIDTH_KEY = "متوسط"

class QuoteWidget(QWidget):
    def __init__(self, parent_widget, settings, initial_font_pt, initial_boxed_style):
        super().__init__(parent_widget) 
        self.parent_widget = parent_widget
        self.settings = settings
        self.font_pt = initial_font_pt
        self.boxed_style = initial_boxed_style
        self.quote_box_width_key = self.settings.value("quote_widget/width_key", DEFAULT_QUOTE_BOX_WIDTH_KEY)
        self.quote_box_width_val = quote_box_widths.get(self.quote_box_width_key, quote_box_widths[DEFAULT_QUOTE_BOX_WIDTH_KEY])
        self.old_pos = None

        self.setWindowTitle("جعبه نقل قول")
        # Removed Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        
        # Explicitly enable mouse tracking to receive move events even without buttons pressed
        self.setMouseTracking(True)

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        default_quote = self.settings.value("quote_widget/default_quote", "اینجا نقل قول نمایش داده می‌شود.")
        self.quote_label = QLabel("...") # Placeholder, updated by _update_quote_text_display
        
        # Font will be set in apply_theme using self.font_pt
        self.quote_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.quote_label.setWordWrap(True)
        
        # Ensure the label has a policy that expands vertically but stays fixed width
        self.quote_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        
        # Set word wrap mode to properly wrap words
        self.quote_label.setTextFormat(Qt.TextFormat.RichText)
        
        # Set minimum width to ensure proper text wrapping
        self.quote_label.setMinimumWidth(self.quote_box_width_val - 30)  # Account for margins
        
        if hasattr(self.parent_widget, 'shadow'):
             self.quote_label.setGraphicsEffect(self.parent_widget.shadow())
        layout.addWidget(self.quote_label)
        self.setLayout(layout)

        # Quote related initializations
        self.quotes_list = []
        self.quote_update_frequency = "daily" # Default: daily, hourly, weekly
        self.last_quote_update_timestamp = 0 # Store as timestamp
        self.current_quote_index = self.settings.value("quote_widget/current_quote_index", 0, type=int)

        self.quote_timer = QTimer(self)
        self.quote_timer.timeout.connect(self._check_and_update_quote)
        
        self._load_quote_settings_and_start_timer()

        self.apply_theme() 
        self.load_position() 
        # self.adjustSize() # adjustSize will be called in _update_quote_text_display and apply_theme 
    
        # Add a delayed resize to ensure proper sizing when first shown
        QTimer.singleShot(100, self._ensure_proper_size)

    def load_position(self):
        pos = self.settings.value("quote_widget/pos", None)
        if pos:
            self.move(pos)
        else: 
            if self.parent_widget:
                parent_geo = self.parent_widget.geometry()
                screen_geo = QApplication.primaryScreen().availableGeometry()
                x = parent_geo.right() + 10
                y = parent_geo.top()
                
                # Attempt to place it fully on screen if default position is off
                # Use self.frameGeometry().width() before widget is shown and sized
                temp_width = self.frameGeometry().width() if self.isVisible() else self.sizeHint().width() + 20 # Estimate with padding
                temp_height = self.frameGeometry().height() if self.isVisible() else self.sizeHint().height() + 20

                if x + temp_width > screen_geo.right():
                    x = parent_geo.left() - temp_width - 10
                if x < screen_geo.left(): 
                    x = screen_geo.left()

                if y + temp_height > screen_geo.bottom():
                    y = screen_geo.bottom() - temp_height
                if y < screen_geo.top():
                    y = screen_geo.top()
                self.move(x,y)

    def save_settings(self):
        if self.isVisible(): # Only save position if visible, otherwise it might save a weird off-screen pos
            self.settings.setValue("quote_widget/pos", self.pos())
        self.settings.setValue("quote_widget/quotes_list", self.quotes_list)
        self.settings.setValue("quote_widget/frequency", self.quote_update_frequency)
        self.settings.setValue("quote_widget/width_key", self.quote_box_width_key)
        self.settings.setValue("quote_widget/last_update_timestamp", self.last_quote_update_timestamp)
        self.settings.setValue("quote_widget/current_quote_index", self.current_quote_index)

    def _load_quote_settings_and_start_timer(self):
        default_quotes = [
            "همیشه لبخند بزن، حتی وقتی سخت است.",
            "امروز بهترین روز برای شروع است.",
            "موفقیت نتیجه تلاش‌های کوچک و مداوم است.",
            "هر روز یک فرصت جدید است.",
            "به خودت ایمان داشته باش."
        ]
        self.quotes_list = self.settings.value("quote_widget/quotes_list", default_quotes)
        if not self.quotes_list or not isinstance(self.quotes_list, list) or not all(isinstance(q, str) for q in self.quotes_list):
            self.quotes_list = default_quotes

        self.quote_update_frequency = self.settings.value("quote_widget/frequency", "daily")
        self.last_quote_update_timestamp = self.settings.value("quote_widget/last_update_timestamp", 0, type=float)
        
        self._update_quote_text_display(initial_load=True) # Set initial quote
        
        self.quote_timer.start(60 * 1000) # Check every minute
        self._check_and_update_quote() # Perform an initial check/update if needed

    def _get_interval_seconds(self):
        if self.quote_update_frequency == "hourly":
            return 60 * 60
        elif self.quote_update_frequency == "weekly":
            return 60 * 60 * 24 * 7
        # Add a short interval for testing if needed, e.g.:
        # elif self.quote_update_frequency == "testing":
        #     return 15 # 15 seconds 
        else: # daily or default
            return 60 * 60 * 24
            
    def _ensure_proper_size(self):
        """Ensure the widget is properly sized after all layouts are calculated"""
        self.quote_label.adjustSize()
        self.adjustSize()
        QApplication.processEvents()
        # Force update after all events are processed
        self.repaint()

    def _check_and_update_quote(self):
        current_time = time.time()
        time_since_last_update = current_time - self.last_quote_update_timestamp

        if time_since_last_update >= self._get_interval_seconds(): 
            self._update_quote_text_display()
            QApplication.processEvents() # Process events to ensure UI updates

    def _update_quote_text_display(self, initial_load=False):
        current_timestamp = time.time()
        actual_quote_to_display = "(لیست نقل قول خالی است)"

        if not self.quotes_list:
            actual_quote_to_display = "(لیست نقل قول خالی است)"
        else:
            # Determine if we need to update or can use existing displayed quote
            # This logic simplifies: always pick a quote based on timer or if forced by initial_load/settings change
            if not initial_load and (current_timestamp - self.last_quote_update_timestamp) < self._get_interval_seconds():
                # Not enough time passed, keep current quote if available in label
                # This part can be tricky if the label text isn't perfectly synced with quotes_list[current_quote_index]
                # For robustness, let's re-fetch from quotes_list using current_quote_index
                if 0 <= self.current_quote_index < len(self.quotes_list):
                    actual_quote_to_display = self.quotes_list[self.current_quote_index]
                # else, it will fall through to pick a new one / default
            else:
                # Time to pick a new quote
                if len(self.quotes_list) > 1:
                    new_indices = [i for i, _ in enumerate(self.quotes_list) if i != self.current_quote_index]
                    self.current_quote_index = random.choice(new_indices) if new_indices else 0
                elif self.quotes_list: # Only one quote
                    self.current_quote_index = 0
                # If list became empty somehow and wasn't caught above, default_quote will be used
                
                if 0 <= self.current_quote_index < len(self.quotes_list):
                    actual_quote_to_display = self.quotes_list[self.current_quote_index]
                
                self.last_quote_update_timestamp = current_timestamp
                # self.settings.setValue("quote_widget/last_update_timestamp", self.last_quote_update_timestamp) # Saved by save_settings
                # self.settings.setValue("quote_widget/current_quote_index", self.current_quote_index) # Saved by save_settings

        # Set fixed width before setting text to ensure proper height calculation for wrapped text
        self.setFixedWidth(self.quote_box_width_val)
        
        # Configure label for proper text wrapping
        self.quote_label.setWordWrap(True)
        self.quote_label.setMinimumWidth(self.quote_box_width_val - 30)  # Account for margins
        self.quote_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Set text and force proper sizing
        self.quote_label.setText(actual_quote_to_display)
        
        # Using sizeHint() to determine proper height
        text_height = self.quote_label.sizeHint().height()
        self.quote_label.setMinimumHeight(text_height)
        
        # Resize the widget to fit content
        self.adjustSize()

    def set_quote_settings(self, quotes=None, frequency=None):
        if quotes is not None:
            self.quotes_list = quotes if quotes else []
            self.settings.setValue("quote_widget/quotes_list", self.quotes_list)
        
        if frequency is not None:
            self.quote_update_frequency = frequency
            self.settings.setValue("quote_widget/frequency", self.quote_update_frequency)
        
        # Force an immediate update to reflect new settings
        self._update_quote_text_display() 
        # Restart timer with potentially new interval logic (though timer interval is fixed, the check logic changes)
        self._check_and_update_quote() 

    def apply_theme(self):
        if not self.parent_widget: return
        print(f"[QuoteWidget] apply_theme: Applying theme with boxed_style = {self.boxed_style}") # Debug
        scheme = color_schemes[self.parent_widget.active_scheme_key]

        # Store current visibility state
        was_visible = self.isVisible()
        if was_visible:
            self.hide()

        # Always use translucent background for proper alpha handling
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setStyleSheet("")
        
        # Override paintEvent to handle background drawing
        def paintEvent(self, event):
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            if self.boxed_style:
                bg_color = QColor(scheme.get('box_bg', scheme['widget_bg']))
                border_color = QColor(scheme.get('box_border', scheme['menu_border']))
                
                # Draw rounded rect background with proper alpha
                painter.setBrush(QBrush(bg_color))
                painter.setPen(QPen(border_color, 1))
                painter.drawRoundedRect(self.rect(), 6, 6)
            else:
                # Fully transparent in non-boxed mode
                pass
            
            # Call the original paint event to handle children
            super(QuoteWidget, self).paintEvent(event)
        
        # Replace the paintEvent method
        self.paintEvent = types.MethodType(paintEvent, self)
        
        # Update label style
        label_text_color = scheme.get('box_text', scheme['widget_text'])
        self.quote_label.setStyleSheet(f"QLabel {{ color: {label_text_color.name(QColor.NameFormat.HexArgb)}; background-color: transparent; border: none; }}")

        # Update font
        current_label_font_size = self.font_pt - 2 if self.font_pt > 10 else self.font_pt
        current_label_font_size = max(8, current_label_font_size)
        self.quote_label.setFont(QFont(DEFAULT_FONT_FAMILY, current_label_font_size))
        
        # Force immediate update
        self.update()
        self.repaint()
        QApplication.processEvents()

        # Show widget if it was visible before
        if was_visible:
            self.show()
            self.raise_()

        self._update_quote_text_display() # Update text and apply size constraints

    def update_display_settings(self, font_pt=None, boxed_style=None, width_key=None):
        changed = False
        width_value_updated = False

        if font_pt is not None and self.font_pt != font_pt:
            self.font_pt = font_pt
            changed = True
        
        if boxed_style is not None and self.boxed_style != boxed_style:
            self.boxed_style = boxed_style
            changed = True
        
        if width_key is not None and self.quote_box_width_key != width_key:
            self.quote_box_width_key = width_key
            new_width_val = quote_box_widths.get(width_key, quote_box_widths[DEFAULT_QUOTE_BOX_WIDTH_KEY])
            if self.quote_box_width_val != new_width_val:
                self.quote_box_width_val = new_width_val
                width_value_updated = True # Specifically track if the pixel value changed
            changed = True
    
        if changed:
            # If the width value itself changed, we need to ensure the fixed width is set *before* 
            # apply_theme and _update_quote_text_display try to calculate sizes.
            if width_value_updated:
                self.setFixedWidth(self.quote_box_width_val)
                # The label's minimum width for wrapping will be set in _update_quote_text_display

            # apply_theme will handle restyling and then call _update_quote_text_display.
            # _update_quote_text_display will use the (potentially new) self.quote_box_width_val 
            # to set label's minimum width, set text, and adjust sizes.
            self.apply_theme()
        
            # Process events once after all changes are applied.
            QApplication.processEvents()

            self.save_settings()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.old_pos = e.globalPosition().toPoint()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            self.grabMouse() # Capture all mouse events while dragging
            e.accept()
        else:
            super().mousePressEvent(e)
            
    def mouseMoveEvent(self, e):
        # Only drag if we have old_pos set from mousePressEvent
        if hasattr(self, 'old_pos') and self.old_pos is not None:
            delta = QPoint(e.globalPosition().toPoint() - self.old_pos)
            new_pos = self.pos() + delta
            self.move(new_pos)
            self.old_pos = e.globalPosition().toPoint()
            e.accept()
            return
        
        # If not dragging, pass to parent
        super().mouseMoveEvent(e)
    
    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and hasattr(self, 'old_pos') and self.old_pos is not None:
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.releaseMouse() # Release the mouse capture
            self.save_settings()
            self.old_pos = None
            e.accept()
        else:
            super().mouseReleaseEvent(e)
    
    def closeEvent(self, event):
        if hasattr(self, 'quote_timer') and self.quote_timer.isActive():
            self.quote_timer.stop()
        self.save_settings() 
        super().closeEvent(event)



class ManageQuotesDialog(QDialog):
    def __init__(self, current_quotes, parent=None):
        super().__init__(parent)
        self.setWindowTitle("مدیریت لیست نقل قول‌ها")
        self.setMinimumWidth(400)
        self.current_quotes = list(current_quotes) # Make a mutable copy
        self.updated_quotes = list(current_quotes) # Initialize with current quotes

        layout = QVBoxLayout(self)

        self.quotes_list_widget = QListWidget()
        for quote in self.current_quotes:
            item = QListWidgetItem(quote)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable) # Allow in-place editing
            self.quotes_list_widget.addItem(item)
        layout.addWidget(self.quotes_list_widget)

        self.new_quote_input = QLineEdit()
        self.new_quote_input.setPlaceholderText("نقل قول جدید را اینجا وارد کنید...")
        layout.addWidget(self.new_quote_input)

        buttons_layout = QHBoxLayout()
        self.add_button = QPushButton("➕ افزودن")
        self.delete_button = QPushButton("➖ حذف انتخاب شده")
        buttons_layout.addWidget(self.add_button)
        buttons_layout.addWidget(self.delete_button)
        layout.addLayout(buttons_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(self.button_box)

        self.add_button.clicked.connect(self._add_quote)
        self.delete_button.clicked.connect(self._delete_quote)
        self.button_box.accepted.connect(self._on_accept)
        self.button_box.rejected.connect(self.reject)

        self.setLayout(layout)

    def _add_quote(self):
        new_quote_text = self.new_quote_input.text().strip()
        if new_quote_text:
            item = QListWidgetItem(new_quote_text)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.quotes_list_widget.addItem(item)
            self.new_quote_input.clear()

    def _delete_quote(self):
        selected_item = self.quotes_list_widget.currentItem()
        if selected_item:
            row = self.quotes_list_widget.row(selected_item)
            self.quotes_list_widget.takeItem(row)

    def _on_accept(self):
        self.updated_quotes = []
        for i in range(self.quotes_list_widget.count()):
            self.updated_quotes.append(self.quotes_list_widget.item(i).text())
        self.accept()

    def get_updated_quotes(self):
        return self.updated_quotes


class CalendarWidget(QWidget):
    def _fetch_and_cache_range_events(self, start_date, end_date):
        if self.is_background_caching_busy:
            print("Background event caching is already in progress. Skipping new request.")
            return
        
        self.is_background_caching_busy = True
        try:
            print(f"Starting to fetch and cache events from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
            current_processing_date = start_date
            days_processed_for_event_processing = 0

            while current_processing_date <= end_date:
                date_str = current_processing_date.strftime("%Y-%m-%d")
                print(f"Processing {date_str}...")
                
                cached_events = self._load_event_from_cache(current_processing_date)
                if cached_events is not None:
                    print(f"  Events for {date_str} already in cache. Skipping.")
                    current_processing_date += jdatetime.timedelta(days=1)
                    continue
                
                try:
                    # Use the new pnldev.com API
                    url = f"https://pnldev.com/api/calender?year={current_processing_date.year}&month={current_processing_date.month}&day={current_processing_date.day}"
                    response = requests.get(url, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    events_list = [] # Default to empty list
                    if data.get("status") is True and "result" in data and isinstance(data["result"], dict):
                        events_list = data["result"].get("event", [])
                        if not isinstance(events_list, list):
                            print(f"  Events data for {date_str} is not a list: {events_list}. Treating as no events.")
                            events_list = []
                    else:
                        status_val = data.get('status', 'N/A')
                        error_msg = data.get('result', 'No result field or API status not true')
                        if isinstance(error_msg, dict) and "message" in error_msg: # some APIs return error details in result.message
                            error_msg = error_msg["message"]
                        elif not isinstance(error_msg, str): # ensure error_msg is a string for logging
                            error_msg = str(error_msg)
                        print(f"  Failed to parse events for {date_str}. API Status: {status_val}. Message: '{error_msg}'")
                    self._save_event_to_cache(current_processing_date, events_list)
                    print(f"  Fetched and cached events for {date_str}: {events_list if events_list else 'No events'}")
                except requests.exceptions.RequestException as e:
                    print(f"  Failed to fetch events for {date_str}: {e}. Saving as no events.")
                    self._save_event_to_cache(current_processing_date, []) # Save empty list on error
                except json.JSONDecodeError as e:
                    print(f"  JSON Decode Error for {date_str}: {e}. Saving as no events.")
                    self._save_event_to_cache(current_processing_date, [])
                except Exception as e:
                    print(f"  Unexpected error for {date_str}: {e}. Saving as no events.")
                    self._save_event_to_cache(current_processing_date, [])
                
                time.sleep(0.1) # Be polite to the API server
                days_processed_for_event_processing += 1
                if days_processed_for_event_processing % 5 == 0: # Process events every 5 days or so
                    QApplication.processEvents() # Keep UI responsive
                
                current_processing_date += jdatetime.timedelta(days=1)
            
            QApplication.processEvents() # Final process events
            print(f"Finished fetching and caching events for the specified range.")
        finally:
            self.is_background_caching_busy = False
    
    # The following line was incorrectly part of the view of this function previously
    # end_date = today + jdatetime.timedelta(days=days_after)
    # self._fetch_and_cache_range_events(start_date, end_date)

    def _handle_cache_surrounding_days(self, days_before=7, days_after=7):
        """Cache events for days surrounding today (+-7 days by default)."""
        today = jdatetime.date.today()
        start_date = today - jdatetime.timedelta(days=days_before)
        end_date = today + jdatetime.timedelta(days=days_after)
        print(f"Manually triggered cache update for {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        self._fetch_and_cache_range_events(start_date, end_date)

    def _fetch_and_cache_year_events(self, year):
        print(f"Starting to fetch and cache events for Shamsi year: {year} using new API.")
        api_url = f"https://pnldev.com/api/calender?year={year}"
        
        try:
            print(f"Fetching all events for year {year} from {api_url}...")
            response = requests.get(api_url, timeout=30) # Increased timeout for a larger response
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            data = response.json()

            if data.get("status") is True and "result" in data:
                year_data = data["result"]
                days_processed_count = 0
                if not isinstance(year_data, dict): # Ensure year_data is a dictionary (months)
                    print(f"  Error: Expected year_data to be a dictionary for year {year}, got {type(year_data)}. API response: {data.get('result')}")
                    # Save empty events for all days of the year to prevent re-fetching with bad data
                    # This part might need more nuanced error handling depending on how often this case occurs
                    # For now, we log and exit the processing for this year.
                else:
                    for month_str, month_data in year_data.items():
                        if not isinstance(month_data, dict): # Skip if month_data is not a dictionary of days
                            print(f"  Skipping non-dict month_data for month {month_str} in year {year}. Value: {month_data}")
                            continue
                        for day_str, day_details in month_data.items():
                            if not isinstance(day_details, dict): # Skip if day_details is not a dictionary
                                print(f"  Skipping non-dict day_details for {year}-{month_str}-{day_str}. Value: {day_details}")
                                continue

                            # Ensure 'solar' details are present to confirm it's a valid day entry
                            if "solar" not in day_details or not isinstance(day_details["solar"], dict) or not all(k in day_details["solar"] for k in ["year", "month", "day"]):
                                print(f"  Skipping entry for {year}-{month_str}-{day_str} due to missing or malformed solar details. Details: {day_details.get('solar')}")
                                continue
                        
                            try:
                                api_year = int(day_details["solar"]["year"])
                                api_month = int(day_details["solar"]["month"])
                                api_day = int(day_details["solar"]["day"])
                                
                                # Verify that the year, month, day from API match our iteration context
                                if api_year != year or api_month != int(month_str) or api_day != int(day_str):
                                    print(f"  Data mismatch for {year}-{month_str}-{day_str}: API reported {api_year}-{api_month}-{api_day}. Skipping.")
                                    continue

                                actual_date = jdatetime.date(year, int(month_str), int(day_str))
                                events_list = day_details.get("event", []) # Default to empty list if "event" key is missing
                                
                                if not isinstance(events_list, list):
                                    print(f"  Events data for {actual_date.strftime('%Y-%m-%d')} is not a list: {events_list}. Treating as no events.")
                                    events_list = []
                                    
                                self._save_event_to_cache(actual_date, events_list)
                                days_processed_count +=1
                            except (ValueError, TypeError) as ve_te:
                                print(f"  Error processing date/event for {year}-{month_str}-{day_str} from solar details {day_details.get('solar')}: {ve_te}")
                            except Exception as inner_e:
                                print(f"  Unexpected error processing day {year}-{month_str}-{day_str}: {inner_e}")
                
                if days_processed_count > 0:
                    print(f"  Successfully processed and cached {days_processed_count} days for year {year}.")
                else:
                    print(f"  No valid day data found or processed for year {year} in API response.")
            else:
                status = data.get('status', 'N/A')
                error_message = "API status not true or result missing."
                # Check if 'result' contains a string error message from the API
                if "result" in data and isinstance(data["result"], str):
                    error_message = data["result"]
                elif "message" in data and isinstance(data["message"], str): # Some APIs use 'message'
                    error_message = data["message"]
                print(f"  Failed to parse events for year {year}. API Status: {status}. Message: '{error_message}'")

        except requests.exceptions.Timeout:
            print(f"  Timeout while fetching events for year {year} from {api_url}.")
            # Consider saving empty events for the whole year or marking year as failed fetch
        except requests.exceptions.RequestException as e:
            print(f"  Failed to fetch events for year {year} from {api_url}: {e}")
        except json.JSONDecodeError as e:
            print(f"  JSON Decode Error for year {year} from {api_url}: {e}")
        except Exception as e:
            print(f"  Unexpected error while processing events for year {year}: {e}")
    
        QApplication.processEvents() # Process events once after attempting to fetch the whole year
        print(f"Finished fetching and caching attempt for Shamsi year: {year} using new API.")

    # _handle_cache_current_year and _handle_cache_next_year are no longer used by the menu
    # def _handle_cache_current_year(self):
    #     current_shamsi_year = jdatetime.date.today().year
    #     self._fetch_and_cache_year_events(current_shamsi_year)

    # def _handle_cache_next_year(self):
    #     next_shamsi_year = jdatetime.date.today().year + 1
    #     self._fetch_and_cache_year_events(next_shamsi_year)
    def _get_cache_file_path(self):
        # Place cache file in the same directory as the script
        # sys.argv[0] is the script path. If frozen with PyInstaller, sys.executable might be better.
        # For simplicity with .pyw files run directly, os.path.dirname(__file__) is robust.
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
        except NameError: # __file__ is not defined if running in an interactive interpreter or frozen
            script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        return os.path.join(script_dir, EVENTS_CACHE_FILE)

    def _load_event_from_cache(self, j_date):
        cache_file = self._get_cache_file_path()
        date_str = j_date.strftime("%Y-%m-%d")
        try:
            if not os.path.exists(cache_file):
                return None
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            return cache_data.get(date_str)
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading from cache: {e}")
            return None

    def _save_event_to_cache(self, j_date, events_list):
        cache_file = self._get_cache_file_path()
        date_str = j_date.strftime("%Y-%m-%d")
        try:
            if not os.path.exists(os.path.dirname(cache_file)):
                 os.makedirs(os.path.dirname(cache_file), exist_ok=True)
            
            cache_data = {}
            if os.path.exists(cache_file):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    try:
                        cache_data = json.load(f)
                    except json.JSONDecodeError:
                        # Cache is corrupt, start fresh or handle error
                        print(f"Warning: Cache file {cache_file} is corrupt. Starting fresh.") 
                        pass # Will overwrite with new data
            
            cache_data[date_str] = events_list
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=4)
        except IOError as e:
            print(f"Error saving to cache: {e}")

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ویجت تقویم شمسی")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.old_pos = None 

        self.settings = QSettings("MyCompany", "ShamsiCalendar")
        self.DEFAULT_FONT_FAMILY = DEFAULT_FONT_FAMILY # Make accessible for child widgets

        # Ensure the cache file exists, create if not
        try:
            cache_path = self._get_cache_file_path()
            if not os.path.exists(cache_path):
                # Create directory if it doesn't exist
                cache_dir = os.path.dirname(cache_path)
                if cache_dir and not os.path.exists(cache_dir): # Ensure cache_dir is not empty
                    os.makedirs(cache_dir, exist_ok=True)
                with open(cache_path, 'w', encoding='utf-8') as f:
                    json.dump({}, f) # Initialize with an empty JSON object
        except IOError as e:
            # It's possible cache_path is not defined if _get_cache_file_path() fails early
            print(f"Warning: Could not create/initialize cache file. Error: {e}") 
        except Exception as e:
            print(f"Unexpected error during cache file initialization: {e}")

        saved_scheme_name = self.settings.value("color_scheme", "Dark")
        self.active_scheme_key = saved_scheme_name if saved_scheme_name in color_schemes else "Dark"
        self.boxed_style = self.settings.value("boxed", "yes") == "yes"
        self.font_size_lbl = self.settings.value("font_size", "متوسط")
        self.compact_mode = self.settings.value("compact", "no") == "yes"
        self.font_pt = font_sizes.get(self.font_size_lbl, 15)
        self.offset = 0
        self.quote_widget = None # Initialize quote_widget
        self.rss_widget = None # Initialize rss_widget
        self.is_background_caching_busy = False

        self.init_quote_widget() # Create/show quote widget
        self.init_rss_widget() # Create/show rss widget
        self.apply_theme_stylesheet()
        self.load_position() 
        self.build_ui()

    def init_rss_widget(self):
        if not self.rss_widget:
            self.rss_widget = RSSReaderWidget(self, self.settings, self.font_pt, self.boxed_style)
        
        rss_widget_visible = self.settings.value("rss_widget/is_visible", False, type=bool) # Default to False
        print(f"[CalendarWidget] Loading RSS widget with saved visibility: {rss_widget_visible}")
        
        if self.rss_widget:
            if rss_widget_visible:
                self.rss_widget.show()
                self.rss_widget.raise_()
            else:
                self.rss_widget.hide()

    def init_quote_widget(self):
        if not self.quote_widget:
            self.quote_widget = QuoteWidget(self, self.settings, self.font_pt, self.boxed_style)
        
        # Load the saved visibility state - default to True for better user experience
        quote_widget_visible = self.settings.value("quote_widget/is_visible", True, type=bool)
        
        print(f"[CalendarWidget] Loading quote widget with saved visibility: {quote_widget_visible}")
        
        if self.quote_widget: # Ensure it was created
            if quote_widget_visible:
                self.quote_widget.show()
                self.quote_widget.raise_()
            else:
                self.quote_widget.hide()
            # The visibility state is only saved in toggle_quote_widget_visibility_action and closeEvent

    def apply_theme_stylesheet(self):
        scheme = color_schemes[self.active_scheme_key]
        self.setStyleSheet(f"QWidget {{ background-color: {scheme['widget_bg'].name(QColor.NameFormat.HexArgb)}; color: {scheme['widget_text'].name(QColor.NameFormat.HexArgb)}; }}")
        if hasattr(self, 'quote_widget') and self.quote_widget:
            self.quote_widget.apply_theme()
        if hasattr(self, 'rss_widget') and self.rss_widget:
            self.rss_widget.apply_theme()

    def load_position(self):
        pos = self.settings.value("pos", None)
        if pos: self.move(pos)

    def _clear_layout_widgets(self, layout):
        if layout is None: return
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget: widget.deleteLater()
            else:
                sub_layout = item.layout()
                if sub_layout: self._clear_layout_widgets(sub_layout); sub_layout.deleteLater() 

    def build_ui(self):
        if self.layout() is not None:
            self._clear_layout_widgets(self.layout()); QWidget().setLayout(self.layout())

        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        main_layout.setContentsMargins(10, 5, 10, 10)

        secondary_font_size = self.font_pt - 2 if self.font_pt > 10 else (self.font_pt - 1 if self.font_pt > 8 else self.font_pt)
        secondary_font_size = max(8, secondary_font_size) 

        top_right_layout = QHBoxLayout()
        top_right_layout.addStretch(1)

        # Today Icon Button
        self.today_icon_btn = QPushButton()
        self.today_icon_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload))
        self.today_icon_btn.setToolTip("بازگشت به امروز")
        self.today_icon_btn.setFixedSize(26, 26)
        self.today_icon_btn.setFlat(True)
        # Hover style for icon buttons will be set in update_date like settings button
        self.today_icon_btn.clicked.connect(self.reset_today)
        top_right_layout.addWidget(self.today_icon_btn)

        # Center Window Icon Button
        self.center_icon_btn = QPushButton()
        self.center_icon_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DesktopIcon))
        self.center_icon_btn.setToolTip("مرکز صفحه")
        self.center_icon_btn.setFixedSize(26, 26)
        self.center_icon_btn.setFlat(True)
        self.center_icon_btn.clicked.connect(self.center_widget_action)
        top_right_layout.addWidget(self.center_icon_btn)
        
        # Settings Button (existing)
        self.top_settings_btn = QPushButton("⚙️") # Using a gear character
        settings_icon_font_size = max(10, int(self.font_pt * 0.8))
        self.top_settings_btn.setFont(QFont(DEFAULT_FONT_FAMILY, settings_icon_font_size))
        self.top_settings_btn.setFixedSize(26, 26)
        self.top_settings_btn.setFlat(True)
        self.top_settings_btn.clicked.connect(self.show_settings_menu)
        top_right_layout.addWidget(self.top_settings_btn)
        main_layout.addLayout(top_right_layout)

        self.date_label = QLabel()
        self.date_label.setFont(QFont(DEFAULT_FONT_FAMILY, self.font_pt))
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.date_label.setGraphicsEffect(self.shadow())

        # --- Navigation Buttons - Icons set to standard visual direction ---
        self.nav_left_button = QPushButton("◀") # Left button, "previous" icon
        self.nav_right_button = QPushButton("▶") # Right button, "next" icon

        nav_button_font_size = self.font_pt 
        for btn in [self.nav_left_button, self.nav_right_button]:
            btn.setFont(QFont(DEFAULT_FONT_FAMILY, nav_button_font_size))
            btn.setFixedSize(30, 30) 
            btn.setFlat(True) # Flat appearance, detailed style (including hover) in update_date
            btn.setGraphicsEffect(self.shadow())
        
        self.nav_right_button.clicked.connect(self.prev_day) 
        self.nav_left_button.clicked.connect(self.next_day)
        # --- End Navigation Buttons ---

        date_row_layout = QHBoxLayout()
        date_row_layout.addWidget(self.nav_left_button) 
        date_row_layout.addWidget(self.date_label, 1) 
        date_row_layout.addWidget(self.nav_right_button) 
        main_layout.addLayout(date_row_layout)

        if not self.compact_mode:
            self.sub_label = QLabel()
            self.sub_label.setFont(QFont(DEFAULT_FONT_FAMILY, secondary_font_size))
            self.sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.sub_label.setGraphicsEffect(self.shadow())
            main_layout.addWidget(self.sub_label)

            self.event_label = QLabel("مناسبت: ---")
            self.event_label.setFont(QFont(DEFAULT_FONT_FAMILY, secondary_font_size))
            self.event_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.event_label.setGraphicsEffect(self.shadow())
            self.event_label.setWordWrap(True)
            main_layout.addWidget(self.event_label)

            # The old bottom_buttons_layout is intentionally omitted here as its functionality
            # has been moved to the icon buttons in the top_right_layout.

        self.setLayout(main_layout)
        self.update_date()
        if not self.settings.value("pos"): self.center_on_screen()
    def update_date(self):
        today = jdatetime.date.today() + jdatetime.timedelta(days=self.offset)
        g = today.togregorian(); h = Gregorian(g.year, g.month, g.day).to_hijri()
        scheme = color_schemes[self.active_scheme_key] # For hover colors

        if hasattr(self,'date_label'): self.date_label.setText(f"{weekday_fa[today.strftime('%A')]} {today.day} {months_fa[today.strftime('%B')]} {today.year}")

        if hasattr(self,'compact_mode') and not self.compact_mode:
            if hasattr(self,'sub_label'): self.sub_label.setText(f"میلادی: {g.strftime('%d %B %Y')}     ⬥     قمری: {h.day} {hijri_months_fa[h.month]} {h.year}")
            if hasattr(self,'event_label'):
                cached_events = self._load_event_from_cache(today)
            if cached_events is not None:
                self.event_label.setText("مناسبت: " + ", ".join(cached_events) if cached_events else "مناسبت: ---")
            else:
                try:
                    # Use the new pnldev.com API for inline fetching
                    url = f"https://pnldev.com/api/calender?year={today.year}&month={today.month}&day={today.day}"
                    response = requests.get(url, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    ev = [] # Default to empty list
                    if data.get("status") is True and "result" in data and isinstance(data["result"], dict):
                        ev = data["result"].get("event", [])
                        if not isinstance(ev, list):
                            print(f"  Events data for {today.strftime('%Y-%m-%d')} in update_date is not a list: {ev}. Treating as no events.")
                            ev = []
                    else: # This 'else' means data.get("status") was not True or 'result' was missing/not a dict
                        current_status_val = "Unknown"
                        current_error_msg = "Malformed API response or status not true."
                        if isinstance(data, dict):
                            current_status_val = str(data.get('status', 'N/A')) # Ensure string for printing
                            raw_error_msg = data.get('result', 'No result field or API status not true')
                            if isinstance(raw_error_msg, dict) and "message" in raw_error_msg:
                                current_error_msg = str(raw_error_msg["message"])
                            elif not isinstance(raw_error_msg, str):
                                current_error_msg = str(raw_error_msg)
                            else:
                                current_error_msg = raw_error_msg # It's already a string
                        else:
                            current_error_msg = f"API response was not a dictionary: {str(data)[:100]}" # Log part of the unexpected data
                        
                        print(f"  Failed to parse events for {today.strftime('%Y-%m-%d')} in update_date. API Status: {current_status_val}. Message: '{current_error_msg}'")
                    self.event_label.setText("مناسبت: " + ", ".join(ev) if ev else "مناسبت: ---")
                    self._save_event_to_cache(today, ev)
                    # --- Automatic background cache for surrounding days ---
                    if not self.is_background_caching_busy:
                        print(f"Online: Triggering background cache for {today.strftime('%Y-%m-%d')} +/- 7 days.")
                        cache_start_date = today - jdatetime.timedelta(days=7)
                        cache_end_date = today + jdatetime.timedelta(days=7)
                        # This call will manage its own busy flag
                        self._fetch_and_cache_range_events(cache_start_date, cache_end_date)
                    else:
                        print("Skipping automatic background cache: process already busy.")
                except requests.exceptions.RequestException as e:
                    # This catches network errors, timeout, HTTP errors, etc.
                    print(f"API Request failed: {e}")
                    self.event_label.setText("مناسبت: (آفلاین - بدون اطلاعات)")
                except json.JSONDecodeError as e:
                    print(f"JSON Decode Error: {e}")
                    self.event_label.setText("مناسبت: (خطا در پاسخ API)")
                except Exception as e: # Catch any other unexpected error during fetch
                    print(f"Unexpected error during event fetch: {e}")
                    self.event_label.setText("مناسبت: (خطای نامشخص)")
        
        # Style for QLabels
        label_style_str = self.get_element_style(boxed=self.boxed_style, is_button=False)
        # Style for QPushButtons (nav, today, center)
        button_style_str = self.get_element_style(boxed=self.boxed_style, is_button=True)

        if hasattr(self,'date_label'): self.date_label.setStyleSheet(label_style_str)
        
        # Nav buttons use the button style with hover
        if hasattr(self,'nav_left_button'): self.nav_left_button.setStyleSheet(button_style_str)
        if hasattr(self,'nav_right_button'): self.nav_right_button.setStyleSheet(button_style_str)
        
        # Top settings button hover style
        if hasattr(self, 'top_settings_btn'):
            text_color = scheme['widget_text'].name(QColor.NameFormat.HexArgb)
            # Use a subtle version of flat_hover_bg for consistency
            hover_bg = scheme['flat_hover_bg'].name(QColor.NameFormat.HexArgb) 
            self.top_settings_btn.setStyleSheet(f"""
                QPushButton {{ background:none; border:none; padding:0px; color:{text_color}; }}
                QPushButton:hover {{ background-color: {hover_bg}; border-radius: 4px; }}""")

        # Today icon button hover style
        if hasattr(self, 'today_icon_btn'):
            self.today_icon_btn.setStyleSheet(f"""
                QPushButton {{ background:none; border:none; padding:0px; color:{text_color}; }}
                QPushButton:hover {{ background-color: {hover_bg}; border-radius: 4px; }}""")

        # Center icon button hover style
        if hasattr(self, 'center_icon_btn'):
            self.center_icon_btn.setStyleSheet(f"""
                QPushButton {{ background:none; border:none; padding:0px; color:{text_color}; }}
                QPushButton:hover {{ background-color: {hover_bg}; border-radius: 4px; }}""")

        if hasattr(self,'compact_mode') and not self.compact_mode:
            if hasattr(self,'sub_label'): self.sub_label.setStyleSheet(label_style_str)
            if hasattr(self,'event_label'): self.event_label.setStyleSheet(label_style_str)
            
            if hasattr(self,'today_btn'): self.today_btn.setStyleSheet(button_style_str)
            if hasattr(self,'center_widget_btn'): self.center_widget_btn.setStyleSheet(button_style_str)
        self.adjustSize()

    def prev_day(self): self.offset -= 1; self.update_date()
    def next_day(self): self.offset += 1; self.update_date()
    def reset_today(self): self.offset = 0; self.update_date()
    def center_widget_action(self): self.center_on_screen()

    def show_settings_menu(self):
        if not hasattr(self, 'top_settings_btn') or not self.top_settings_btn: return
        menu = QMenu(self)
        scheme = color_schemes[self.active_scheme_key]
        menu_style = f"""
            QMenu {{background-color:{scheme['menu_bg'].name(QColor.NameFormat.HexArgb)};color:{scheme['menu_text'].name(QColor.NameFormat.HexArgb)};border:1px solid {scheme['menu_border'].name(QColor.NameFormat.HexArgb)};padding:4px;}}
            QMenu::item {{padding:5px 20px;border-radius:4px;}} QMenu::item:selected {{background-color:{scheme['menu_selected_bg'].name(QColor.NameFormat.HexArgb)};color:{scheme['menu_selected_text'].name(QColor.NameFormat.HexArgb)};}}
            QMenu::separator {{height:1px;background-color:{scheme['menu_border'].name(QColor.NameFormat.HexArgb)};margin:4px 5px;}}
        """
        menu.setStyleSheet(menu_style)

        # Theme Menu
        theme_menu = QMenu("🎨 تغییر پوسته", menu)
        theme_menu.setStyleSheet(menu_style)
        for k, v in color_schemes.items():
            a = QAction(v['name_fa'], self, checkable=True)
            a.setChecked(k == self.active_scheme_key)
            a.triggered.connect(lambda checked, key=k: self.set_color_scheme(key))
            theme_menu.addAction(a)
        menu.addMenu(theme_menu)

        # Box Style Toggle
        box_action = QAction("🔳 باکس روشن/خاموش", self, checkable=True)
        box_action.setChecked(self.boxed_style)
        box_action.triggered.connect(self.toggle_box)
        menu.addAction(box_action)

        # Compact Mode Toggle
        compact_action = QAction("📏 حالت ساده/کامل", self, checkable=True)
        compact_action.setChecked(self.compact_mode)
        compact_action.triggered.connect(self.toggle_compact)
        menu.addAction(compact_action)

        # Font Size Menu
        font_menu = QMenu("🔠 اندازه فونت", menu)
        font_menu.setStyleSheet(menu_style)
        for lbl in font_sizes:
            a = QAction(lbl, self, checkable=True)
            a.setChecked(lbl == self.font_size_lbl)
            a.triggered.connect(lambda checked, l=lbl: self.set_font_size(l))
            font_menu.addAction(a)
        menu.addMenu(font_menu)

        menu.addSeparator()

        # --- Event Cache Settings ---
        cache_surrounding_days_action = QAction("🔄 به‌روزرسانی کش (اطراف امروز)", menu) # Text can be refined
        cache_surrounding_days_action.setToolTip("دانلود و ذخیره مناسبت‌های ۷ روز قبل و بعد از تاریخ امروز")
        cache_surrounding_days_action.triggered.connect(self._handle_cache_surrounding_days)
        menu.addAction(cache_surrounding_days_action)
        
        menu.addSeparator()

        # --- Quote Widget Settings Menu --- 
        quote_settings_menu = QMenu("💬 تنظیمات جعبه نقل قول", menu) # Changed icon for clarity
        quote_settings_menu.setStyleSheet(menu_style)

        # Toggle Quote Widget Visibility Action
        toggle_quote_visibility_action = QAction("👁️ نمایش/مخفی کردن جعبه", quote_settings_menu, checkable=True)
        initial_visibility = False
        if hasattr(self, 'quote_widget') and self.quote_widget:
            initial_visibility = self.quote_widget.isVisible()
        else: 
            initial_visibility = self.settings.value("quote_widget/is_visible", True, type=bool)
        toggle_quote_visibility_action.setChecked(initial_visibility)
        toggle_quote_visibility_action.triggered.connect(self.toggle_quote_widget_visibility_action)
        quote_settings_menu.addAction(toggle_quote_visibility_action)

        # Frequency submenu
        frequency_menu = QMenu("⏱️ فرکانس بروزرسانی", quote_settings_menu)
        frequency_menu.setStyleSheet(menu_style)
        
        self.frequency_action_group = QActionGroup(frequency_menu)
        self.frequency_action_group.setExclusive(True)

        current_frequency = "daily" # Default
        if hasattr(self, 'quote_widget') and self.quote_widget:
            current_frequency = self.quote_widget.quote_update_frequency
        else:
            current_frequency = self.settings.value("quote_widget/frequency", "daily")

        frequencies = {
            "hourly": "ساعتی",
            "daily": "روزانه",
            "weekly": "هفتگی",
        }

        for freq_key, freq_name in frequencies.items():
            action = QAction(freq_name, frequency_menu, checkable=True)
            action.setData(freq_key) # Store the key in the action's data
            action.setChecked(freq_key == current_frequency)
            action.triggered.connect(self._handle_quote_frequency_change)
            self.frequency_action_group.addAction(action)
            frequency_menu.addAction(action)
        
        quote_settings_menu.addMenu(frequency_menu)

        # --- Quote Box Width Submenu ---
        width_menu = QMenu("↔️ عرض جعبه نقل قول", quote_settings_menu)
        width_menu.setStyleSheet(menu_style)
        self.quote_width_action_group = QActionGroup(width_menu)
        self.quote_width_action_group.setExclusive(True)

        current_width_key = DEFAULT_QUOTE_BOX_WIDTH_KEY # Default
        if hasattr(self, 'quote_widget') and self.quote_widget:
            current_width_key = self.quote_widget.quote_box_width_key
        else:
            current_width_key = self.settings.value("quote_widget/width_key", DEFAULT_QUOTE_BOX_WIDTH_KEY)

        for w_key, w_name_map in quote_box_widths.items(): # Assuming quote_box_widths keys are the display names for simplicity here, or map if needed
            action = QAction(w_key, width_menu, checkable=True) # Use w_key as label
            action.setData(w_key)
            action.setChecked(w_key == current_width_key)
            action.triggered.connect(self._handle_quote_width_change)
            self.quote_width_action_group.addAction(action)
            width_menu.addAction(action)
        quote_settings_menu.addMenu(width_menu)
        # --- End Quote Box Width Submenu ---

        # Edit Quote List Action
        edit_quotes_action = QAction("📝 ویرایش لیست نقل قول ها", quote_settings_menu)
        edit_quotes_action.triggered.connect(self._show_edit_quotes_dialog)
        quote_settings_menu.addAction(edit_quotes_action)

        menu.addMenu(quote_settings_menu) # Add Quote Settings menu to main menu

        # --- RSS Widget Settings Menu --- 
        rss_settings_menu = QMenu("📰 تنظیمات RSS", menu) # Changed icon for clarity
        rss_settings_menu.setStyleSheet(menu_style)

        # Toggle RSS Widget Visibility Action
        toggle_rss_visibility_action = QAction("👁️ نمایش/مخفی کردن RSS", rss_settings_menu, checkable=True)
        initial_visibility = False
        if hasattr(self, 'rss_widget') and self.rss_widget:
            initial_visibility = self.rss_widget.isVisible()
        else: 
            initial_visibility = self.settings.value("rss_widget/is_visible", False, type=bool)
        toggle_rss_visibility_action.setChecked(initial_visibility)
        toggle_rss_visibility_action.triggered.connect(self.toggle_rss_widget_visibility_action)
        rss_settings_menu.addAction(toggle_rss_visibility_action)

        # Action to manage RSS feeds
        manage_rss_feeds_action = QAction("🔧 مدیریت منبع‌های RSS", rss_settings_menu)
        manage_rss_feeds_action.triggered.connect(self._show_manage_rss_feeds_dialog)
        rss_settings_menu.addAction(manage_rss_feeds_action)

        # RSS Box Width Submenu
        rss_width_menu = QMenu("عرض جعبه RSS", rss_settings_menu)
        rss_width_menu.setStyleSheet(menu_style)
        rss_width_group = QActionGroup(rss_width_menu)
        rss_width_group.setExclusive(True)

        current_rss_width_key = DEFAULT_RSS_BOX_WIDTH_KEY
        if hasattr(self, 'rss_widget') and self.rss_widget:
            current_rss_width_key = self.rss_widget.rss_box_width_key
        else:
            current_rss_width_key = self.settings.value("rss_widget/width_key", DEFAULT_RSS_BOX_WIDTH_KEY)

        for key, width_value in RSS_BOX_WIDTHS.items():
            action_text = f"{key.capitalize().replace('Xl', 'XL')} ({width_value}px)" # Format text like 'Small (300px)' or 'XL (600px)'
            action = QAction(action_text, rss_width_menu, checkable=True)
            action.setData(key)
            if key == current_rss_width_key:
                action.setChecked(True)
            rss_width_group.addAction(action)
            action.triggered.connect(self._handle_rss_box_width_change)
            rss_width_menu.addAction(action)
        rss_settings_menu.addMenu(rss_width_menu)

        menu.addMenu(rss_settings_menu)
        menu.addSeparator()

        menu.addAction("❌ خروج", QApplication.instance().quit)
        btn_global_pos = self.top_settings_btn.mapToGlobal(QPoint(0, self.top_settings_btn.height()))
        menu.exec(btn_global_pos)

    def set_color_scheme(self, k):
        self.active_scheme_key = k
        self.settings.setValue("color_scheme", k)
        self.apply_theme_stylesheet()
        self.update_date()
        # Also update the quote widget if it exists
        if hasattr(self, 'quote_widget') and self.quote_widget:
            self.quote_widget.apply_theme()
        if hasattr(self, 'rss_widget') and self.rss_widget:
            self.rss_widget.apply_theme()

    def get_current_color_scheme(self):
        """Returns the currently active color scheme dictionary."""
        return color_schemes[self.active_scheme_key]

    def toggle_box(self):
        self.boxed_style = not self.boxed_style
        print(f"[CalendarWidget] Toggling box style to: {self.boxed_style}") # Debug
        self.settings.setValue("boxed", "yes" if self.boxed_style else "no")
        self.build_ui()
        
        # Complete recreation of the quote widget when box style changes
        if hasattr(self, 'quote_widget') and self.quote_widget:
            print(f"[CalendarWidget] Recreating quote_widget with boxed_style = {self.boxed_style}") # Debug
            
            # Save current state
            was_visible = self.quote_widget.isVisible()
            last_pos = self.quote_widget.pos()
            
            # Close the current widget
            self.quote_widget.close()
            self.quote_widget.deleteLater()
            
            # Create a new one
            self.quote_widget = QuoteWidget(self, self.settings, self.font_pt, self.boxed_style)
            
            # Restore state
            if last_pos:
                self.quote_widget.move(last_pos)
            if was_visible:
                self.quote_widget.show()
                self.quote_widget.raise_()

        # Complete recreation of the rss widget when box style changes
        if hasattr(self, 'rss_widget') and self.rss_widget:
            print(f"[CalendarWidget] Recreating rss_widget with boxed_style = {self.boxed_style}")
            
            # Save current state
            rss_was_visible = self.rss_widget.isVisible()
            rss_last_pos = self.rss_widget.pos()
            
            # Close the current widget
            self.rss_widget.close()
            self.rss_widget.deleteLater()
            
            # Create a new one
            self.rss_widget = RSSReaderWidget(self, self.settings, self.font_pt, self.boxed_style)
            
            # Restore state
            if rss_last_pos:
                self.rss_widget.move(rss_last_pos)
            if rss_was_visible:
                self.rss_widget.show()
                self.rss_widget.raise_()

    def toggle_compact(self):self.compact_mode=not self.compact_mode;self.settings.setValue("compact","yes" if self.compact_mode else "no");self.build_ui() 
    def set_font_size(self, lbl):
        self.font_size_lbl = lbl
        self.font_pt = font_sizes[lbl]
        self.settings.setValue("font_size", lbl)
        self.build_ui()
        if hasattr(self, 'quote_widget') and self.quote_widget:
            self.quote_widget.update_display_settings(font_pt=self.font_pt)
        if hasattr(self, 'rss_widget') and self.rss_widget:
            self.rss_widget.update_display_settings(font_pt=self.font_pt) 

    def _handle_quote_frequency_change(self):
        action = self.sender()
        if action and action.isChecked():
            new_frequency = action.data()
            if self.quote_widget:
                self.quote_widget.set_quote_settings(frequency=new_frequency)
            else: # Save directly if quote widget not yet fully initialized or visible
                self.settings.setValue("quote_widget/frequency", new_frequency)
            # No need to rebuild UI, quote widget handles its own update

    def _handle_quote_width_change(self):
        action = self.sender()
        if action and action.isChecked():
            new_width_key = action.data()
            self.settings.setValue("quote_widget/width_key", new_width_key) # Save setting immediately
            if self.quote_widget:
                self.quote_widget.update_display_settings(width_key=new_width_key)
            # If quote_widget is None, it will pick up the new width_key from settings upon its initialization.

    def _show_edit_quotes_dialog(self):
        if hasattr(self, 'quote_widget') and self.quote_widget:
            initial_quotes = getattr(self.quote_widget, 'quotes_list', [])
            if not isinstance(initial_quotes, list):
                initial_quotes = []

            dialog = ManageQuotesDialog(initial_quotes, self)
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                updated_quotes = dialog.get_updated_quotes()
                if updated_quotes != initial_quotes:
                    self.quote_widget.set_quote_settings(
                        quotes=updated_quotes, 
                        frequency=self.quote_widget.quote_update_frequency
                    )
        else:
            print("Quote widget not available to edit quotes.")

    def toggle_quote_widget_visibility_action(self):
        if not hasattr(self, 'quote_widget') or not self.quote_widget:
            self.init_quote_widget() # Ensure it's created if called early

        if hasattr(self, 'quote_widget') and self.quote_widget:
            is_now_visible = not self.quote_widget.isVisible()
            self.quote_widget.setVisible(is_now_visible)
            self.settings.setValue("quote_widget/is_visible", is_now_visible)

    def _show_manage_rss_feeds_dialog(self):
        if not hasattr(self, 'rss_widget') or not self.rss_widget:
            self.init_rss_widget() # Ensure it's created
            if not self.rss_widget: # Still not created, something is wrong
                print("[CalendarWidget] Error: RSS Widget could not be initialized for managing feeds.")
                # Optionally, show a QMessageBox to the user
                return

        current_feeds_list = list(self.rss_widget.feeds_data) # Pass a copy
        dialog = ManageRSSFeedsDialog(current_feeds_list, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_feeds = dialog.get_updated_feeds()
            self.rss_widget.set_feeds(updated_feeds)
            # No need to save to self.settings here, rss_widget.save_settings() will handle it.
            # self.settings.setValue("rss_widget/feeds_list", updated_feeds) # This is done in rss_widget.save_settings
            print(f"[CalendarWidget] RSS feeds updated by dialog: {updated_feeds}")
        else:
            print("[CalendarWidget] RSS feed management dialog cancelled.")

    def _handle_rss_box_width_change(self):
        action = self.sender()
        if action and hasattr(self, 'rss_widget') and self.rss_widget:
            new_width_key = action.data()
            self.rss_widget.update_display_settings(width_key=new_width_key)
            # self.settings.setValue("rss_widget/width_key", new_width_key) # RSSReaderWidget.save_settings() handles this now
            print(f"[CalendarWidget] RSS widget width key set to: {new_width_key}")

    def toggle_rss_widget_visibility_action(self):
        if not hasattr(self, 'rss_widget') or not self.rss_widget:
            self.init_rss_widget() # Ensure it's created if called early

        if hasattr(self, 'rss_widget') and self.rss_widget:
            is_now_visible = not self.rss_widget.isVisible()
            self.rss_widget.setVisible(is_now_visible)
            self.settings.setValue("rss_widget/is_visible", is_now_visible)

    def get_element_style(self, boxed, is_button=False):
        scheme = color_schemes[self.active_scheme_key]
        padding_value = "padding: 4px 6px;" 
        border_radius_value = "border-radius: 6px;"
        
        # Base properties
        base_bg_color_str = ""
        base_text_color_str = f"color: {scheme['widget_text'].name(QColor.NameFormat.HexArgb)};"
        border_style_str = "border: none;"

        if boxed: 
            base_bg_color_str = f"background-color: {scheme['box_bg'].name(QColor.NameFormat.HexArgb)};"
            base_text_color_str = f"color: {scheme['box_text'].name(QColor.NameFormat.HexArgb)};"
            base_border_color = scheme['box_border']
            lighter_border = base_border_color.lighter(130).name(QColor.NameFormat.HexArgb)
            darker_border = base_border_color.darker(130).name(QColor.NameFormat.HexArgb)   
            border_style_str = (f"border-width: 1px; border-style: solid;"
                               f"border-top-color: {lighter_border}; border-left-color: {lighter_border};"
                               f"border-bottom-color: {darker_border}; border-right-color: {darker_border};")
        else: # Not boxed (flat)
            base_bg_color_str = "background-color: transparent;"
        
        base_style = f"{base_bg_color_str} {base_text_color_str} {border_style_str} {padding_value} {border_radius_value if boxed else 'border-radius: 4px;'}" # smaller radius for flat

        if is_button:
            hover_bg_color_str = ""
            if boxed:
                hover_bg_color_str = f"background-color: {scheme['box_bg_hover'].name(QColor.NameFormat.HexArgb)};"
            else: # Flat button hover
                hover_bg_color_str = f"background-color: {scheme['flat_hover_bg'].name(QColor.NameFormat.HexArgb)};"
            
            # For flat buttons, we might not want to change text color or border on hover
            # For boxed buttons, the existing border and text color from base_style might be fine for hover too
            # Or you can define specific hover text/border colors in scheme
            hover_style_specifics = f"{hover_bg_color_str}" # Add other hover specifics if needed

            selector = "QPushButton" # Could be more specific if needed
            return f"{selector} {{ {base_style} }} {selector}:hover {{ {hover_style_specifics} }}"
        else: # For QLabels
            selector = "QLabel"
            return f"{selector} {{ {base_style} }}"


    def shadow(self):s=QGraphicsDropShadowEffect();s.setColor(QColor(0,0,0,100));s.setBlurRadius(8);s.setOffset(1,1);return s
    def center_on_screen(self):self.adjustSize();scr=QApplication.primaryScreen().availableGeometry();self.move((scr.width()-self.width())//2+scr.left(),(scr.height()-self.height())//2+scr.top())
    def mousePressEvent(self,e):
        if e.button()==Qt.MouseButton.LeftButton:self.old_pos=e.globalPosition().toPoint();e.accept()
    def mouseMoveEvent(self,e):
        if e.buttons()==Qt.MouseButton.LeftButton and self.old_pos is not None:
            d=QPoint(e.globalPosition().toPoint()-self.old_pos);self.move(self.x()+d.x(),self.y()+d.y());self.old_pos=e.globalPosition().toPoint();e.accept()
    def mouseReleaseEvent(self,e):
        if e.button()==Qt.MouseButton.LeftButton and self.old_pos is not None:self.settings.setValue("pos",self.pos());self.old_pos=None;e.accept()
    def closeEvent(self,e):
        self.settings.setValue("pos",self.pos())
        if hasattr(self, 'quote_widget') and self.quote_widget:
            # Save the quote widget's position and other settings
            self.quote_widget.save_settings()
            
            # IMPORTANT: Don't rely on isVisible() at close time as it may be affected by window manager
            # Instead, use the last explicitly set visibility state from settings
            # This ensures the visibility setting persists between sessions correctly
            current_setting = self.settings.value("quote_widget/is_visible", True, type=bool)
            print(f"[CalendarWidget] Persisting quote widget visibility state: {current_setting}")
            
            # Don't save here, as we're using the current setting from storage
            # Only toggle_quote_widget_visibility_action should modify this setting
            self.quote_widget.close()

        if hasattr(self, 'rss_widget') and self.rss_widget:
            self.rss_widget.save_settings()
            rss_current_setting = self.settings.value("rss_widget/is_visible", False, type=bool)
            print(f"[CalendarWidget] Persisting RSS widget visibility state: {rss_current_setting}")
            self.rss_widget.close()
        super().closeEvent(e)

if __name__ == "__main__":
    app=QApplication(sys.argv);w=CalendarWidget();w.show();sys.exit(app.exec())