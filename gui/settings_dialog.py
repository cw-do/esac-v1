from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton, QFormLayout
from services.config_manager import ConfigManager
from services.llm_service import LLMService

class SettingsDialog(QDialog):
    def __init__(self, config_manager, llm_service):
        super().__init__()
        self.config_manager = config_manager
        self.llm_service = llm_service

        self.setWindowTitle("Settings")
        self.setModal(True)

        layout = QVBoxLayout()

        form_layout = QFormLayout()

        # Provider selection
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["openrouter", "openai"])
        current_provider = self.config_manager.get("provider", "openrouter")
        self.provider_combo.setCurrentText(current_provider)
        self.provider_combo.currentTextChanged.connect(self.on_provider_changed)
        form_layout.addRow("Provider:", self.provider_combo)

        # Base URL
        self.base_url_input = QLineEdit()
        current_base_url = self.config_manager.get("base_url", "https://openrouter.ai/api/v1")
        self.base_url_input.setText(current_base_url)
        form_layout.addRow("Base URL:", self.base_url_input)

        # Model selection
        self.model_combo = QComboBox()
        self.update_model_list()
        current_model = self.config_manager.get("model", "openai/gpt-4o-mini")
        self.model_combo.setCurrentText(current_model)
        form_layout.addRow("Model:", self.model_combo)

        # API Key
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        current_key = self.config_manager.get("api_key", "")
        self.api_key_input.setText(current_key)
        form_layout.addRow("API Key:", self.api_key_input)

        layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_settings)
        button_layout.addWidget(save_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def on_provider_changed(self):
        provider = self.provider_combo.currentText()
        if provider == "openrouter":
            self.base_url_input.setText("https://openrouter.ai/api/v1")
        elif provider == "openai":
            self.base_url_input.setText("https://api.openai.com/v1")
        self.update_model_list()

    def update_model_list(self):
        provider = self.provider_combo.currentText()
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

    def save_settings(self):
        provider = self.provider_combo.currentText()
        base_url = self.base_url_input.text()
        model = self.model_combo.currentText()
        api_key = self.api_key_input.text()

        self.config_manager.set("provider", provider)
        self.config_manager.set("base_url", base_url)
        self.config_manager.set("model", model)
        self.config_manager.set("api_key", api_key)
        self.llm_service.update_config(provider, base_url, model, api_key)

        self.accept()