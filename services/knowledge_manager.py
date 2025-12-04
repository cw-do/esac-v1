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

        # Check for the specific eqsans_scanfunctions_live.py file first
        dev_script_path = "/home/controls/var/tmp/scripting/dev/eqsans_scanfunctions_live.py"
        if os.path.exists(dev_script_path):
            try:
                with open(dev_script_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    self.local_knowledge["eqsans_scanfunctions_live.py"] = content
                    print(f"Loaded development script from: {dev_script_path}")
            except Exception as e:
                print(f"Error loading development script {dev_script_path}: {e}")

        for knowledge_dir in directories:
            if os.path.exists(knowledge_dir):
                for file in os.listdir(knowledge_dir):
                    filepath = os.path.join(knowledge_dir, file)
                    try:
                        # Skip eqsans_scanfunctions_live.py if we already loaded it from dev path
                        if file == "eqsans_scanfunctions_live.py" and "eqsans_scanfunctions_live.py" in self.local_knowledge:
                            print(f"Skipping local {file} - already loaded from dev path")
                            continue
                            
                        if file.endswith((".txt", ".md", ".py")):
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
        # Prioritize eqsans_scanfunctions_live.py as it's most important for function definitions
        priority_files = ['eqsans_scanfunctions_live.py']
        other_files = [f for f in self.local_knowledge.keys() if f not in priority_files]
        
        # Build context with priority files first
        context_parts = []
        for filename in priority_files + other_files:
            if filename in self.local_knowledge:
                content = self.local_knowledge[filename]
                context_parts.append(f"=== {filename} ===\n{content}\n")

        full_context = "\n".join(context_parts)
        
        # If we're going to truncate, at least include the priority file completely
        if len(full_context) > max_length:
            # Try to fit the priority file completely
            priority_content = ""
            if priority_files and priority_files[0] in self.local_knowledge:
                priority_content = f"=== {priority_files[0]} ===\n{self.local_knowledge[priority_files[0]]}\n"
            
            remaining_length = max_length - len(priority_content)
            if remaining_length > 0:
                other_content = ""
                for filename in other_files:
                    if filename in self.local_knowledge:
                        file_content = f"=== {filename} ===\n{self.local_knowledge[filename]}\n"
                        if len(other_content) + len(file_content) <= remaining_length:
                            other_content += file_content
                        else:
                            # Truncate this file if needed
                            available_space = remaining_length - len(other_content)
                            if available_space > len(f"=== {filename} ===\n"):
                                truncated_content = self.local_knowledge[filename][:available_space - len(f"=== {filename} ===\n") - 1]
                                other_content += f"=== {filename} ===\n{truncated_content}\n"
                            break
                full_context = priority_content + other_content
            else:
                # If priority file alone exceeds limit, truncate it
                full_context = priority_content[:max_length]
        
        return full_context