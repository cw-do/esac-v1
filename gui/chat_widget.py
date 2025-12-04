from PyQt5.QtWidgets import QWidget, QVBoxLayout, QListWidget, QLineEdit, QPushButton, QHBoxLayout, QListWidgetItem, QComboBox, QTextEdit, QLabel
from PyQt5.QtCore import QThread, pyqtSignal, Qt
import re
from services.llm_service import LLMService
from services.knowledge_manager import KnowledgeManager

class ChatWorker(QThread):
    response_chunk = pyqtSignal(str)
    finished = pyqtSignal()
    usage_info = pyqtSignal(dict)

    def __init__(self, llm_service, knowledge_manager, message, context, conversation_history=None, icl=False):
        super().__init__()
        self.llm_service = llm_service
        self.knowledge_manager = knowledge_manager
        self.message = message
        self.context = context
        self.conversation_history = conversation_history
        self.icl = icl
        self.full_response = ""
        self.usage = None

    def run(self):
        try:
            def chunk_callback(chunk):
                self.full_response += chunk
                self.response_chunk.emit(chunk)
            
            result = self.llm_service.generate_response_stream(self.message, self.context, chunk_callback, self.conversation_history, self.icl)
            if isinstance(result, tuple):
                self.full_response, self.usage = result
            else:
                self.full_response = result
                self.usage = None
        except Exception as e:
            self.response_chunk.emit(f"Error: {str(e)}")
        finally:
            if self.usage:
                self.usage_info.emit(self.usage)
            self.finished.emit()

class ChatWidget(QWidget):
    copy_to_editor_signal = pyqtSignal(str)

    def __init__(self, llm_service, knowledge_manager, config_manager, editor_widget=None, icl=False):
        super().__init__()
        self.llm_service = llm_service
        self.knowledge_manager = knowledge_manager
        self.config_manager = config_manager
        self.editor_widget = editor_widget
        self.icl = icl
        self.last_speaker = None  # Track who spoke last for adding blank lines
        
        # Token tracking
        self.total_tokens = 0
        self.total_cost = 0.0
        
        # Pricing per model (approximate USD per 1M tokens)
        self.pricing = {
            'openai/gpt-4o-mini': {'input': 0.15, 'output': 0.60},
            'openai/gpt-4o': {'input': 2.50, 'output': 10.00},
            'openai/gpt-3.5-turbo': {'input': 0.50, 'output': 1.50},
            'anthropic/claude-3-haiku': {'input': 0.25, 'output': 1.25},
            'anthropic/claude-3-sonnet': {'input': 3.00, 'output': 15.00},
            'meta-llama/llama-3.1-8b-instruct': {'input': 0.10, 'output': 0.20},
            'meta-llama/llama-3.1-70b-instruct': {'input': 0.50, 'output': 1.00},
        }

        layout = QVBoxLayout()

        # Chat history
        self.chat_list = QListWidget()
        self.chat_list.setSelectionMode(QListWidget.MultiSelection)  # Allow selection
        self.chat_list.setVerticalScrollMode(QListWidget.ScrollPerPixel)  # Smooth scrolling
        self.chat_list.setWordWrap(True)  # Enable word wrapping
        self.chat_list.setTextElideMode(Qt.ElideNone)  # Don't elide text
        # Enable rich text display
        self.chat_list.setStyleSheet("QListWidget::item { padding: 2px; }")
        layout.addWidget(self.chat_list)

        # Input layout (vertical)
        input_layout = QVBoxLayout()
        
        # Text input field (multi-line)
        self.input_field = QTextEdit()
        self.input_field.setMaximumHeight(80)  # Allow up to ~3 lines
        self.input_field.setPlaceholderText("Type your message here...")
        input_layout.addWidget(self.input_field)

        # Button layout
        button_layout = QHBoxLayout()
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        button_layout.addWidget(self.send_button)

        self.copy_button = QPushButton("Copy Last Code to Editor")
        self.copy_button.clicked.connect(self.copy_to_editor)
        button_layout.addWidget(self.copy_button)

        self.new_chat_button = QPushButton("New Chat")
        self.new_chat_button.clicked.connect(self.new_chat)
        button_layout.addWidget(self.new_chat_button)

        input_layout.addLayout(button_layout)

        layout.addLayout(input_layout)

        # Model selection and token display
        model_layout = QHBoxLayout()
        
        self.model_combo = QComboBox()
        self.update_model_list()
        self.model_combo.currentTextChanged.connect(self.change_model)
        model_layout.addWidget(self.model_combo)
        
        # Token display label
        self.token_label = QLabel("Tokens: 0 ($0.00)")
        model_layout.addWidget(self.token_label)
        
        # Reset token counter button
        self.reset_tokens_button = QPushButton("Reset")
        self.reset_tokens_button.clicked.connect(self.reset_token_counter)
        model_layout.addWidget(self.reset_tokens_button)
        
        layout.addLayout(model_layout)

        self.setLayout(layout)

        self.conversation_history = []

    def add_message(self, speaker, message):
        """Add a message to the chat with proper formatting and speaker separation"""
        # Add blank line if speaker changed
        if self.last_speaker is not None and self.last_speaker != speaker:
            self.chat_list.addItem("")  # Empty item for blank line
        
        # Create message with formatted speaker name
        formatted_message = f"[{speaker}]: {message}"
        self.chat_list.addItem(formatted_message)
        
        # Store the plain text for extraction
        item = self.chat_list.item(self.chat_list.count() - 1)
        item.setData(Qt.UserRole, f"{speaker}: {message}")
        
        # Update last speaker
        self.last_speaker = speaker
        
        # Scroll to bottom
        self.chat_list.scrollToBottom()

    def copy_to_editor(self):
        # Find the last Python code block in the chat history
        last_code_block = None
        
        # Iterate through chat items in reverse order to find the last code block
        for i in range(self.chat_list.count() - 1, -1, -1):
            item = self.chat_list.item(i)
            text = item.data(Qt.UserRole)  # Get stored plain text
            
            # Skip empty items (blank lines)
            if not text or not text.strip():
                continue
            
            # Only check AI responses
            if text.startswith("AI: "):
                response_text = text[4:]
                
                # Find code blocks (```python or ```)
                import re
                code_pattern = r'```(?:python)?\s*\n(.*?)\n```'
                matches = re.findall(code_pattern, response_text, re.DOTALL)
                
                if matches:
                    # Take the last code block from this response
                    last_code_block = matches[-1].strip()
                    break
                else:
                    # If no code blocks, look for indented code
                    lines = response_text.split('\n')
                    code_lines = []
                    in_code = False
                    for line in lines:
                        if line.startswith('    ') or line.startswith('\t'):
                            code_lines.append(line)
                            in_code = True
                        elif in_code and line.strip() == '':
                            code_lines.append(line)
                        elif in_code:
                            break
                    if code_lines:
                        last_code_block = '\n'.join(code_lines).strip()
                        break
        
        if last_code_block:
            self.copy_to_editor_signal.emit(last_code_block)
        else:
            # If no code blocks found in any AI response, show a message
            self.copy_to_editor_signal.emit("# No Python code found in chat history")

    def change_model(self, model):
        self.llm_service.model = model
        self.config_manager.set("model", model)

    def update_model_list(self):
        provider = self.config_manager.get("provider", "openrouter")
        self.model_combo.clear()
        if provider == "openrouter":
            models = [
                "anthropic/claude-3-haiku",
                "openai/gpt-4o-mini",
                "google/gemini-2.5-flash"
            ]
        elif provider == "openai":
            models = [
                "gpt-4o-mini",
            ]
        self.model_combo.addItems(models)
        current = self.llm_service.model
        if current in models:
            self.model_combo.setCurrentText(current)

    def new_chat(self):
        """Clear the chat history and start a new conversation"""
        # Clear the chat list
        self.chat_list.clear()
        
        # Clear conversation history
        self.conversation_history = []
        
        # Reset state variables
        self.last_speaker = None
        if hasattr(self, 'current_ai_item'):
            delattr(self, 'current_ai_item')
        if hasattr(self, 'ai_response_text'):
            delattr(self, 'ai_response_text')

    def send_message(self):
        message = self.input_field.toPlainText().strip()
        if not message:
            return

        # Check if message mentions the script/left window
        script_keywords = ['script', 'left window', 'editor', 'current script', 'existing code']
        mentions_script = any(keyword in message.lower() for keyword in script_keywords)
        
        enhanced_message = message
        if mentions_script and self.editor_widget:
            editor_content = self.editor_widget.get_text()
            tab_title = self.editor_widget.get_current_tab_title()
            
            # Add information about all tabs
            tabs_info = self.editor_widget.get_all_tabs_info()
            tab_titles = []
            for tab in tabs_info:
                title = tab['title']
                if tab['is_current']:
                    title += ' (current)'
                tab_titles.append(title)
            tabs_summary = f"Open tabs: {', '.join(tab_titles)}"
            
            if editor_content.strip():
                enhanced_message = f"{message}\n\n{tabs_summary}\n\nCurrent script in editor (tab: {tab_title}):\n```\n{editor_content}\n```"
            else:
                enhanced_message = f"{message}\n\n{tabs_summary}\n\nCurrent tab ({tab_title}) is empty."

        # Add user message to chat (show original message)
        self.add_message("You", message)
        self.conversation_history.append({"role": "user", "content": enhanced_message})

        # Check if message is asking about knowledge sources
        source_keywords = ['source', 'sources', 'knowledge', 'files', 'documents', 'documents']
        is_source_query = any(keyword in message.lower() for keyword in source_keywords)
        
        # Get context from knowledge
        if self.icl:
            context = self.knowledge_manager.get_full_context()
        else:
            context = self.knowledge_manager.get_relevant_context(enhanced_message)
        
        # If asking about sources, add information about all knowledge files
        if is_source_query and hasattr(self.knowledge_manager, 'local_knowledge'):
            source_info = "Knowledge Base Sources:\n" + "\n".join(f"- {filename}" for filename in sorted(self.knowledge_manager.local_knowledge.keys()))
            context = source_info + "\n\n" + context

        # Start worker thread for LLM response
        self.worker = ChatWorker(self.llm_service, self.knowledge_manager, enhanced_message, context, self.conversation_history.copy(), self.icl)
        self.worker.response_chunk.connect(self.on_response_chunk)
        self.worker.finished.connect(self.on_response_finished)
        self.worker.usage_info.connect(self.on_usage_info)
        self.worker.start()

        self.input_field.clear()

    def on_response_chunk(self, chunk):
        # Add chunk to the last AI message
        if not hasattr(self, 'current_ai_item'):
            # Create initial AI message with formatting
            self.add_message("AI", "")
            self.current_ai_item = self.chat_list.item(self.chat_list.count() - 1)
            self.ai_response_text = ""  # Track the actual response text
        
        # Update the response text
        self.ai_response_text += chunk
        formatted_text = f"[AI]: {self.ai_response_text}"
        self.current_ai_item.setText(formatted_text)
        
        # Update the UserRole data with the current response text
        self.current_ai_item.setData(Qt.UserRole, f"AI: {self.ai_response_text}")
        
        self.chat_list.scrollToBottom()

    def on_response_finished(self):
        # Add to conversation history
        if hasattr(self, 'ai_response_text'):
            self.conversation_history.append({"role": "assistant", "content": self.ai_response_text})
        # Clean up
        if hasattr(self, 'current_ai_item'):
            delattr(self, 'current_ai_item')
        if hasattr(self, 'ai_response_text'):
            delattr(self, 'ai_response_text')
        self.worker.deleteLater()

    def on_usage_info(self, usage):
        """Update token count and cost when usage info is received"""
        if usage:
            input_tokens = usage.get('prompt_tokens', 0)
            output_tokens = usage.get('completion_tokens', 0)
            total_tokens = usage.get('total_tokens', input_tokens + output_tokens)
            
            self.total_tokens += total_tokens
            
            # Calculate cost
            model = self.llm_service.model
            if model in self.pricing:
                input_cost = (input_tokens / 1000000) * self.pricing[model]['input']
                output_cost = (output_tokens / 1000000) * self.pricing[model]['output']
                cost = input_cost + output_cost
                self.total_cost += cost
            else:
                cost = 0.0
            
            # Update display
            self.token_label.setText(f"Tokens: {self.total_tokens} (${self.total_cost:.4f})")

    def reset_token_counter(self):
        """Reset the token counter and cost"""
        self.total_tokens = 0
        self.total_cost = 0.0
        self.token_label.setText("Tokens: 0 ($0.00)")

    def new_chat(self):
        """Start a new chat session"""
        self.chat_list.clear()
        self.conversation_history = []
        self.reset_token_counter()