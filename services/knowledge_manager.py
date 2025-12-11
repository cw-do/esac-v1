import os
import re
from PyPDF2 import PdfReader
import json
import hashlib
import sys

# Priority files loaded for ICL (full context) - update this list as needed
PRIORITY_FILES = [
    'eqsans_scanfunctions_live.py',
    'module1.md',
    'module2.md', 
    'module3.md',
    'module4.md',
    'module5.md',
    'module6.md',
]

class KnowledgeManager:
    def __init__(self):
        self.local_knowledge = {}
        self.rag_only = set()  # Files that are only for RAG, not included in full ICL context

    def load_or_build_index(self, extra_dirs=None):
        """Load knowledge base text files for both ICL and RAG modes"""
        directories = ["knowledge"]
        if extra_dirs:
            directories.extend(extra_dirs)
        
        # Load all knowledge files
        self.load_local_knowledge(directories)
        print(f"Knowledge base loaded with {len(self.local_knowledge)} files")
        # print loaded filenames with full paths
        # for filename in sorted(self.local_knowledge.keys()):
        #     print(f"  - {filename}")


    def load_local_knowledge(self, directories=["knowledge"]):
        """Load all knowledge files into memory"""
        self.local_knowledge = {}

        if hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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
            full_dir = os.path.join(base_path, knowledge_dir)
            if os.path.exists(full_dir):
                for file in os.listdir(full_dir):
                    filepath = os.path.join(full_dir, file)
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

        # Mark non-priority static files as RAG-only
        for filename in self.local_knowledge:
            if filename not in PRIORITY_FILES:
                self.rag_only.add(filename)

    def get_full_context(self, max_length=100000):
        """Get all local knowledge as context for ICL mode"""
        # Prioritize specified files for ICL
        priority_files = [f for f in PRIORITY_FILES if f in self.local_knowledge]
        other_files = [f for f in self.local_knowledge.keys() if f not in PRIORITY_FILES and f not in self.rag_only]
        
        # Build context with priority files first
        context_parts = []
        for filename in priority_files + other_files:
            if filename in self.local_knowledge:
                content = self.local_knowledge[filename]
                context_parts.append(f"=== {filename} ===\n{content}\n")

        full_context = "\n".join(context_parts)
        
        # If we're going to truncate, at least include the priority file completely
        
        # If we're going to truncate, at least include the priority file completely
        if len(full_context) > max_length:
            # Try to fit the priority files completely
            priority_content = ""
            for filename in priority_files:
                if filename in self.local_knowledge:
                    priority_content += f"=== {filename} ===\n{self.local_knowledge[filename]}\n"
            
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
                # If priority files alone exceed limit, truncate them
                full_context = priority_content[:max_length]
        
        return full_context

    #updated one
    def get_relevant_context(self, query, max_length=100000):
        """Get relevant context for RAG mode based on query similarity"""
        if not self.local_knowledge:
            return "No knowledge base loaded."

        import re
        from collections import defaultdict
        
        # Prepare query for matching
        query_lower = query.lower()
        query_words = set(re.findall(r'\b\w+\b', query_lower))
        
        # Score each file based on relevance
        file_scores = {}
        relevant_sections = defaultdict(list)
        
        for filename, content in self.local_knowledge.items():
            content_lower = content.lower()
            score = 0
            
            # Exact phrase matches (highest weight)
            if query_lower in content_lower:
                score += 100
            
            # Function name matches (high weight)
            func_pattern = r'def\s+(\w+)\s*\('
            functions = re.findall(func_pattern, content)
            for func in functions:
                if func.lower() in query_lower or any(word in func.lower() for word in query_words):
                    score += 50
            
            # Keyword matches
            keyword_matches = sum(1 for word in query_words if word in content_lower)
            score += keyword_matches * 10
            
            # Technical term matches (medium weight)
            technical_terms = ['eqsans', 'sans', 'scan', 'function', 'script', 'instrument', 'detector', 'sample', 'transmission', 'scattering']
            for term in technical_terms:
                if term in query_lower and term in content_lower:
                    score += 20
            
            file_scores[filename] = score
            
            # Extract relevant sections from this file
            if score > 0:
                lines = content.split('\n')
                relevant_lines = []
                
                # For markdown files, extract entire sections based on headers
                if filename.endswith('.md'):
                    sections = re.split(r'(^#{1,6}\s+.*$)', content, flags=re.MULTILINE)
                    for i in range(1, len(sections), 2):  # Headers are at odd indices
                        header = sections[i].strip()
                        section_content = sections[i+1] if i+1 < len(sections) else ""
                        if any(word in header.lower() for word in query_words) or any(word in section_content.lower() for word in query_words):
                            relevant_lines.append(header)
                            relevant_lines.extend(section_content.split('\n'))
                            relevant_lines.append("")
                else:
                    # Original line-by-line extraction for non-markdown files
                    for i, line in enumerate(lines):
                        line_lower = line.lower()
                        line_score = 0
                        
                        # Check for function definitions
                        if re.search(func_pattern, line):
                            func_name = re.search(func_pattern, line).group(1)
                            if any(word in func_name.lower() for word in query_words):
                                line_score += 50
                        
                        # Check for keyword matches
                        if any(word in line_lower for word in query_words):
                            line_score += 10
                        
                        # Check for technical terms
                        if any(term in line_lower for term in technical_terms if term in query_lower):
                            line_score += 5
                        
                        if line_score > 0:
                            # Include expanded context around the relevant line (increased from 2/3 to 5/10)
                            start = max(0, i - 5)
                            end = min(len(lines), i + 10)
                            context_lines = lines[start:end]
                            relevant_lines.extend(context_lines)
                            relevant_lines.append("")  # Add blank line between sections
                
                if relevant_lines:
                    # Remove duplicates while preserving order
                    seen = set()
                    unique_lines = []
                    for line in relevant_lines:
                        if line not in seen:
                            unique_lines.append(line)
                            seen.add(line)
                    
                    relevant_sections[filename] = unique_lines
        
        # Sort files by relevance score
        sorted_files = sorted(file_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Build context from most relevant files
        context_parts = []
        total_length = 0
        
        for filename, score in sorted_files:
            if score == 0:
                continue
                
            file_content = f"=== {filename} (relevance: {score}) ===\n"
            
            if filename in relevant_sections:
                # Use extracted relevant sections
                section_content = '\n'.join(relevant_sections[filename])
                file_content += section_content
            else:
                # Fallback to full file content if no sections extracted
                file_content += self.local_knowledge[filename]
            
            # Check if adding this file would exceed the limit
            if total_length + len(file_content) > max_length:
                # Truncate this file to fit
                available_space = max_length - total_length
                if available_space > len(f"=== {filename} (relevance: {score}) ===\n"):
                    truncated_content = file_content[:available_space]
                    context_parts.append(truncated_content)
                break
            else:
                context_parts.append(file_content)
                total_length += len(file_content)
        
        if not context_parts:
            # If no relevant content found, return a sample from the most important file
            priority_file = 'eqsans_scanfunctions_live.py'
            if priority_file in self.local_knowledge:
                content = self.local_knowledge[priority_file]
                # Return first 2000 characters as fallback
                return f"=== {priority_file} ===\n{content[:2000]}..."
            else:
                return "No relevant knowledge found for this query."
        
        return '\n\n'.join(context_parts)

