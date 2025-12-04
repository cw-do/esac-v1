import os
import re
from PyPDF2 import PdfReader
import json
import hashlib

class KnowledgeManager:
    def __init__(self):
        self.local_knowledge = {}
        # Removed: model, index, documents, FAISS files

    def load_or_build_index(self, extra_dirs=None):
        """Load knowledge base text files (simplified for ICL mode only)"""
        directories = ["knowledge"]
        if extra_dirs:
            directories.extend(extra_dirs)

        # Load all knowledge files
        self.load_local_knowledge(directories)
        print("Knowledge base loaded for ICL mode")

    def load_local_knowledge(self, directories=["knowledge"]):
        """Load all knowledge files into memory"""
        self.local_knowledge = {}

        for knowledge_dir in directories:
            if os.path.exists(knowledge_dir):
                for file in os.listdir(knowledge_dir):
                    filepath = os.path.join(knowledge_dir, file)
                    try:
                        if file.endswith(".txt") or file.endswith(".md"):
                            with open(filepath, "r", encoding="utf-8") as f:
                                content = f.read()
                                self.local_knowledge[file] = content
                        elif file.endswith(".pdf"):
                            reader = PdfReader(filepath)
                            text = ""
                            for page in reader.pages:
                                text += page.extract_text() + "\n"
                            self.local_knowledge[file] = text
                        elif file.endswith(".json"):
                            with open(filepath, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                self.local_knowledge[file] = json.dumps(data, indent=2)
                    except Exception as e:
                        print(f"Error loading {file}: {e}")

    def get_full_context(self, max_length=100000):
        """Get all local knowledge as context for ICL mode"""
        context_parts = []
        for filename, content in self.local_knowledge.items():
            context_parts.append(f"=== {filename} ===\n{content}\n")

        full_context = "\n".join(context_parts)
        return full_context[:max_length] if len(full_context) > max_length else full_context