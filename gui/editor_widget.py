from PyQt5.QtWidgets import QVBoxLayout, QWidget, QPlainTextEdit, QTextEdit, QTabWidget, QHBoxLayout, QPushButton, QFileDialog, QMessageBox
from PyQt5.QtGui import QFont, QColor, QSyntaxHighlighter, QTextCharFormat, QPainter, QFontMetrics, QTextBlock, QTextFormat, QIcon
from PyQt5.QtCore import Qt, QRect, QSize
import re
import os

class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor(0, 0, 255))
        keyword_format.setFontWeight(QFont.Bold)
        keywords = [
            "and", "as", "assert", "break", "class", "continue", "def", "del", "elif", "else",
            "except", "False", "finally", "for", "from", "global", "if", "import", "in", "is",
            "lambda", "None", "nonlocal", "not", "or", "pass", "raise", "return", "True", "try",
            "while", "with", "yield"
        ]
        self.highlighting_rules = [(re.compile(r'\b' + keyword + r'\b'), keyword_format) for keyword in keywords]

        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor(255, 0, 0))
        self.highlighting_rules.append((re.compile(r'".*"'), string_format))
        self.highlighting_rules.append((re.compile(r"'.*'"), string_format))

        # Comments
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor(0, 128, 0))
        self.highlighting_rules.append((re.compile(r'#.*'), comment_format))

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            for match in pattern.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), format)

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor.line_number_area_paint_event(event)

class CodeEditor(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        self.line_number_area = LineNumberArea(self)
        
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        
        self.update_line_number_area_width(0)
        self.highlight_current_line()
        
        # Create syntax highlighter
        self.highlighter = PythonHighlighter(self.document())
        
        # Store file path for this editor
        self.file_path = None

    def line_number_area_width(self):
        digits = 1
        max_block = max(1, self.blockCount())
        while max_block >= 10:
            max_block /= 10
            digits += 1
        
        space = 3 + self.fontMetrics().width('9') * digits
        return space

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), Qt.lightGray)
        
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()
        
        height = self.fontMetrics().height()
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(Qt.black)
                painter.drawText(0, top, self.line_number_area.width(), height, Qt.AlignRight, number)
            
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1

    def highlight_current_line(self):
        extra_selections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor(Qt.yellow).lighter(160)
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        self.setExtraSelections(extra_selections)

class EditorWidget(QWidget):
    def __init__(self, base_mono_font_size=None, config_manager=None):
        super().__init__()
        layout = QVBoxLayout()
        # Store base monospace font size for new editor tabs
        self.base_mono_font_size = base_mono_font_size
        # Config manager for persisting last used directory
        self.config_manager = config_manager

        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        
        # Create button layout
        button_layout = QHBoxLayout()
        
        self.new_tab_button = QPushButton("New Tab")
        self.new_tab_button.clicked.connect(lambda: self.new_tab())
        
        self.open_button = QPushButton("Open")
        self.open_button.clicked.connect(self.open_file)
        
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_file)
        
        self.save_as_button = QPushButton("Save As")
        self.save_as_button.clicked.connect(self.save_file_as)
        
        button_layout.addWidget(self.new_tab_button)
        button_layout.addWidget(self.open_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.save_as_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        layout.addWidget(self.tab_widget)
        
        self.setLayout(layout)
        
        # Track file paths for each tab (no longer needed - using CodeEditor.file_path)
        # self.tab_files = {}
        
        # Create initial tab
        self.new_tab("Untitled-1")
        
        # Connect tab change signal
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        # Add keyboard shortcuts
        from PyQt5.QtWidgets import QShortcut
        from PyQt5.QtGui import QKeySequence
        
        # Ctrl+N for new tab
        QShortcut(QKeySequence("Ctrl+N"), self).activated.connect(lambda: self.new_tab())
        
        # Ctrl+O for open
        QShortcut(QKeySequence("Ctrl+O"), self).activated.connect(self.open_file)
        
        # Ctrl+S for save
        QShortcut(QKeySequence("Ctrl+S"), self).activated.connect(self.save_file)
        
        # Ctrl+Shift+S for save as
        QShortcut(QKeySequence("Ctrl+Shift+S"), self).activated.connect(self.save_file_as)

    def on_tab_changed(self, index):
        """Called when the current tab changes"""
        if index >= 0:
            # Could emit a signal here if needed for other components
            pass

    def new_tab(self, title=None, content=""):
        # Generate unique title if not provided
        if title is None:
            existing_titles = [self.tab_widget.tabText(i) for i in range(self.tab_widget.count())]
            counter = 1
            while f"Untitled-{counter}" in existing_titles:
                counter += 1
            title = f"Untitled-{counter}"
        
        # Create new editor widget
        editor = CodeEditor()
        # Use provided base monospace font size if passed, otherwise default to 10
        try:
            size = int(self.base_mono_font_size) if self.base_mono_font_size is not None else 10
        except Exception:
            size = 10
        editor.setFont(QFont("Courier New", size))
        
        # Add tab
        tab_index = self.tab_widget.addTab(editor, title)
        self.tab_widget.setCurrentIndex(tab_index)
        
        # Set initial content
        if content:
            editor.setPlainText(content)
        
        # File path is already None in CodeEditor.__init__

    def close_tab(self, index):
        if self.tab_widget.count() > 1:
            # Remove tab
            self.tab_widget.removeTab(index)
        else:
            QMessageBox.warning(self, "Warning", "Cannot close the last tab.")

    def open_file(self):
        # Determine initial directory: current file dir, configured last_dir, or default tmp folder
        start_dir = ""
        current_path = self.get_current_file_path()
        if current_path:
            start_dir = os.path.dirname(current_path)
        elif self.config_manager and self.config_manager.get('last_dir'):
            start_dir = self.config_manager.get('last_dir')
        else:
            start_dir = "/home/controls/var/tmp"

        filename, _ = QFileDialog.getOpenFileName(self, "Open File", start_dir, "Python Files (*.py);;Text Files (*.txt);;All Files (*)")
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Get filename for tab title
                basename = os.path.basename(filename)
                
                # Create new tab or replace current tab content
                current_index = self.tab_widget.currentIndex()
                current_editor = self.tab_widget.widget(current_index)
                if (current_index >= 0 and 
                    isinstance(current_editor, CodeEditor) and
                    current_editor.file_path is None and 
                    self.get_text().strip() == ""):
                    # Replace empty untitled tab
                    self.set_text(content)
                    self.tab_widget.setTabText(current_index, basename)
                    current_editor.file_path = filename
                else:
                    # Create new tab
                    self.new_tab(basename, content)
                    # Set file path for the new tab
                    new_index = self.tab_widget.currentIndex()
                    new_editor = self.tab_widget.widget(new_index)
                    if isinstance(new_editor, CodeEditor):
                        new_editor.file_path = filename
                # Persist last directory
                try:
                    if self.config_manager:
                        self.config_manager.set('last_dir', os.path.dirname(filename))
                except Exception:
                    pass
                    
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open file: {str(e)}")

    def load_file(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            basename = os.path.basename(filepath)
            
            current_index = self.tab_widget.currentIndex()
            current_editor = self.tab_widget.widget(current_index)
            if (current_index >= 0 and 
                isinstance(current_editor, CodeEditor) and
                current_editor.file_path is None and 
                self.get_text().strip() == ""):
                # Replace empty untitled tab
                self.set_text(content)
                self.tab_widget.setTabText(current_index, basename)
                current_editor.file_path = filepath
            else:
                # Create new tab
                self.new_tab(basename, content)
                new_index = self.tab_widget.currentIndex()
                new_editor = self.tab_widget.widget(new_index)
                if isinstance(new_editor, CodeEditor):
                    new_editor.file_path = filepath
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load file: {str(e)}")

    def save_file(self):
        current_index = self.tab_widget.currentIndex()
        if current_index < 0:
            return
            
        current_editor = self.tab_widget.widget(current_index)
        if not isinstance(current_editor, CodeEditor):
            return
            
        filename = current_editor.file_path
        if filename:
            # Save to existing file
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.get_text())
                QMessageBox.information(self, "Success", "File saved successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save file: {str(e)}")
        else:
            # Save as new file
            self.save_file_as()

    def save_file_as(self):
        current_index = self.tab_widget.currentIndex()
        if current_index < 0:
            return
            
        current_editor = self.tab_widget.widget(current_index)
        if not isinstance(current_editor, CodeEditor):
            return
            
        # Determine initial directory for save dialog
        start_dir = ""
        current_path = self.get_current_file_path()
        if current_path:
            start_dir = os.path.dirname(current_path)
        elif self.config_manager and self.config_manager.get('last_dir'):
            start_dir = self.config_manager.get('last_dir')
        else:
            start_dir = "/home/controls/var/tmp"

        filename, _ = QFileDialog.getSaveFileName(self, "Save File", start_dir, "Python Files (*.py);;Text Files (*.txt);;All Files (*)")
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.get_text())
                
                # Update tab title and file tracking
                basename = os.path.basename(filename)
                self.tab_widget.setTabText(current_index, basename)
                current_editor.file_path = filename
                # Persist last directory
                try:
                    if self.config_manager:
                        self.config_manager.set('last_dir', os.path.dirname(filename))
                except Exception:
                    pass
                QMessageBox.information(self, "Success", "File saved successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save file: {str(e)}")

    def get_text(self):
        """Get text from current tab"""
        current_index = self.tab_widget.currentIndex()
        if current_index >= 0:
            current_widget = self.tab_widget.widget(current_index)
            if isinstance(current_widget, CodeEditor):
                return current_widget.toPlainText()
        return ""

    def set_text(self, text):
        """Set text in current tab"""
        current_index = self.tab_widget.currentIndex()
        if current_index >= 0:
            current_widget = self.tab_widget.widget(current_index)
            if isinstance(current_widget, CodeEditor):
                current_widget.setPlainText(text)

    def get_current_tab_title(self):
        """Get the title of the current tab"""
        current_index = self.tab_widget.currentIndex()
        if current_index >= 0:
            return self.tab_widget.tabText(current_index)
        return "Untitled"

    def get_current_file_path(self):
        """Get the file path of the current tab"""
        current_index = self.tab_widget.currentIndex()
        if current_index >= 0:
            current_widget = self.tab_widget.widget(current_index)
            if isinstance(current_widget, CodeEditor):
                return current_widget.file_path
        return None

    def get_all_tabs_info(self):
        """Get information about all tabs"""
        tabs_info = []
        for i in range(self.tab_widget.count()):
            title = self.tab_widget.tabText(i)
            widget = self.tab_widget.widget(i)
            file_path = None
            if isinstance(widget, CodeEditor):
                file_path = widget.file_path
            tabs_info.append({
                'index': i,
                'title': title,
                'file_path': file_path,
                'is_current': i == self.tab_widget.currentIndex()
            })
        return tabs_info