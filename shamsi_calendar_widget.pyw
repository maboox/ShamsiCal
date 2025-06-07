from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QPushButton, QMenu, QGraphicsDropShadowEffect, QInputDialog,
    QDialog, QListWidget, QLineEdit, QDialogButtonBox, QListWidgetItem
)
from PyQt6.QtGui import QFont, QIcon, QAction, QColor, QActionGroup
from PyQt6.QtCore import Qt, QPoint, QSettings, QTimer, QDateTime # Removed QSize as it's not used
import jdatetime
import random
import time
import requests
from hijri_converter import Gregorian
import sys

DEFAULT_FONT_FAMILY = "DanaFaNum"

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

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        default_quote = self.settings.value("quote_widget/default_quote", "اینجا نقل قول نمایش داده می‌شود.")
        self.quote_label = QLabel("...") # Placeholder, updated by _update_quote_text_display
        
        # Font will be set in apply_theme using self.font_pt
        # current_label_font_size = self.font_pt - 2 if self.font_pt > 10 else self.font_pt
        # current_label_font_size = max(8, current_label_font_size)
        # self.quote_label.setFont(QFont(DEFAULT_FONT_FAMILY, current_label_font_size))
        self.quote_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.quote_label.setWordWrap(True)
        if hasattr(self.parent_widget, 'shadow'):
             self.quote_label.setGraphicsEffect(self.parent_widget.shadow())
        layout.addWidget(self.quote_label)
        self.setLayout(layout)

        # Quote related initializations
        self.quotes_list = []
        self.quote_update_frequency = "daily" # Default: daily, hourly, weekly
        self.last_quote_update_timestamp = 0 # Store as timestamp

        self.quote_timer = QTimer(self)
        self.quote_timer.timeout.connect(self._check_and_update_quote)
        
        self._load_quote_settings_and_start_timer()

        self.apply_theme() 
        self.load_position() 
        # self.adjustSize() # adjustSize will be called in _update_quote_text_display and apply_theme 

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

    def _check_and_update_quote(self):
        current_timestamp = time.time()
        interval_seconds = self._get_interval_seconds()
        
        if (current_timestamp - self.last_quote_update_timestamp) >= interval_seconds:
            self._update_quote_text_display()

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

        self.quote_label.setWordWrap(True)
        self.quote_label.setText(actual_quote_to_display)
        self.setFixedWidth(self.quote_box_width_val) 
        self.quote_label.adjustSize() # Allow label to determine its new height
        self.adjustSize() # Widget adjusts to new label height and fixed width

    def set_quote_settings(self, quotes, frequency):
        self.quotes_list = quotes if quotes else []
        self.quote_update_frequency = frequency
        self.settings.setValue("quote_widget/quotes_list", self.quotes_list)
        self.settings.setValue("quote_widget/frequency", self.quote_update_frequency)
        # Force an immediate update to reflect new settings
        self._update_quote_text_display() 
        # Restart timer with potentially new interval logic (though timer interval is fixed, the check logic changes)
        self._check_and_update_quote() 

    def apply_theme(self):
        if not self.parent_widget: return
        scheme = color_schemes[self.parent_widget.active_scheme_key]

        if self.boxed_style:
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
            bg_color = QColor(scheme.get('box_bg', scheme['widget_bg'])) 
            border_color = QColor(scheme.get('box_border', scheme['menu_border']))
            self.setStyleSheet(
                f"QWidget {{ "
                f"background-color: {bg_color.name(QColor.NameFormat.HexArgb)}; "
                f"border: 1px solid {border_color.name(QColor.NameFormat.HexArgb)}; "
                f"border-radius: 6px; "
                f"}}"
            )
        else:
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            self.setStyleSheet(f"QWidget {{ background-color: transparent; border-radius: 6px; }}")
        
        label_text_color = scheme.get('box_text', scheme['widget_text'])
        self.quote_label.setStyleSheet(f"QLabel {{ color: {label_text_color.name(QColor.NameFormat.HexArgb)}; background-color: transparent; border: none; }}")
        
        current_label_font_size = self.font_pt - 2 if self.font_pt > 10 else self.font_pt
        current_label_font_size = max(8, current_label_font_size)
        self.quote_label.setFont(QFont(DEFAULT_FONT_FAMILY, current_label_font_size))
        
        self._update_quote_text_display() # Update text and apply size constraints

    def update_display_settings(self, font_pt=None, boxed_style=None, width_key=None):
        changed = False
        if font_pt is not None and self.font_pt != font_pt:
            self.font_pt = font_pt
            changed = True
        if boxed_style is not None and self.boxed_style != boxed_style:
            self.boxed_style = boxed_style
            changed = True
        if width_key is not None and self.quote_box_width_key != width_key:
            self.quote_box_width_key = width_key
            self.quote_box_width_val = quote_box_widths.get(width_key, quote_box_widths[DEFAULT_QUOTE_BOX_WIDTH_KEY])
            changed = True
        
        if changed:
            self.apply_theme() # This will also call _update_quote_text_display
            self.save_settings() # Save if settings changed()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.old_pos = e.globalPosition().toPoint()
            e.accept()

    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.MouseButton.LeftButton and self.old_pos is not None:
            delta = QPoint(e.globalPosition().toPoint() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = e.globalPosition().toPoint()
            e.accept()

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and self.old_pos is not None:
            self.save_settings() 
            self.old_pos = None
            e.accept()

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
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ویجت تقویم شمسی")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.old_pos = None 

        self.settings = QSettings("MyCompany", "ShamsiCalendar")
        saved_scheme_name = self.settings.value("color_scheme", "Dark")
        self.active_scheme_key = saved_scheme_name if saved_scheme_name in color_schemes else "Dark"
        self.boxed_style = self.settings.value("boxed", "yes") == "yes"
        self.font_size_lbl = self.settings.value("font_size", "متوسط")
        self.compact_mode = self.settings.value("compact", "no") == "yes"
        self.font_pt = font_sizes.get(self.font_size_lbl, 15)
        self.offset = 0
        self.quote_widget = None # Initialize quote_widget

        self.init_quote_widget() # Create/show quote widget
        self.apply_theme_stylesheet()
        self.load_position() 
        self.build_ui()

    def init_quote_widget(self):
        if not self.quote_widget:
            self.quote_widget = QuoteWidget(self, self.settings, self.font_pt, self.boxed_style)
        
        quote_widget_visible = self.settings.value("quote_widget/is_visible", True, type=bool)
        if self.quote_widget: # Ensure it was created
            if quote_widget_visible:
                self.quote_widget.show()
            else:
                self.quote_widget.hide()

    def apply_theme_stylesheet(self):
        scheme = color_schemes[self.active_scheme_key]
        self.setStyleSheet(f"QWidget {{ background-color: {scheme['widget_bg'].name(QColor.NameFormat.HexArgb)}; color: {scheme['widget_text'].name(QColor.NameFormat.HexArgb)}; }}")
        if hasattr(self, 'quote_widget') and self.quote_widget:
            self.quote_widget.apply_theme()

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
        self.top_settings_btn = QPushButton("⚙️")
        settings_icon_font_size = max(10, int(self.font_pt * 0.8))
        self.top_settings_btn.setFont(QFont(DEFAULT_FONT_FAMILY, settings_icon_font_size))
        self.top_settings_btn.setFixedSize(26, 26) # Adjusted size
        self.top_settings_btn.setFlat(True)
        # Hover style for top_settings_btn will be set in update_date
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
        
        # Functions remain standard: left goes to previous, right goes to next
        self.nav_left_button.clicked.connect(self.prev_day) 
        self.nav_right_button.clicked.connect(self.next_day)
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

            bottom_buttons_layout = QHBoxLayout()
            self.today_btn = QPushButton("بازگشت به امروز")
            self.center_widget_btn = QPushButton("مرکز صفحه")
            
            action_buttons = [self.today_btn, self.center_widget_btn]
            for btn in action_buttons:
                btn.setFont(QFont(DEFAULT_FONT_FAMILY, secondary_font_size))
                btn.setFlat(True) 
                btn.setGraphicsEffect(self.shadow()) 
            
            self.today_btn.clicked.connect(self.reset_today)
            self.center_widget_btn.clicked.connect(self.center_widget_action) 

            bottom_buttons_layout.addStretch(1)
            bottom_buttons_layout.addWidget(self.today_btn)
            bottom_buttons_layout.addSpacing(10) 
            bottom_buttons_layout.addWidget(self.center_widget_btn)
            bottom_buttons_layout.addStretch(1)
            
            main_layout.addLayout(bottom_buttons_layout)

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
                try:
                    url=f"https://holidayapi.ir/jalali/{today.year}/{today.month:02}/{today.day:02}"; data=requests.get(url,timeout=5).json()
                    ev=[e["description"] for e in data.get("events",[])]; self.event_label.setText("مناسبت: "+"، ".join(ev) if ev else "مناسبت: ---")
                except: self.event_label.setText("مناسبت: (خطا در دریافت)")
        
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

        menu.addMenu(quote_settings_menu)
        menu.addSeparator()

        menu.addAction("❌ خروج", QApplication.instance().quit)
        btn_global_pos = self.top_settings_btn.mapToGlobal(QPoint(0, self.top_settings_btn.height()))
        menu.exec(btn_global_pos)

    def set_color_scheme(self,k):self.active_scheme_key=k;self.settings.setValue("color_scheme",k);self.apply_theme_stylesheet();self.update_date() 
    def toggle_box(self):
        self.boxed_style = not self.boxed_style
        self.settings.setValue("boxed", "yes" if self.boxed_style else "no")
        self.build_ui()
        if hasattr(self, 'quote_widget') and self.quote_widget:
            self.quote_widget.update_display_settings(boxed_style=self.boxed_style)
    def toggle_compact(self):self.compact_mode=not self.compact_mode;self.settings.setValue("compact","yes" if self.compact_mode else "no");self.build_ui() 
    def set_font_size(self, lbl):
        self.font_size_lbl = lbl
        self.font_pt = font_sizes[lbl]
        self.settings.setValue("font_size", lbl)
        self.build_ui()
        if hasattr(self, 'quote_widget') and self.quote_widget:
            self.quote_widget.update_display_settings(font_pt=self.font_pt) 

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
            self.quote_widget.save_settings()
            self.settings.setValue("quote_widget/is_visible", self.quote_widget.isVisible())
            self.quote_widget.close()
        super().closeEvent(e)

if __name__ == "__main__":
    app=QApplication(sys.argv);w=CalendarWidget();w.show();sys.exit(app.exec())