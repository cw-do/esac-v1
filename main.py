import sys
import os
import warnings
import argparse

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
    def __init__(self, icl=False):
        super().__init__()
        self.icl = icl
        mode_name = "ICL Mode" if icl else "RAG Mode"
        self.setWindowTitle(f"ESAC v1 - EQ-SANS Assisting Chatbot ({mode_name})")
        self.setGeometry(100, 100, 1200, 800)

        # Initialize services
        self.config_manager = ConfigManager()
        self.llm_service = LLMService(self.config_manager)
        self.knowledge_manager = KnowledgeManager()
        self.script_executor = ScriptExecutor()

        # Load knowledge base
        self.knowledge_manager.load_or_build_index()

        # Print ICL context files if in ICL mode
        if self.icl:
            print("ICL Mode: Files included in context:")
            for filename in sorted(self.knowledge_manager.local_knowledge.keys()):
                print(f"  - {filename}")

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
        self.chat = ChatWidget(self.llm_service, self.knowledge_manager, self.config_manager, self.editor, self.icl)
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

        # Build Knowledge Base button
        self.build_kb_button = QPushButton("Build Knowledge Base")
        self.build_kb_button.clicked.connect(self.build_knowledge_base)
        button_layout.addWidget(self.build_kb_button)

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

        # Load initial knowledge
        extra_dirs = ["/home/controls/var/tmp"] if os.path.exists("/home/controls/var/tmp") else None
        self.knowledge_manager.load_or_build_index(extra_dirs)

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

    def build_knowledge_base(self):
        """Rebuild the knowledge base from all available directories"""
        import os  # Import os at the top
        extra_dirs = ["/home/controls/var/tmp"] if os.path.exists("/home/controls/var/tmp") else []
        directories = ["knowledge"] + extra_dirs
        print(f"Building knowledge base from: {directories}")
        
        # Force rebuild by removing existing index files
        for file in ["knowledge_index.faiss", "knowledge_docs.json", "knowledge_hash.txt"]:
            if os.path.exists(file):
                os.remove(file)
        
        # Rebuild the index
        self.knowledge_manager.load_or_build_index(extra_dirs)
        print("Knowledge base rebuilt successfully")

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
    parser = argparse.ArgumentParser(description="ESAC v1 - EQ-SANS Assisting Chatbot")
    parser.add_argument('--icl', action='store_true', help='Use In-Context Learning mode (default)')
    parser.add_argument('--rag', action='store_true', help='Use Retrieval-Augmented Generation mode')
    args = parser.parse_args()

    # Determine mode: ICL is default, RAG if --rag is specified
    if args.rag:
        icl_mode = False
    else:
        icl_mode = True  # Default to ICL

    app = QApplication(sys.argv)
    window = MainWindow(icl=icl_mode)
    window.show()
    sys.exit(app.exec_())