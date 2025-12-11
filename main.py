import sys
import os
import warnings
import tiktoken

# Suppress SIP deprecation warning
warnings.filterwarnings("ignore", message=".*sipPyTypeDict.*deprecated.*", category=DeprecationWarning)

from PyQt5.QtWidgets import QApplication, QMainWindow, QSplitter, QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QLabel, QComboBox, QLineEdit, QTextEdit, QListWidget, QProgressBar
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QSyntaxHighlighter, QTextCharFormat, QColor
import re

from gui.editor_widget import EditorWidget
from gui.chat_widget import ChatWidget
from gui.settings_dialog import SettingsDialog
from services.llm_service import LLMService
from services.knowledge_manager import KnowledgeManager
from services.script_executor import ScriptExecutor
from services.config_manager import ConfigManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        mode_name = "Hybrid Mode"
        self.setWindowTitle(f"ESAC v1 - EQ-SANS Assisting Chatbot ({mode_name})")
        self.setGeometry(100, 100, 1200, 800)

        # Initialize services
        self.config_manager = ConfigManager()
        self.llm_service = LLMService(self.config_manager)
        self.knowledge_manager = KnowledgeManager()
        self.script_executor = ScriptExecutor()

        # Load initial knowledge
        # extra_dirs = ["/home/controls/var/tmp"] if os.path.exists("/home/controls/var/tmp") else None
        extra_dirs = None # No extra dirs on initial load if needed
        self.knowledge_manager.load_or_build_index(extra_dirs)

        # Check for QRangeConfigurations and add to knowledge as RAG-only
        qrange_dir = os.environ.get("QRangeConfigurations_DIR", "/home/controls/var/QRangeConfigurations")
        if os.path.exists(qrange_dir) and os.path.isdir(qrange_dir):
            sav_files = sorted([f for f in os.listdir(qrange_dir) if f.lower().endswith('.sav')])
            if sav_files:
                config_names = [os.path.splitext(f)[0] for f in sav_files]
                content = "# Available QRange Configurations\n\nUse these when selecting or discussing instrument setups:\n\n" + "\n".join(f"- {name}" for name in config_names)
                self.knowledge_manager.local_knowledge["QRangeConfigurations.md"] = content
                self.knowledge_manager.rag_only.add("QRangeConfigurations.md")

        # Print knowledge files included in context
        print("Hybrid Mode: Files included in context:")
        for filename in sorted(self.knowledge_manager.local_knowledge.keys()):
            print(f"  - {filename}")
        
        # Calculate total tokens for ICL part
        context = self.knowledge_manager.get_full_context(max_length=200000)
        encoding = tiktoken.encoding_for_model("gpt-4")  # Use GPT-4 encoding as reference
        tokens = len(encoding.encode(context))
        print(f"Total tokens in ICL context: {tokens}")
        print(f"Within typical context limit (128k): {tokens < 128000}")

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create main vertical splitter for top/bottom
        main_splitter = QSplitter(Qt.Vertical)

        # Top part: horizontal splitter for editor and chat
        top_splitter = QSplitter(Qt.Horizontal)
        
        # Editor widget
        self.editor = EditorWidget()
        top_splitter.addWidget(self.editor)

        # Chat widget
        self.chat = ChatWidget(self.llm_service, self.knowledge_manager, self.config_manager, self.editor)
        self.chat.copy_to_editor_signal.connect(self.copy_to_editor)
        top_splitter.addWidget(self.chat)

        # Set splitter proportions
        top_splitter.setSizes([600, 600])
        
        main_splitter.addWidget(top_splitter)

        # Bottom part: buttons and controls
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout()

        # Action buttons
        button_layout = QHBoxLayout()

        # Run button
        self.run_button = QPushButton("Run")
        self.run_button.clicked.connect(self.run_script)
        button_layout.addWidget(self.run_button)

        # Simulate button
        self.simulate_button = QPushButton("Simulate")
        self.simulate_button.clicked.connect(self.simulate_script)
        button_layout.addWidget(self.simulate_button)

        # NOTE: Build Knowledge Base button removed - knowledge is loaded from `knowledge/` only

        # Settings button
        self.settings_button = QPushButton("Settings")
        self.settings_button.clicked.connect(self.show_settings)
        button_layout.addWidget(self.settings_button)

        # Add stretch to push PC controls to the right
        button_layout.addStretch()

        # Proton charge input section
        pc_layout = QHBoxLayout()
        pc_layout.addWidget(QLabel("PC per hour:"))
        self.pc_input = QLineEdit("5.2")
        self.pc_input.setFixedWidth(50)
        pc_layout.addWidget(self.pc_input)
        pc_layout.addWidget(QLabel("  "))  # Small spacer
        button_layout.addLayout(pc_layout)

        # Estimate time button
        self.estimate_button = QPushButton("Estimate Time")
        self.estimate_button.clicked.connect(self.estimate_time)
        button_layout.addWidget(self.estimate_button)

        # Estimated time label
        self.time_label = QLabel("Est. time: --")
        button_layout.addWidget(self.time_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        button_layout.addWidget(self.progress_bar)

        bottom_layout.addLayout(button_layout)
        bottom_widget.setLayout(bottom_layout)
        
        main_splitter.addWidget(bottom_widget)

        # Set main splitter proportions (more space for top)
        main_splitter.setSizes([800, 200])

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(main_splitter)
        central_widget.setLayout(main_layout)


    def run_script(self):
        script_content = self.editor.get_text()
        if script_content.strip():
            self.script_executor.run_script(script_content)

    def simulate_script(self):
        script_content = self.editor.get_text()
        if script_content.strip():
            # Basic syntax check
            try:
                compile(script_content, '<string>', 'exec')
                self.time_label.setText("Syntax OK")
            except SyntaxError as e:
                self.time_label.setText(f"Syntax Error: {e}")

    # NOTE: build_knowledge_base function removed - knowledge is loaded on startup and can be
    # reloaded from the `knowledge/` directory via the application logic (if needed)

    def copy_to_editor(self, data):
        if isinstance(data, tuple):
            type_, content = data
            if type_ == 'text':
                current_text = self.editor.get_text()
                if current_text:
                    # Append to existing text
                    self.editor.set_text(current_text + "\n\n" + content)
                else:
                    self.editor.set_text(content)
            elif type_ == 'file':
                if self.editor.get_text():
                    self.editor.new_tab()
                self.editor.load_file(content)
        else:
            # Backward compatibility
            current_text = self.editor.get_text()
            if current_text:
                self.editor.set_text(current_text + "\n\n" + data)
            else:
                self.editor.set_text(data)

    def show_settings(self):
        dialog = SettingsDialog(self.config_manager, self.llm_service)
        dialog.exec_()
        self.chat.update_model_list()

    def estimate_time(self):
        script_content = self.editor.get_text()
        if script_content.strip():
            try:
                pc_per_hour = float(self.pc_input.text())
                estimated_time = self.script_executor.estimate_time(script_content, pc_per_hour)
                self.time_label.setText(f"Est. time: {estimated_time}")
            except ValueError:
                self.time_label.setText("Est. time: Invalid PC value")
        else:
            self.time_label.setText("Est. time: No script")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())