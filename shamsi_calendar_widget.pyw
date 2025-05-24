from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QPushButton, QMenu, QGraphicsDropShadowEffect
)
from PyQt6.QtGui import QFont, QIcon, QAction, QColor
from PyQt6.QtCore import Qt, QPoint, QSettings # Removed QSize as it's not used
import jdatetime
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

        self.apply_theme_stylesheet()
        self.load_position() 
        self.build_ui()

    def apply_theme_stylesheet(self):
        scheme = color_schemes[self.active_scheme_key]
        self.setStyleSheet(f"QWidget {{ background-color: {scheme['widget_bg'].name(QColor.NameFormat.HexArgb)}; color: {scheme['widget_text'].name(QColor.NameFormat.HexArgb)}; }}")

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
        menu = QMenu(self); scheme = color_schemes[self.active_scheme_key]
        menu_style = f"""
            QMenu {{background-color:{scheme['menu_bg'].name(QColor.NameFormat.HexArgb)};color:{scheme['menu_text'].name(QColor.NameFormat.HexArgb)};border:1px solid {scheme['menu_border'].name(QColor.NameFormat.HexArgb)};padding:4px;}}
            QMenu::item {{padding:5px 20px;border-radius:4px;}} QMenu::item:selected {{background-color:{scheme['menu_selected_bg'].name(QColor.NameFormat.HexArgb)};color:{scheme['menu_selected_text'].name(QColor.NameFormat.HexArgb)};}}
            QMenu::separator {{height:1px;background-color:{scheme['menu_border'].name(QColor.NameFormat.HexArgb)};margin:4px 5px;}}"""
        menu.setStyleSheet(menu_style)
        theme_menu=QMenu("🎨 تغییر پوسته",menu); theme_menu.setStyleSheet(menu_style)
        for k,v in color_schemes.items(): a=QAction(v['name_fa'],self,checkable=True);a.setChecked(k==self.active_scheme_key);a.triggered.connect(lambda c,key=k:self.set_color_scheme(key));theme_menu.addAction(a)
        menu.addMenu(theme_menu)
        menu.addAction("🔳 باکس روشن/خاموش",self.toggle_box); menu.addAction("📏 حالت ساده/کامل",self.toggle_compact)
        font_menu=QMenu("🔠 اندازه فونت",menu); font_menu.setStyleSheet(menu_style)
        for lbl in font_sizes:a=QAction(lbl,self,checkable=True);a.setChecked(lbl==self.font_size_lbl);a.triggered.connect(lambda c,l=lbl:self.set_font_size(l));font_menu.addAction(a)
        menu.addMenu(font_menu)
        menu.addSeparator(); menu.addAction("❌ خروج",QApplication.instance().quit)
        btn_global_pos = self.top_settings_btn.mapToGlobal(QPoint(0, self.top_settings_btn.height()))
        menu.exec(btn_global_pos)

    def set_color_scheme(self,k):self.active_scheme_key=k;self.settings.setValue("color_scheme",k);self.apply_theme_stylesheet();self.update_date() 
    def toggle_box(self):self.boxed_style=not self.boxed_style;self.settings.setValue("boxed","yes" if self.boxed_style else "no");self.update_date()
    def toggle_compact(self):self.compact_mode=not self.compact_mode;self.settings.setValue("compact","yes" if self.compact_mode else "no");self.build_ui() 
    def set_font_size(self,lbl):self.font_size_lbl=lbl;self.font_pt=font_sizes[lbl];self.settings.setValue("font_size",lbl);self.build_ui() 

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
    def closeEvent(self,e):self.settings.setValue("pos",self.pos());super().closeEvent(e)

if __name__ == "__main__":
    app=QApplication(sys.argv);w=CalendarWidget();w.show();sys.exit(app.exec())