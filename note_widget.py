import sys
import sys
from PyQt6.QtWidgets import (QApplication, QWidget, QTextEdit, QVBoxLayout, 
                              QPushButton, QTabWidget, QLineEdit, QToolBar, 
                              QSizePolicy, QFrame, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QSize, QPoint, pyqtSignal
from PyQt6.QtGui import (QIcon, QAction, QTextCharFormat, QFont, 
                         QTextListFormat, QTextCursor, QMouseEvent, QColor)

class ChecklistTextEdit(QTextEdit):
    UNCHECKED = "☐"
    CHECKED = "☑"

    def __init__(self, parent=None):
        super().__init__(parent)

    def keyPressEvent(self, e):
        cursor = self.textCursor()
        # Handle Enter key for to-do lists
        if e.key() in [Qt.Key.Key_Return, Qt.Key.Key_Enter] and \
           cursor.block().text().lstrip().startswith((self.UNCHECKED, self.CHECKED)):
            
            # If the current to-do item is empty, remove it and create a normal new line
            if cursor.block().text().strip() in [self.UNCHECKED, self.CHECKED]:
                cursor.beginEditBlock()
                cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
                cursor.removeSelectedText()
                cursor.insertBlock()
                cursor.endEditBlock()
            else:
                # Otherwise, create a new to-do item on the next line
                cursor.insertBlock()
                cursor.insertText(self.UNCHECKED + " ")
            e.accept()
        else:
            super().keyPressEvent(e)

    def mousePressEvent(self, e):
        cursor = self.cursorForPosition(e.pos())
        # Check if the click was on the checkbox character
        if e.button() == Qt.MouseButton.LeftButton and cursor.positionInBlock() == 0:
            self.toggle_checklist_state(cursor)
            e.accept()
        else:
            super().mousePressEvent(e)

    def toggle_checklist_state(self, cursor):
        block = cursor.block()
        if not block.isValid() or not block.text():
            return

        mod_cursor = QTextCursor(block)
        mod_cursor.beginEditBlock()

        text_char_fmt = QTextCharFormat()
        text = block.text()

        if text.startswith(self.CHECKED):
            mod_cursor.movePosition(QTextCursor.MoveOperation.NextCharacter, QTextCursor.MoveMode.KeepAnchor, 1)
            mod_cursor.removeSelectedText()
            mod_cursor.insertText(self.UNCHECKED)
            text_char_fmt.setFontStrikeOut(False)
        elif text.startswith(self.UNCHECKED):
            mod_cursor.movePosition(QTextCursor.MoveOperation.NextCharacter, QTextCursor.MoveMode.KeepAnchor, 1)
            mod_cursor.removeSelectedText()
            mod_cursor.insertText(self.CHECKED)
            text_char_fmt.setFontStrikeOut(True)
        else:
            mod_cursor.endEditBlock()
            return

        mod_cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)
        mod_cursor.mergeCharFormat(text_char_fmt)
        mod_cursor.endEditBlock()


class TabbedNoteManager(QWidget):
    closed = pyqtSignal() # Signal emitted when the widget is closed by its own button

    def __init__(self, theme_scheme, boxed_style, parent=None):
        super().__init__(parent)

        self.setWindowTitle("یادداشت ها")
        self.setWindowIcon(QIcon(":/icons/notes.png"))
        self.setMinimumSize(400, 300)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.old_pos = None

        # Main container for styling and shadow
        self.background_frame = QFrame(self)
        self.background_frame.setObjectName("background_frame")
        
        # Create shadow effect
        self.shadow_effect = self.shadow()
        self.setGraphicsEffect(self.shadow_effect)

        # The main layout is now inside the background frame
        self.frame_layout = QVBoxLayout(self.background_frame)

        # Set the main widget's layout to just contain the frame
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10) # To make shadow visible
        main_layout.addWidget(self.background_frame)

        # Formatting Toolbar
        self.toolbar = QToolBar("Formatting")
        self.toolbar.setIconSize(QSize(20, 20))
        self.frame_layout.addWidget(self.toolbar)

        # Tab widget to hold notes
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.tabBarDoubleClicked.connect(self.edit_tab_title)
        self.tab_widget.currentChanged.connect(self.update_toolbar_state)

        # Add new note button
        self.add_note_button = QPushButton("ایجاد یادداشت جدید")
        self.add_note_button.clicked.connect(self.add_new_tab)

        # Add widgets to layout
        self.frame_layout.addWidget(self.tab_widget)
        self.frame_layout.addWidget(self.add_note_button)

        self.apply_theme(theme_scheme, boxed_style)

        self.setup_toolbar()

        # Keep track of note count for default naming
        self.note_counter = 0

        # Add the first tab
        self.add_new_tab()

    def add_new_tab(self, title="", content=""):
        self.note_counter += 1
        
        # Use provided title or create a default one
        tab_title = title if title else f"یادداشت {self.note_counter}"

        # Create the text editor for the new tab
        text_edit = ChecklistTextEdit()
        text_edit.setHtml(content) # Use setHtml to support rich text later
        text_edit.currentCharFormatChanged.connect(self.update_toolbar_state)

        # Add the new tab
        new_tab_index = self.tab_widget.addTab(text_edit, tab_title)
        
        # Switch to the new tab
        self.tab_widget.setCurrentIndex(new_tab_index)

    def close_tab(self, index):
        # If it's the last tab, don't close it, just clear it.
        # This ensures there's always at least one tab open.
        if self.tab_widget.count() == 1:
            self.tab_widget.widget(index).clear()
            self.tab_widget.setTabText(index, "یادداشت 1")
            self.note_counter = 1
        else:
            widget = self.tab_widget.widget(index)
            if widget is not None:
                widget.deleteLater()
            self.tab_widget.removeTab(index)

    def setup_toolbar(self):
        # Bold Action
        self.action_bold = QAction(QIcon.fromTheme("format-text-bold"), "Bold", self)
        self.action_bold.setCheckable(True)
        self.action_bold.triggered.connect(self.toggle_bold)
        self.toolbar.addAction(self.action_bold)

        # Italic Action
        self.action_italic = QAction(QIcon.fromTheme("format-text-italic"), "Italic", self)
        self.action_italic.setCheckable(True)
        self.action_italic.triggered.connect(self.toggle_italic)
        self.toolbar.addAction(self.action_italic)

        # Underline Action
        self.action_underline = QAction(QIcon.fromTheme("format-text-underline"), "Underline", self)
        self.action_underline.setCheckable(True)
        self.action_underline.triggered.connect(self.toggle_underline)
        self.toolbar.addAction(self.action_underline)

        self.toolbar.addSeparator()

        # List Actions
        self.action_bullet_list = QAction(QIcon.fromTheme("format-justify-fill"), "Bulleted List", self)
        self.action_bullet_list.setCheckable(True)
        self.action_bullet_list.triggered.connect(self.format_bullet_list)
        self.toolbar.addAction(self.action_bullet_list)

        self.action_number_list = QAction(QIcon.fromTheme("format-justify-center"), "Numbered List", self) # Using a placeholder icon
        self.action_number_list.setCheckable(True)
        self.action_number_list.triggered.connect(self.format_number_list)
        self.toolbar.addAction(self.action_number_list)

        self.toolbar.addSeparator()

        # To-Do List Action
        self.action_todo_list = QAction(QIcon.fromTheme("checkbox"), "To-Do List", self)
        self.action_todo_list.setCheckable(True)
        self.action_todo_list.triggered.connect(self.format_todo_list)
        self.toolbar.addAction(self.action_todo_list)

        # Add a spacer to push the close button to the right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.toolbar.addWidget(spacer)

        # Close button for the frameless window
        action_close = QAction(QIcon.fromTheme("window-close"), "Close", self)
        action_close.triggered.connect(self.close)
        self.toolbar.addAction(action_close)

    def get_current_editor(self):
        return self.tab_widget.currentWidget()

    def toggle_bold(self):
        editor = self.get_current_editor()
        if not editor: return
        fmt = QTextCharFormat()
        fmt.setFontWeight(QFont.Weight.Bold if self.action_bold.isChecked() else QFont.Weight.Normal)
        editor.mergeCurrentCharFormat(fmt)

    def toggle_italic(self):
        editor = self.get_current_editor()
        if not editor: return
        fmt = QTextCharFormat()
        fmt.setFontItalic(self.action_italic.isChecked())
        editor.mergeCurrentCharFormat(fmt)

    def toggle_underline(self):
        editor = self.get_current_editor()
        if not editor: return
        fmt = QTextCharFormat()
        fmt.setFontUnderline(self.action_underline.isChecked())
        editor.mergeCurrentCharFormat(fmt)

    def format_bullet_list(self):
        editor = self.get_current_editor()
        if not editor: return
        cursor = editor.textCursor()
        list_format = QTextListFormat()
        if self.action_bullet_list.isChecked():
            list_format.setStyle(QTextListFormat.Style.ListDisc)
            self.action_number_list.setChecked(False) # Uncheck the other list type
        cursor.createList(list_format)

    def format_number_list(self):
        editor = self.get_current_editor()
        if not editor: return
        cursor = editor.textCursor()
        list_format = QTextListFormat()
        if self.action_number_list.isChecked():
            list_format.setStyle(QTextListFormat.Style.ListDecimal)
            self.action_bullet_list.setChecked(False) # Uncheck the other list type
        cursor.createList(list_format)

    def format_todo_list(self):
        editor = self.get_current_editor()
        if not editor or not isinstance(editor, ChecklistTextEdit): return

        cursor = editor.textCursor()
        block = cursor.block()
        text = block.text()

        cursor.beginEditBlock()

        # If it's a list, turn it off first
        if cursor.currentList():
            cursor.createList(QTextListFormat()) # Pass empty format to remove list
            self.action_bullet_list.setChecked(False)
            self.action_number_list.setChecked(False)

        if self.action_todo_list.isChecked():
            if not text.startswith(ChecklistTextEdit.UNCHECKED) and not text.startswith(ChecklistTextEdit.CHECKED):
                cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
                cursor.insertText(ChecklistTextEdit.UNCHECKED + " ")
        else:
            if text.startswith(ChecklistTextEdit.UNCHECKED) or text.startswith(ChecklistTextEdit.CHECKED):
                cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
                cursor.movePosition(QTextCursor.MoveOperation.NextCharacter, QTextCursor.MoveMode.KeepAnchor, 2)
                cursor.removeSelectedText()
                
                char_fmt = QTextCharFormat()
                char_fmt.setFontStrikeOut(False)
                cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
                cursor.mergeCharFormat(char_fmt)
                cursor.clearSelection()

        cursor.endEditBlock()

    def update_toolbar_state(self):
        editor = self.get_current_editor()
        if not editor: return
        # Update bold, italic, underline buttons
        fmt = editor.currentCharFormat()
        self.action_bold.setChecked(fmt.fontWeight() == QFont.Weight.Bold)
        self.action_italic.setChecked(fmt.fontItalic())
        self.action_underline.setChecked(fmt.fontUnderline())

        # Update list buttons
        cursor = editor.textCursor()
        current_list = cursor.currentList()
        if current_list:
            style = current_list.format().style()
            self.action_bullet_list.setChecked(style == QTextListFormat.Style.ListDisc)
            self.action_number_list.setChecked(style in [QTextListFormat.Style.ListDecimal, QTextListFormat.Style.ListLowerAlpha, QTextListFormat.Style.ListUpperAlpha])
            self.action_todo_list.setChecked(False) # Can't be a list and a todo
        else:
            self.action_bullet_list.setChecked(False)
            self.action_number_list.setChecked(False)
            # Update To-Do button state
            text = cursor.block().text()
            is_todo = text.startswith(ChecklistTextEdit.UNCHECKED) or text.startswith(ChecklistTextEdit.CHECKED)
            self.action_todo_list.setChecked(is_todo)

    def edit_tab_title(self, index):
        # Do nothing if the index is invalid
        if index == -1:
            return

        # Create a QLineEdit for editing the tab title
        line_edit = QLineEdit(self.tab_widget.tabText(index))
        line_edit.setParent(self.tab_widget.tabBar())
        
        # Finish editing when Enter is pressed or focus is lost
        line_edit.editingFinished.connect(lambda: self.finish_editing_title(index, line_edit))
        
        # Position the QLineEdit over the tab
        tab_rect = self.tab_widget.tabBar().tabRect(index)
        line_edit.setGeometry(tab_rect)
        line_edit.show()
        line_edit.selectAll()
        line_edit.setFocus()

    def finish_editing_title(self, index, line_edit):
        new_title = line_edit.text().strip()
        if new_title:
            self.tab_widget.setTabText(index, new_title)
        line_edit.deleteLater()

    def apply_theme(self, scheme, boxed_style):
        # Note manager should always look 'boxed' as it's a floating panel.
        bg_color = scheme['box_bg'].name(QColor.NameFormat.HexArgb)
        border_color = scheme['box_border'].name(QColor.NameFormat.HexArgb)
        text_color = scheme['box_text'].name(QColor.NameFormat.HexArgb)
        hover_color = scheme['box_bg_hover'].name(QColor.NameFormat.HexArgb)
        
        # Store the theme colors for later use
        self.current_theme = {
            'bg_color': bg_color,
            'border_color': border_color,
            'text_color': text_color,
            'hover_color': hover_color
        }
        
        # Make sure the background frame is visible
        self.background_frame.setVisible(True)
        
        # Apply theme to all editors in tabs
        for i in range(self.tab_widget.count()):
            editor = self.tab_widget.widget(i)
            if isinstance(editor, QTextEdit):
                editor.setStyleSheet(f"background-color: {bg_color}; color: {text_color};")
        
        style = f"""
        #background_frame {{
            background-color: {bg_color};
            border: 1px solid {border_color};
            border-radius: 8px;
        }}
        
        /* Text edit and tab pane styling */
        QTextEdit, QTabWidget::pane {{
            background-color: {bg_color};
            color: {text_color};
            border: none;
        }}
        
        /* Tab bar styling */
        QTabBar::tab {{
            background-color: {bg_color};
            color: {text_color};
            border: 1px solid {border_color};
            border-bottom: none;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            padding: 5px 10px;
            margin-right: 2px;
        }}
        
        QTabBar::tab:selected {{
            background-color: {hover_color};
            border-bottom: none;
        }}
        
        QTabBar::tab:hover:!selected {{
            background-color: {hover_color};
        }}
        
        /* Toolbar styling */
        QToolBar {{
            background-color: transparent;
            border: none;
        }}
        
        QToolBar QToolButton {{
            background-color: transparent;
            border: none;
            color: {text_color};
            padding: 3px;
            border-radius: 3px;
        }}
        
        QToolBar QToolButton:hover {{
            background-color: {hover_color};
        }}
        
        QToolBar QToolButton:checked {{
            background-color: {hover_color};
            border: 1px solid {border_color};
        }}
        
        /* Button styling */
        QPushButton {{
            color: {text_color};
            background-color: transparent;
            border: 1px solid {border_color};
            padding: 4px 8px;
            border-radius: 4px;
        }}
        
        QPushButton:hover {{
            background-color: {hover_color};
        }}
        """
        
        # Apply the stylesheet
        self.setStyleSheet(style)
        
        # Ensure the widget is visible and properly rendered
        self.update()
        
        # Recreate shadow effect to ensure it's properly applied
        if hasattr(self, 'shadow_effect'):
            self.shadow_effect.deleteLater()
        self.shadow_effect = self.shadow()
        self.setGraphicsEffect(self.shadow_effect)

    def shadow(self): # Utility for shadow effect
        s = QGraphicsDropShadowEffect()
        s.setColor(QColor(0,0,0,100))
        s.setBlurRadius(10)
        s.setOffset(0,0)
        return s

    def closeEvent(self, event):
        self.closed.emit()
        super().closeEvent(event)

    # --- Window Dragging Methods ---
    def mousePressEvent(self, e: QMouseEvent):
        if e.button() == Qt.MouseButton.LeftButton:
            self.old_pos = e.globalPosition().toPoint()
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e: QMouseEvent):
        if e.buttons() == Qt.MouseButton.LeftButton and self.old_pos is not None and self.toolbar.underMouse():
            delta = QPoint(e.globalPosition().toPoint() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = e.globalPosition().toPoint()
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e: QMouseEvent):
        if e.button() == Qt.MouseButton.LeftButton:
            self.old_pos = None
        super().mouseReleaseEvent(e)


# For testing the widget independently
if __name__ == '__main__':
    app = QApplication(sys.argv)
    note_manager = TabbedNoteManager()
    note_manager.show()
    sys.exit(app.exec_())
