import os
import json
from cryptography.fernet import Fernet, InvalidToken
from dotenv import load_dotenv

class ConfigManager:
    def __init__(self, config_file="config.json", key_file="key.key"):
        self.config_file = config_file
        self.key_file = key_file
        self.config = {}
        self.cipher = None

        # Load .env file
        load_dotenv()

        self._load_or_create_key()
        self._load_config()

    def _load_or_create_key(self):
        if os.path.exists(self.key_file):
            with open(self.key_file, "rb") as f:
                key = f.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_file, "wb") as f:
                f.write(key)
        self.cipher = Fernet(key)

    def _load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "rb") as f:
                    encrypted_data = f.read()
                if encrypted_data:
                    decrypted_data = self.cipher.decrypt(encrypted_data)
                    self.config = json.loads(decrypted_data.decode())
                else:
                    self.config = {}
            except (InvalidToken, Exception) as e:
                print(f"Warning: Could not decrypt config file ({e}). Starting with default config.")
                # Remove corrupted config file
                if os.path.exists(self.config_file):
                    os.remove(self.config_file)
                self.config = {}
        else:
            self.config = {}

        # Set defaults
        if 'provider' not in self.config:
            self.config['provider'] = 'openrouter'
        if 'base_url' not in self.config:
            self.config['base_url'] = 'https://openrouter.ai/api/v1'
        if 'model' not in self.config:
            self.config['model'] = 'openai/gpt-4o-mini'

    def _save_config(self):
        data = json.dumps(self.config).encode()
        encrypted_data = self.cipher.encrypt(data)
        with open(self.config_file, "wb") as f:
            f.write(encrypted_data)

    def get(self, key, default=None):
        # First check environment variables
        env_key = f"OPENROUTER_API_KEY" if key == "api_key" else key.upper()
        env_value = os.getenv(env_key)
        if env_value:
            return env_value
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self._save_config()