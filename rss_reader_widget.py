from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QSizePolicy, QScrollArea, QFrame, 
    QLineEdit, QListWidget, QListWidgetItem, QDialogButtonBox, QDialog, QApplication, QComboBox,
    QTextEdit, QMessageBox, QInputDialog
)
# For DeepSeek API - ensure you have 'openai' installed: pip install openai
from openai import OpenAI
import requests
from newspaper import Article, ArticleException
from PyQt6.QtGui import QFont, QColor, QDesktopServices, QAction, QPainter, QBrush, QPen
from PyQt6.QtCore import Qt, QPoint, QSettings, QTimer, QUrl
import feedparser
import webbrowser
import types
from bs4 import BeautifulSoup

# Assuming color_schemes and DEFAULT_FONT_FAMILY are accessible 
# or will be passed/imported appropriately from the main widget.
# For now, we'll define placeholders if needed or assume they are passed via parent.

DEFAULT_RSS_BOX_WIDTH_KEY = "متوسط"
RSS_BOX_WIDTHS = {"باریک": 250, "متوسط": 350, "عریض": 450} # Width in pixels

class RSSReaderWidget(QWidget):
    def __init__(self, parent_widget, settings, initial_font_pt, initial_boxed_style):
        super().__init__(parent_widget)
        self.parent_widget = parent_widget
        self.settings = settings
        self.font_pt = initial_font_pt
        self.boxed_style = initial_boxed_style
        self.rss_box_width_key = self.settings.value("rss_widget/width_key", DEFAULT_RSS_BOX_WIDTH_KEY)
        self.rss_box_width_val = RSS_BOX_WIDTHS.get(self.rss_box_width_key, RSS_BOX_WIDTHS[DEFAULT_RSS_BOX_WIDTH_KEY])
        self.old_pos = None

        self.feeds_data = []  # List of dicts: {'url': 'feed_url', 'name': 'Feed Name', 'items': []}
        self.current_feed_index = 0
        self.current_item_index = -1 # -1 means no item selected or no items

        self.setWindowTitle("منبع خوان RSS")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setMouseTracking(True)
        self.togetherai_api_token = self.settings.value("togetherai/api_token", "")

        self._init_ui()
        self._load_rss_settings_and_feeds()
        self.apply_theme()
        self.load_position()
        QTimer.singleShot(100, self._ensure_proper_size)

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        # Header for Feed Name and Refresh
        header_layout = QHBoxLayout()
        self.feed_source_label = QLabel("منبع: -")
        self.feed_source_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        header_layout.addWidget(self.feed_source_label)
        header_layout.addStretch()

        # --- Feed Navigation Buttons ---
        self.prev_feed_button = QPushButton("⏪") # Previous Feed
        self.prev_feed_button.setToolTip("منبع قبلی")
        self.prev_feed_button.setFixedSize(28, 28)
        self.prev_feed_button.clicked.connect(self._prev_feed_source)
        header_layout.addWidget(self.prev_feed_button)

        self.next_feed_button = QPushButton("⏩") # Next Feed
        self.next_feed_button.setToolTip("منبع بعدی")
        self.next_feed_button.setFixedSize(28, 28)
        self.next_feed_button.clicked.connect(self._next_feed_source)
        header_layout.addWidget(self.next_feed_button)

        # --- Item Navigation Buttons (Moved from footer to header) ---
        self.prev_button = QPushButton("◀️") # Changed icon
        self.prev_button.setToolTip("مورد قبلی")
        self.prev_button.setFixedSize(28, 28)
        self.prev_button.clicked.connect(self.prev_item)
        header_layout.addWidget(self.prev_button)

        self.next_button = QPushButton("▶️") # Changed icon
        self.next_button.setToolTip("مورد بعدی")
        self.next_button.setFixedSize(28, 28)
        self.next_button.clicked.connect(self.next_item)
        header_layout.addWidget(self.next_button)

        self.open_link_button = QPushButton("🔗") # Icon for open link
        self.open_link_button.setToolTip("باز کردن لینک مورد") # Updated tooltip
        self.open_link_button.setFixedSize(28,28)
        self.open_link_button.clicked.connect(self._open_current_item_link)
        self.open_link_button.setEnabled(False)
        header_layout.addWidget(self.open_link_button)

        self.refresh_button = QPushButton("🔄") # Refresh Icon
        self.refresh_button.setToolTip("بارگذاری مجدد منبع")
        self.refresh_button.setFixedSize(28, 28)
        self.refresh_button.clicked.connect(self.refresh_current_feed)
        header_layout.addWidget(self.refresh_button)

        self.summarize_button = QPushButton("✨") # Icon for Summarize/Translate
        self.summarize_button.setToolTip("خلاصه و ترجمه خبر (Together.AI)")
        self.summarize_button.setFixedSize(28, 28)
        self.summarize_button.clicked.connect(self._handle_summarize_action)
        self.summarize_button.setEnabled(False) # Initially disabled
        header_layout.addWidget(self.summarize_button)

        self.main_layout.addLayout(header_layout)

        # Content Area
        self.title_label = QLabel("عنوان خبر")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.title_label.setWordWrap(True)
        self.title_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        self.title_label.setOpenExternalLinks(True) # For any links in title

        self.content_scroll_area = QScrollArea()
        self.content_scroll_area.setWidgetResizable(True)
        self.content_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.content_scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.content_label = QLabel("محتوای خبر...")
        self.content_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        self.content_label.setWordWrap(True)
        self.content_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        self.content_label.setOpenExternalLinks(True)
        self.content_scroll_area.setWidget(self.content_label)
        
        self.main_layout.addWidget(self.title_label)
        self.main_layout.addWidget(self.content_scroll_area, 1) # Stretch factor for content

        # Only apply shadows if we're not in boxed mode
        if not self.boxed_style and hasattr(self.parent_widget, 'shadow'):
            for widget in [self.title_label, self.content_label, self.feed_source_label]:
                widget.setGraphicsEffect(self.parent_widget.shadow())
        
        self.setLayout(self.main_layout)

    def _load_rss_settings_and_feeds(self):
        loaded_feeds = self.settings.value("rss_widget/feeds_list", [])
        self.feeds_data = []
        for feed in loaded_feeds:
            if not isinstance(feed, dict):
                # Handle potential data corruption or older format if necessary
                print(f"Skipping malformed feed data: {feed}")
                continue
            if 'direction' not in feed:
                feed['direction'] = 'rtl'  # Default to RTL for older saved feeds
            self.feeds_data.append(feed)
            
        self.current_feed_index = self.settings.value("rss_widget/current_feed_index", 0, type=int)
        self.current_item_index = self.settings.value("rss_widget/current_item_index", -1, type=int)
        
        if not self.feeds_data:
            self._update_display() # Show empty state
            return

        # Ensure current_feed_index is valid
        if not 0 <= self.current_feed_index < len(self.feeds_data):
            self.current_feed_index = 0
        
        self.fetch_feed(self.current_feed_index, on_load=True)

    def fetch_feed(self, feed_index, on_load=False):
        if not (0 <= feed_index < len(self.feeds_data)):
            self._update_display() # Show empty state
            return

        feed_info = self.feeds_data[feed_index]
        url = feed_info.get('url')
        if not url:
            self._update_display()
            return

        # Show loading state
        self.title_label.setText("در حال بارگذاری...")
        self.content_label.setText("")
        self.feed_source_label.setText(f"منبع: {feed_info.get('name', url)}")
        QApplication.processEvents() # Ensure UI updates

        try:
            parsed_feed = feedparser.parse(url)
            feed_info['items'] = []
            for entry in parsed_feed.entries:
                title = entry.get('title', 'بدون عنوان')
                link = entry.get('link', '#')
                # Try to get summary, then description, then content
                summary = entry.get('summary', entry.get('description', ''))
                if hasattr(entry, 'content') and entry.content:
                    # feedparser can return a list of content items
                    if isinstance(entry.content, list) and entry.content:
                        summary = entry.content[0].get('value', summary)
                    elif isinstance(entry.content, dict):
                         summary = entry.content.get('value', summary)
                
                # Basic HTML stripping (very rudimentary)
                import re
                summary = re.sub('<[^<]+?>', '', summary).strip()
                summary = summary[:300] + '...' if len(summary) > 300 else summary # Limit content length

                feed_info['items'].append({'title': title, 'link': link, 'summary': summary})
            
            if not on_load: # If it's a refresh, reset to first item
                self.current_item_index = 0 if feed_info['items'] else -1
            else: # On initial load, try to restore last viewed item index
                if not (0 <= self.current_item_index < len(feed_info['items'])):
                    self.current_item_index = 0 if feed_info['items'] else -1

        except Exception as e:
            print(f"Error fetching/parsing RSS feed {url}: {e}")
            feed_info['items'] = []
            self.current_item_index = -1
            self.title_label.setText("خطا در بارگذاری منبع")
            self.content_label.setText(str(e))
        
        self._update_display()

    def _update_display(self):
        if not self.feeds_data or self.current_feed_index >= len(self.feeds_data):
            self.feed_source_label.setText("منبع: (خالی)")
            self.title_label.setText("هیچ منبعی انتخاب نشده یا منبع خالی است.")
            self.content_label.setText("لطفا از طریق تنظیمات، منبع RSS اضافه کنید.")
            self.open_link_button.setEnabled(False)
            self.prev_button.setEnabled(False)
            self.next_button.setEnabled(False)
            self.summarize_button.setEnabled(False)
            self.prev_feed_button.setEnabled(False) # Disable feed nav if no feeds
            self.next_feed_button.setEnabled(False) # Disable feed nav if no feeds
            # Default alignment for empty state
            text_align = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            content_align = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop
            self.feed_source_label.setAlignment(text_align)
            self.title_label.setAlignment(text_align)
            self.content_label.setAlignment(content_align)
            return

        current_feed_data = self.feeds_data[self.current_feed_index]
        feed_name = current_feed_data.get('name', 'بی نام')
        feed_direction = current_feed_data.get('direction', 'rtl') # Default to RTL

        if feed_direction == 'ltr':
            text_align = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            content_align = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
            self.feed_source_label.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
            self.title_label.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
            self.content_label.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        else: # RTL
            text_align = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            content_align = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop
            self.feed_source_label.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            self.title_label.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            self.content_label.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self.feed_source_label.setAlignment(text_align)
        self.title_label.setAlignment(text_align)
        self.content_label.setAlignment(content_align)

        self.feed_source_label.setText(f"منبع: {feed_name} ({self.current_feed_index + 1}/{len(self.feeds_data)})")

        items = current_feed_data.get('items', [])
        if not items:
            self.title_label.setText("هیچ موردی در این منبع یافت نشد.")
            self.content_label.setText("ممکن است لازم باشد منبع را بروزرسانی کنید.")
            self.open_link_button.setEnabled(False)
            self.prev_button.setEnabled(len(items) > 1)
            self.next_button.setEnabled(len(items) > 1)
            self.summarize_button.setEnabled(False)
            return

        if not 0 <= self.current_item_index < len(items):
            self.current_item_index = 0 # Default to first item if index is bad
            if not items: # Double check after potential reset
                 self.title_label.setText("موردی برای نمایش نیست")
                 self.content_label.setText("")
                 self.open_link_button.setEnabled(False)
                 self.summarize_button.setEnabled(False)
                 return

        item = items[self.current_item_index]
        title = item.get('title', 'بدون عنوان')
        summary = item.get('summary', 'بدون خلاصه')
        link = item.get('link', None)

        self.title_label.setText(title)
        self.content_label.setText(summary)
        self.open_link_button.setEnabled(bool(link))
        self.summarize_button.setEnabled(bool(summary)) # Enable if there's summary content

        self.prev_button.setEnabled(len(items) > 1)
        self.next_button.setEnabled(len(items) > 1)

        # Enable/disable feed navigation buttons
        can_navigate_feeds = len(self.feeds_data) > 1
        self.prev_feed_button.setEnabled(can_navigate_feeds)
        self.next_feed_button.setEnabled(can_navigate_feeds)
        
        self.content_label.adjustSize() # Recalculate size for scroll area
        self.adjustSize()

    def _prev_feed_source(self):
        if not self.feeds_data or len(self.feeds_data) <= 1:
            return
        self.current_feed_index -= 1
        if self.current_feed_index < 0:
            self.current_feed_index = len(self.feeds_data) - 1
        self.current_item_index = -1 # Reset item index for new feed
        self.fetch_feed(self.current_feed_index)
        self.settings.setValue("rss_widget/current_feed_index", self.current_feed_index)

    def _next_feed_source(self):
        if not self.feeds_data or len(self.feeds_data) <= 1:
            return
        self.current_feed_index += 1
        if self.current_feed_index >= len(self.feeds_data):
            self.current_feed_index = 0
        self.current_item_index = -1 # Reset item index for new feed
        self.fetch_feed(self.current_feed_index)
        self.settings.setValue("rss_widget/current_feed_index", self.current_feed_index)

    def refresh_current_feed(self):
        if self.feeds_data and 0 <= self.current_feed_index < len(self.feeds_data):
            self.fetch_feed(self.current_feed_index)

    def next_item(self):
        if not self.feeds_data or not (0 <= self.current_feed_index < len(self.feeds_data)):
            return
        items = self.feeds_data[self.current_feed_index].get('items', [])
        if not items: return
        self.current_item_index = (self.current_item_index + 1) % len(items)
        self._update_display()
        self.save_settings() # Save current item index

    def prev_item(self):
        if not self.feeds_data or not (0 <= self.current_feed_index < len(self.feeds_data)):
            return
        items = self.feeds_data[self.current_feed_index].get('items', [])
        if not items: return
        self.current_item_index = (self.current_item_index - 1 + len(items)) % len(items)
        self._update_display()
        self.save_settings() # Save current item index

    def _open_current_item_link(self):
        if not self.feeds_data or not (0 <= self.current_feed_index < len(self.feeds_data)):
            return
        items = self.feeds_data[self.current_feed_index].get('items', [])
        if items and 0 <= self.current_item_index < len(items):
            link = items[self.current_item_index].get('link')
            if link:
                QDesktopServices.openUrl(QUrl(link))

    def set_feeds(self, feeds_list):
        """ Called from settings dialog to update the list of feeds. """
        self.feeds_data = feeds_list
        self.current_feed_index = 0
        self.current_item_index = -1
        if self.feeds_data:
            self.fetch_feed(self.current_feed_index, on_load=True)
        else:
            self._update_display()
        self.save_settings()

    def apply_theme(self):
        if not self.parent_widget: return
        # Assuming parent_widget has active_scheme_key and color_schemes
        scheme = self.parent_widget.get_current_color_scheme()
        was_visible = self.isVisible()
        if was_visible: self.hide()

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setStyleSheet("") # Clear existing stylesheet

        # Override paintEvent for background
        def paintEvent(self, event):
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            if self.boxed_style:
                bg_color = QColor(scheme.get('box_bg', scheme['widget_bg']))
                border_color = QColor(scheme.get('box_border', scheme['menu_border']))
                painter.setBrush(QBrush(bg_color))
                painter.setPen(QPen(border_color, 1))
                painter.drawRoundedRect(self.rect(), 6, 6)
            else:
                pass # Transparent in non-boxed
            super(RSSReaderWidget, self).paintEvent(event)
        self.paintEvent = types.MethodType(paintEvent, self)
        
        # Style UI elements
        text_color = scheme.get('box_text' if self.boxed_style else 'widget_text', scheme['widget_text'])
        
        # Style labels based on boxed mode
        if self.boxed_style:
            # In boxed mode, make all content containers and labels transparent
            for widget in [self.feed_source_label, self.title_label, self.content_label]:
                widget.setStyleSheet(f"color: {text_color.name(QColor.NameFormat.HexArgb)}; background-color: transparent; border: none; padding: 0px;")
        else:
            # In non-boxed mode, ensure labels have transparent backgrounds
            for widget in [self.feed_source_label, self.title_label, self.content_label]:
                widget.setStyleSheet(f"color: {text_color.name(QColor.NameFormat.HexArgb)}; background-color: transparent; border: none;")
        
        # Always make scroll areas transparent
        self.content_scroll_area.setStyleSheet("background-color: transparent; border: none;")
        self.content_scroll_area.viewport().setStyleSheet("background-color: transparent;")
        
        # Apply font sizes
        font_size_title = self.font_pt
        font_size_content = self.font_pt - 2 if self.font_pt > 10 else self.font_pt
        font_size_source = self.font_pt - 3 if self.font_pt > 11 else max(8, self.font_pt -2)

        self.feed_source_label.setFont(QFont(self.parent_widget.DEFAULT_FONT_FAMILY, font_size_source))
        self.title_label.setFont(QFont(self.parent_widget.DEFAULT_FONT_FAMILY, font_size_title, QFont.Weight.Bold))
        self.content_label.setFont(QFont(self.parent_widget.DEFAULT_FONT_FAMILY, font_size_content))

        # Style buttons (using parent's get_element_style method)
        if hasattr(self.parent_widget, 'get_element_style'):
            btn_style = self.parent_widget.get_element_style(element_should_have_own_box=self.boxed_style, is_button=True)
            for btn in [self.refresh_button, self.prev_button, self.next_button, self.open_link_button, self.prev_feed_button, self.next_feed_button]:
                btn.setStyleSheet(btn_style)
    
        self.update()
        self.repaint()
        QApplication.processEvents()
        if was_visible: self.show(); self.raise_()
        self._ensure_proper_size()

    def update_display_settings(self, font_pt=None, boxed_style=None, width_key=None):
        if font_pt is not None:
            self.font_pt = font_pt
        if boxed_style is not None:
            self.boxed_style = boxed_style
        if width_key is not None:
            self.rss_box_width_key = width_key
            self.rss_box_width_val = RSS_BOX_WIDTHS.get(width_key, RSS_BOX_WIDTHS[DEFAULT_RSS_BOX_WIDTH_KEY])
            self.setFixedWidth(self.rss_box_width_val)

        self.apply_theme()
        self._update_display() # Re-flow text and adjust size
        self.save_settings()

    def _ensure_proper_size(self):
        self.setFixedWidth(self.rss_box_width_val)
        self.adjustSize()
        # Potentially adjust scroll area's content label minimum height if needed after text set
        self.content_label.setMinimumWidth(self.rss_box_width_val - 40) # margins for scroll area
        self.content_label.adjustSize()
        self.adjustSize()

    def load_position(self):
        pos = self.settings.value("rss_widget/pos", None)
        if pos:
            self.move(pos)
        elif self.parent_widget:
            # Default position logic (e.g., next to parent)
            parent_geo = self.parent_widget.geometry()
            screen_geo = QApplication.primaryScreen().availableGeometry()
            x = parent_geo.right() + 10 
            y = parent_geo.top() + parent_geo.height() + 10 # Below parent
            temp_width = self.sizeHint().width() + 20
            temp_height = self.sizeHint().height() + 20
            if x + temp_width > screen_geo.right(): x = parent_geo.left() - temp_width - 10
            if x < screen_geo.left(): x = screen_geo.left()
            if y + temp_height > screen_geo.bottom(): y = screen_geo.bottom() - temp_height
            if y < screen_geo.top(): y = screen_geo.top()
            self.move(x,y)

    def save_settings(self):
        if self.isVisible():
            self.settings.setValue("rss_widget/pos", self.pos())
        # Save other settings like feeds_list, current_feed_index, current_item_index, width_key
        self.settings.setValue("rss_widget/feeds_list", self.feeds_data) 
        self.settings.setValue("rss_widget/current_feed_index", self.current_feed_index)
        self.settings.setValue("rss_widget/current_item_index", self.current_item_index)
        self.settings.setValue("rss_widget/width_key", self.rss_box_width_key)
        # Visibility is saved by the main CalendarWidget

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
            self.save_settings() # Save position
            self.old_pos = None
            e.accept()

    def closeEvent(self, event):
        self.save_settings()
        super().closeEvent(event)

    def _fetch_and_extract_article_text(self, url):
        try:
            # Configure the article object, disable memoization for fresh fetches if needed
            # Newspaper3k uses requests internally, so User-Agent might be set by its defaults
            # or can be configured if necessary.
            article = Article(url, language='en') # Specify language if known, helps with parsing
            article.download()
            article.parse()
            
            # article.nlp() # Uncomment this if you want to use NLP features like keywords (requires nltk data)
            
            print(f"[Newspaper3k] Extracted text length for {url}: {len(article.text if article.text else '')}")

            if not article.text or article.text.strip() == "":
                # Fallback to basic BeautifulSoup extraction if newspaper3k fails to get text
                print(f"Newspaper3k failed to extract text from {url}. Falling back to manual parsing.")
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                response = requests.get(url, headers=headers, timeout=15)
                response.raise_for_status()
                try:
                    html_content = response.content.decode('utf-8')
                except UnicodeDecodeError:
                    html_content = response.text
                soup = BeautifulSoup(html_content, 'html.parser')
                for script_or_style in soup(['script', 'style']):
                    script_or_style.decompose()
                text = soup.get_text(separator='\n', strip=True)
                if not text or text.strip() == "":
                     return None, "محتوای قابل استخراجی از لینک یافت نشد (حتی با روش جایگزین)."
                return text.strip(), None

            return article.text.strip(), None
        except ArticleException as e:
            print(f"Newspaper3k ArticleException for URL {url}: {e}")
            return None, f"خطا در پردازش مقاله با کتابخانه newspaper3k: {e}"
        except requests.exceptions.Timeout:
            print(f"Timeout fetching URL {url}")
            return None, f"خطا: زمان درخواست از لینک {url} به پایان رسید."
        except requests.exceptions.RequestException as e:
            print(f"Error fetching URL {url} (requests): {e}")
            return None, f"خطای شبکه هنگام دسترسی به لینک: {e}"
        except Exception as e:
            print(f"Unexpected error processing URL {url}: {e}")
            return None, f"خطا در پردازش محتوای لینک: {e}"

    def _handle_summarize_action(self):
        if not self.feeds_data or self.current_feed_index >= len(self.feeds_data):
            return
        current_feed_data = self.feeds_data[self.current_feed_index]
        items = current_feed_data.get('items', [])
        if not items or not (0 <= self.current_item_index < len(items)):
            return

        # API Token Check
        if not self.togetherai_api_token and self.settings:
            self.togetherai_api_token = self.settings.value("togetherai/api_token", "")

        if not self.togetherai_api_token:
            token, ok = QInputDialog.getText(self,
                                             "کلید API Together.AI",
                                             "کلید API برای Together.AI تنظیم نشده است. لطفاً آن را وارد کنید:",
                                             QLineEdit.EchoMode.Password)
            if ok and token:
                self.togetherai_api_token = token
                if self.settings:
                    self.settings.setValue("togetherai/api_token", token)
                    print("[RSSReaderWidget] Together.AI API Token saved to settings.")
                else:
                    QMessageBox.warning(self, "خطا در ذخیره سازی", "امکان ذخیره کلید API وجود ندارد (settings object missing).")
            else:
                QMessageBox.warning(self, "عملیات لغو شد", "کلید API برای ادامه کار ضروری است.")
                return

        item = items[self.current_item_index]
        article_url = item.get('link')

        if not article_url:
            QMessageBox.information(self, "لینک موجود نیست", "لینکی برای این خبر جهت دریافت متن کامل وجود ندارد.")
            return

        # Fetch and extract text from the URL
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        full_article_text, error_fetch = self._fetch_and_extract_article_text(article_url)
        QApplication.restoreOverrideCursor()

        if error_fetch:
            QMessageBox.warning(self, "خطا در دریافت محتوا", f"هنگام دریافت محتوای کامل از لینک خطایی رخ داد:\n{error_fetch}")
            return

        if not full_article_text:
            QMessageBox.information(self, "محتوا موجود نیست", "محتوایی برای خلاصه سازی یا ترجمه از لینک خبر یافت نشد.")
            return

        display_original_content = (full_article_text[:700] + '...') if len(full_article_text) > 700 else full_article_text

        summary_prompt = "Summarize the following text very concisely, focusing on the main points. The summary should be in the same language as the input text (which could be multilingual)."
        
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        llm_summary, error_summary = self._call_llm_api(full_article_text, summary_prompt)
        QApplication.restoreOverrideCursor()

        if error_summary:
            QMessageBox.warning(self, "خطا در خلاصه سازی", f"هنگام خلاصه سازی متن کامل خطایی رخ داد: {error_summary}")
            # llm_summary will be None, dialog will show error message for summary

        persian_translation_prompt = "Translate the following summary to Persian. If the summary is already in Persian, return it as is."
        llm_translation = None
        error_translation_msg = None

        if llm_summary: # Only translate if summarization was successful
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            llm_translation, error_translation_api = self._call_llm_api(llm_summary, persian_translation_prompt)
            QApplication.restoreOverrideCursor()
            if error_translation_api:
                error_translation_msg = f"هنگام ترجمه خلاصه به فارسی خطایی رخ داد: {error_translation_api}"
                QMessageBox.warning(self, "خطا در ترجمه", error_translation_msg)
        else: 
            error_translation_msg = "خلاصه سازی ناموفق بود، بنابراین ترجمه انجام نشد."

        llm_summary_display = llm_summary if llm_summary is not None else "خطا در دریافت خلاصه."
        llm_translation_display = llm_translation if llm_translation is not None else ("خطا در دریافت ترجمه." + (f" ({error_translation_msg.split(':')[-1].strip()})" if error_translation_msg else "") )
        
        dialog = SummarizeTranslateDialog(display_original_content, llm_summary_display, llm_translation_display, self)
        dialog.exec()

    # Placeholder for the actual API call logic
    def _call_llm_api(self, text_to_process, task_prompt):
        if not self.togetherai_api_token:
            # This should ideally be checked before calling
            print("Together.AI API token is missing.")
            return None, "کلید API برای Together.AI تنظیم نشده یا نامعتبر است."
        
        try:
            client = OpenAI(api_key=self.togetherai_api_token, base_url="https://api.together.xyz/v1")
            response = client.chat.completions.create(
                model="mistralai/Mistral-7B-Instruct-v0.2", # Or another cost-effective model from Together.AI # Or other suitable model
                messages=[
                    {"role": "system", "content": task_prompt},
                    {"role": "user", "content": text_to_process},
                ],
                stream=False
            )
            return response.choices[0].message.content, None
        except Exception as e:
            print(f"Error calling Together.AI API: {e}")
            return None, str(e)


class ManageRSSFeedsDialog(QDialog):
    def __init__(self, current_feeds, parent=None):
        # parent is expected to be CalendarWidget, which has self.settings
        # If parent is None or doesn't have settings, this will need adjustment
        # or settings should be passed directly.
        # For now, assuming parent is CalendarWidget as per _show_manage_rss_feeds_dialog
        self.settings = None
        if parent and hasattr(parent, 'settings'):
            self.settings = parent.settings
        else:
            # Fallback or error handling if settings are not available
            # This might happen if the dialog is instantiated differently elsewhere.
            # A more robust solution might be to pass settings explicitly.
            print("Warning: ManageRSSFeedsDialog initialized without access to QSettings.")
            # As a minimal fallback, create a temporary QSettings object for this scope
            # This won't persist globally but allows the dialog to function without erroring immediately.
            # The user should ensure settings are passed correctly for persistence.
            # self.settings = QSettings("YourOrg", "YourApp") # Placeholder if you need it to run standalone
            pass # Or raise an error, or disable API key field
        super().__init__(parent)
        self.setWindowTitle("مدیریت منبع‌های RSS")
        self.setMinimumWidth(500)
        # current_feeds is a list of dicts: [{'name': 'Feed Name', 'url': 'feed_url'}, ...]
        self.current_feeds_data = [dict(feed) for feed in current_feeds] # Deep copy

        layout = QVBoxLayout(self)

        # List widget to display feeds
        self.feeds_list_widget = QListWidget()
        self.feeds_list_widget.setToolTip("برای ویرایش، روی مورد دو بار کلیک کنید")
        for feed_data in self.current_feeds_data:
            item_text = f"{feed_data.get('name', 'بی نام')}: {feed_data.get('url', 'بدون آدرس')}"
            list_item = QListWidgetItem(item_text)
            list_item.setData(Qt.ItemDataRole.UserRole, feed_data) # Store original dict
            # item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable) # Editing complex item in place is harder
            self.feeds_list_widget.addItem(list_item)
        self.feeds_list_widget.itemDoubleClicked.connect(self._edit_selected_feed)
        layout.addWidget(self.feeds_list_widget)

        # DeepSeek API Token Input
        if self.settings: # Only add if settings are available
            api_token_layout = QHBoxLayout()
            api_token_label = QLabel("کلید API برای Together.AI:")
            self.api_token_input = QLineEdit()
            self.api_token_input.setPlaceholderText("اختیاری: کلید API خود را اینجا وارد کنید")
            self.api_token_input.setText(self.settings.value("togetherai/api_token", ""))
            api_token_layout.addWidget(api_token_label)
            api_token_layout.addWidget(self.api_token_input)
            layout.addLayout(api_token_layout)

        # Buttons for Add/Delete
        buttons_layout = QHBoxLayout()
        self.add_button = QPushButton("➕ افزودن منبع")
        self.delete_button = QPushButton("➖ حذف انتخاب شده")
        self.edit_button = QPushButton("📝 ویرایش انتخاب شده") # Added Edit button
        buttons_layout.addWidget(self.add_button)
        buttons_layout.addWidget(self.edit_button)
        buttons_layout.addWidget(self.delete_button)
        layout.addLayout(buttons_layout)

        # Dialog Ok/Cancel buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(self.button_box)

        self.add_button.clicked.connect(self._add_feed)
        self.delete_button.clicked.connect(self._delete_feed)
        self.edit_button.clicked.connect(self._edit_selected_feed)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.setLayout(layout)

    def _show_feed_details_dialog(self, feed_data=None):
        dialog = QDialog(self)
        dialog.setWindowTitle("جزئیات منبع RSS" if feed_data else "افزودن منبع RSS جدید")
        form_layout = QVBoxLayout(dialog)

        name_edit = QLineEdit(feed_data.get('name', '') if feed_data else '')
        name_edit.setPlaceholderText("نام منبع (مثال: اخبار BBC)")
        form_layout.addWidget(QLabel("نام منبع:"))
        form_layout.addWidget(name_edit)

        url_edit = QLineEdit(feed_data.get('url', '') if feed_data else '')
        url_edit.setPlaceholderText("آدرس URL منبع (مثال: http://feeds.bbci.co.uk/news/rss.xml)")
        url_edit.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        form_layout.addWidget(QLabel("آدرس URL:"))
        form_layout.addWidget(url_edit)

        direction_combo = QComboBox()
        direction_combo.addItem("راست‌چین (RTL)", "rtl")
        direction_combo.addItem("چپ‌چین (LTR)", "ltr")
        if feed_data and feed_data.get('direction') == 'ltr':
            direction_combo.setCurrentIndex(1)
        else: # Default to RTL
            direction_combo.setCurrentIndex(0)
        form_layout.addWidget(QLabel("جهت متن:"))
        form_layout.addWidget(direction_combo)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        form_layout.addWidget(button_box)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            name = name_edit.text().strip()
            url = url_edit.text().strip()
            direction = direction_combo.currentData()
            if not url: return None # URL is mandatory
            if not name: name = url # Default name to URL if empty
            return {'name': name, 'url': url, 'direction': direction}
        return None

    def _add_feed(self):
        new_feed_data = self._show_feed_details_dialog()
        if new_feed_data:
            # item_text = f"{new_feed_data['name']} ({new_feed_data['direction'].upper()}): {new_feed_data['url']}"
            # For now, keep item_text simpler, will refine display later if needed or in RSSReaderWidget itself.
            item_text = f"{new_feed_data['name']}: {new_feed_data['url']} ({new_feed_data['direction'].upper()})"
            list_item = QListWidgetItem(item_text)
            list_item.setData(Qt.ItemDataRole.UserRole, new_feed_data)
            self.feeds_list_widget.addItem(list_item)
            self.current_feeds_data.append(new_feed_data)

    def _delete_feed(self):
        selected_item = self.feeds_list_widget.currentItem()
        if selected_item:
            row = self.feeds_list_widget.row(selected_item)
            removed_data = self.feeds_list_widget.takeItem(row).data(Qt.ItemDataRole.UserRole)
            if removed_data in self.current_feeds_data:
                 self.current_feeds_data.remove(removed_data)
            del selected_item

    def _edit_selected_feed(self):
        selected_item = self.feeds_list_widget.currentItem()
        if not selected_item: return

        original_feed_data = selected_item.data(Qt.ItemDataRole.UserRole)
        if not original_feed_data: return

        updated_feed_data = self._show_feed_details_dialog(dict(original_feed_data)) # Pass a copy

        if updated_feed_data:
            # Update the item in self.current_feeds_data
            # This assumes original_feed_data is a reference to an item in the list
            # or that self.current_feeds_data is rebuilt by get_updated_feeds anyway.
            # For safety, let's update the original dict if it's still referenced.
            for i, feed in enumerate(self.current_feeds_data):
                if feed is original_feed_data: # Check for identity
                    self.current_feeds_data[i] = updated_feed_data
                    break
            else: # If not found by identity (e.g. if it was a copy), try to find by URL (less robust)
                for i, feed in enumerate(self.current_feeds_data):
                    if feed.get('url') == original_feed_data.get('url') and feed.get('name') == original_feed_data.get('name'):
                         self.current_feeds_data[i] = updated_feed_data
                         break
            
            # Update display text and data in QListWidgetItem
            # item_text = f"{updated_feed_data['name']} ({updated_feed_data['direction'].upper()}): {updated_feed_data['url']}"
            item_text = f"{updated_feed_data['name']}: {updated_feed_data['url']} ({updated_feed_data['direction'].upper()})"
            selected_item.setText(item_text)
            selected_item.setData(Qt.ItemDataRole.UserRole, updated_feed_data)

    def get_updated_feeds(self):
        # This should be called after dialog.exec() == QDialog.DialogCode.Accepted in the parent
        # Reconstruct from the list widget items as the source of truth upon OK
        updated_list = []
        for i in range(self.feeds_list_widget.count()):
            item = self.feeds_list_widget.item(i)
            updated_list.append(item.data(Qt.ItemDataRole.UserRole))
        self.current_feeds_data = updated_list # Ensure internal list is also updated
        return self.current_feeds_data

    def accept(self):
        # Called when OK or equivalent is clicked. Data should be finalized here or retrieved by caller.
        if self.settings and hasattr(self, 'api_token_input'): # Save API token if field exists and settings available
            self.settings.setValue("togetherai/api_token", self.api_token_input.text())
            # Update the token in the RSSReaderWidget instance if possible/needed immediately
            # This assumes the parent passed to this dialog is the CalendarWidget, which has rss_widget
            if self.parent() and hasattr(self.parent(), 'rss_widget') and self.parent().rss_widget:
                self.parent().rss_widget.togetherai_api_token = self.api_token_input.text()
                print("[ManageRSSFeedsDialog] Together.AI API Token updated in RSSReaderWidget.")

        # We will reconstruct the list from the widget items in get_updated_feeds, 
        # so no specific action needed here other than calling super.
        super().accept()

    def reject(self):
        # Called when Cancel or equivalent is clicked.
        super().reject()


class SummarizeTranslateDialog(QDialog):
    def __init__(self, original_text, summary_text, translated_text, parent=None):
        super().__init__(parent)
        self.setWindowTitle("خلاصه و ترجمه خبر")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        layout = QVBoxLayout(self)

        # Original Text
        original_label = QLabel("متن اصلی:")
        self.original_text_edit = QTextEdit()
        self.original_text_edit.setPlainText(original_text)
        self.original_text_edit.setReadOnly(True)
        self.original_text_edit.setFixedHeight(100) # Adjust as needed
        layout.addWidget(original_label)
        layout.addWidget(self.original_text_edit)

        # Summary Text
        summary_label = QLabel("خلاصه:")
        self.summary_text_edit = QTextEdit()
        self.summary_text_edit.setPlainText(summary_text or "خلاصه سازی انجام نشد یا خطایی رخ داد.")
        self.summary_text_edit.setReadOnly(True)
        layout.addWidget(summary_label)
        layout.addWidget(self.summary_text_edit)

        # Translated Text
        translated_label = QLabel("ترجمه (فارسی):")
        self.translated_text_edit = QTextEdit()
        self.translated_text_edit.setPlainText(translated_text or "ترجمه انجام نشد یا خطایی رخ داد.")
        self.translated_text_edit.setReadOnly(True)
        layout.addWidget(translated_label)
        layout.addWidget(self.translated_text_edit)

        # Dialog Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)

        self.setLayout(layout)
