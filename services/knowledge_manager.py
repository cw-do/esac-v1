import os
import re
from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import json
import hashlib

class KnowledgeManager:
    def __init__(self):
        self.local_knowledge = {}
        self.model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')  # Small, fast model, force CPU
        self.index = None
        self.documents = []  # List of (filename, text_chunk)
        self.index_file = "knowledge_index.faiss"
        self.docs_file = "knowledge_docs.json"
        self.hash_file = "knowledge_hash.txt"

    def _get_content_hash(self, directories):
        """Get hash of all files in directories to check for changes"""
        hasher = hashlib.md5()
        for directory in directories:
            if os.path.exists(directory):
                for root, _, files in os.walk(directory):
                    for file in sorted(files):
                        if file.endswith(('.txt', '.pdf', '.md', '.json')):
                            filepath = os.path.join(root, file)
                            with open(filepath, 'rb') as f:
                                hasher.update(f.read())
        return hasher.hexdigest()

    def load_or_build_index(self, extra_dirs=None):
        """Load existing index if valid, otherwise build new one"""
        import json  # Ensure json is available
        directories = ["knowledge"]
        if extra_dirs:
            directories.extend(extra_dirs)
        
        current_hash = self._get_content_hash(directories)
        
        if os.path.exists(self.index_file) and os.path.exists(self.docs_file) and os.path.exists(self.hash_file):
            with open(self.hash_file, 'r') as f:
                saved_hash = f.read().strip()
            if saved_hash == current_hash:
                # Load existing
                self.index = faiss.read_index(self.index_file)
                with open(self.docs_file, 'r', encoding='utf-8') as f:
                    self.documents = json.load(f)
                # Also populate local_knowledge for source queries
                self.local_knowledge = {}
                for filename, _ in self.documents:
                    if filename not in self.local_knowledge:
                        # Load the file content if it exists
                        for directory in directories:
                            filepath = os.path.join(directory, filename)
                            if os.path.exists(filepath):
                                try:
                                    if filename.endswith('.txt') or filename.endswith('.md'):
                                        with open(filepath, 'r', encoding='utf-8') as f:
                                            self.local_knowledge[filename] = f.read()
                                    elif filename.endswith('.json'):
                                        with open(filepath, 'r', encoding='utf-8') as f:
                                            data = json.load(f)
                                            self.local_knowledge[filename] = json.dumps(data, indent=2)
                                    elif filename.endswith('.pdf'):
                                        # For PDFs, just mark as loaded
                                        self.local_knowledge[filename] = "[PDF content loaded]"
                                except:
                                    pass
                                break
                print("Loaded existing knowledge index")
                return
        
        # Build new
        print("Building new knowledge index...")
        self.load_local_knowledge(directories)
        with open(self.hash_file, 'w') as f:
            f.write(current_hash)
        print("Knowledge index built and saved")

    def load_local_knowledge(self, directories=["knowledge"]):
        self.local_knowledge = {}
        self.documents = []
        
        for knowledge_dir in directories:
            if os.path.exists(knowledge_dir):
                for file in os.listdir(knowledge_dir):
                    filepath = os.path.join(knowledge_dir, file)
                    try:
                        if file.endswith(".txt") or file.endswith(".md"):
                            with open(filepath, "r", encoding="utf-8") as f:
                                content = f.read()
                                self.local_knowledge[file] = content
                                self._chunk_and_store(file, content)
                        elif file.endswith(".pdf"):
                            reader = PdfReader(filepath)
                            text = ""
                            for page in reader.pages:
                                text += page.extract_text() + "\n"
                            self.local_knowledge[file] = text
                            self._chunk_and_store(file, text)
                        elif file.endswith(".json"):
                            with open(filepath, "r", encoding="utf-8") as f:
                                json_data = json.load(f)
                                # Convert JSON to readable text format
                                content = json.dumps(json_data, indent=2)
                                self.local_knowledge[file] = content
                                self._chunk_and_store(file, content)
                    except Exception as e:
                        print(f"Error loading {file}: {e}")
        
        # Build FAISS index
        if self.documents:
            embeddings = self.model.encode([doc[1] for doc in self.documents])
            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine
            faiss.normalize_L2(embeddings)  # Normalize for cosine similarity
            self.index.add(embeddings)
            
            # Save index and documents
            faiss.write_index(self.index, self.index_file)
            with open(self.docs_file, 'w', encoding='utf-8') as f:
                json.dump(self.documents, f, ensure_ascii=False, indent=2)

    def _chunk_and_store(self, filename, content):
        # Function-aware chunking: split by function definitions for better retrieval
        lines = content.split('\n')
        current_chunk = ""
        in_function = False
        
        for line in lines:
            stripped = line.strip()
            
            # Check if this is a function definition
            if stripped.startswith('def '):
                # Save previous chunk if it exists
                if current_chunk.strip():
                    self.documents.append((filename, current_chunk.strip()))
                
                # Start new chunk with this function
                current_chunk = line + '\n'
                in_function = True
            elif in_function and stripped and not stripped.startswith('#'):
                # Continue adding to current function chunk
                current_chunk += line + '\n'
                
                # If we hit an empty line after function content, consider function complete
                if not stripped:
                    in_function = False
            else:
                # Non-function content or comments
                if current_chunk:
                    current_chunk += line + '\n'
                else:
                    # Start new chunk for non-function content
                    current_chunk = line + '\n'
        
        # Add the last chunk
        if current_chunk.strip():
            self.documents.append((filename, current_chunk.strip()))
        
        # Check if this file produced any chunks from function-based chunking
        file_chunks = [doc for doc in self.documents if doc[0] == filename]
        chunks_from_function_parsing = len(file_chunks)
        
        # If we have very few chunks total OR this file produced no chunks, fall back to character-based chunking
        if len(self.documents) < 5 or chunks_from_function_parsing == 0:
            # Remove any chunks from this file
            self.documents = [doc for doc in self.documents if doc[0] != filename]
            
            # Fallback: character-based chunking
            chunk_size = 2000
            overlap = 200
            
            words = content.split()
            current_chunk = ""
            
            for word in words:
                if len(current_chunk) + len(word) + 1 > chunk_size:
                    if current_chunk:
                        self.documents.append((filename, current_chunk.strip()))
                        # Start new chunk with overlap
                        overlap_words = current_chunk.split()[-5:]  # Last 5 words as overlap
                        current_chunk = ' '.join(overlap_words) + ' ' + word
                else:
                    current_chunk += ' ' + word
            
            if current_chunk:
                self.documents.append((filename, current_chunk.strip()))

    def get_relevant_context(self, query, max_length=12000):
        """Get relevant context using semantic search with embeddings"""
        if not self.index or not self.documents:
            return self._fallback_context(query, max_length)
        
        # Encode query
        query_embedding = self.model.encode([query])[0]
        faiss.normalize_L2(query_embedding.reshape(1, -1))
        
        # Search for top-k similar documents
        k = 25  # Retrieve more for better context
        distances, indices = self.index.search(query_embedding.reshape(1, -1), k)
        
        relevant_parts = []
        seen_files = set()
        retrieved_chunks = set()
        
        # FIRST: Check for specific function names mentioned in the query
        mentioned_parts = []
        query_lower = query.lower()
        
        for filename, chunk in self.documents:
            chunk_key = (filename, hash(chunk))
            if chunk_key not in retrieved_chunks:
                # Check if chunk contains a function definition that matches any word in the query
                func_match = re.search(r'\bdef\s+(\w+)\s*\(', chunk)
                if func_match:
                    func_name = func_match.group(1)
                    if func_name.lower() in query_lower:
                        mentioned_parts.append(f"Requested function from {filename}:\n{chunk}")
                        retrieved_chunks.add(chunk_key)
        
        # SECOND: add semantically similar chunks
        for idx in indices[0]:
            if idx < len(self.documents):
                filename, chunk = self.documents[idx]
                chunk_key = (filename, hash(chunk))
                if chunk_key not in retrieved_chunks:
                    relevant_parts.append(f"From {filename}:\n{chunk}")
                    retrieved_chunks.add(chunk_key)
        
        # THIRD: add chunks that contain function definitions with query keywords
        query_keywords = set(re.findall(r'\b\w+\b', query_lower))
        
        keyword_parts = []
        for filename, chunk in self.documents:
            chunk_lower = chunk.lower()
            chunk_key = (filename, hash(chunk))
            if (chunk_key not in retrieved_chunks and 
                'def ' in chunk and 
                any(keyword in chunk_lower for keyword in query_keywords if len(keyword) > 3)):
                keyword_parts.append(f"Function match from {filename}:\n{chunk}")
                retrieved_chunks.add(chunk_key)
        
        # Combine: mentioned functions first, then keyword matches, then semantic matches
        relevant_parts = mentioned_parts + keyword_parts + relevant_parts
        
        # Additional: If query mentions "function", also include function definitions containing keywords
        if 'function' in query_lower:
            for filename, content in self.local_knowledge.items():
                if 'def ' in content:
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if line.strip().startswith('def ') and any(word in line.lower() for word in query_keywords):
                            # Find the full function
                            func_lines = [line]
                            for j in range(i + 1, len(lines)):
                                if lines[j].strip() and not lines[j].strip().startswith('def '):
                                    func_lines.append(lines[j])
                                else:
                                    break
                            func_text = '\n'.join(func_lines)
                            relevant_parts.append(f"Function from {filename}:\n{func_text}")
                            break  # One per file
        
        context = "\n\n".join(relevant_parts)
        return context[:max_length] if len(context) > max_length else context

    def _fallback_context(self, query, max_length):
        """Fallback to keyword search if embeddings not available"""
        relevant_parts = []
        function_parts = []
        query_lower = query.lower()

        for filename, content in self.local_knowledge.items():
            # Check if query mentions this file
            if filename.lower() in query_lower:
                relevant_parts.append(f"From {filename}:\n{content}")
                continue
            
            # Look for function definitions
            if 'def ' in content:
                lines = content.split('\n')
                matching_functions = []
                query_words = set(re.findall(r'\b\w+\b', query_lower))
                i = 0
                while i < len(lines):
                    line = lines[i]
                    if line.strip().startswith('def '):
                        func_name = line.split('(')[0].replace('def ', '').strip()
                        if func_name in query_words:
                            # Include the function definition
                            func_lines = []
                            func_lines.append(line)
                            # Add next lines until empty line or next def
                            j = i + 1
                            while j < len(lines) and lines[j].strip() and not lines[j].strip().startswith('def '):
                                func_lines.append(lines[j])
                                j += 1
                            matching_functions.append('\n'.join(func_lines))
                            i = j
                        else:
                            i += 1
                    else:
                        i += 1
                if matching_functions:
                    function_parts.append(f"From {filename}:\n" + '\n\n'.join(matching_functions))
            
            # Simple keyword matching for other content
            query_words = set(re.findall(r'\b\w+\b', query_lower))
            content_lower = content.lower()
            
            if query_words & set(re.findall(r'\b\w+\b', content_lower)):
                # Extract relevant sections
                sections = content.split('\n\n')  # Split by paragraphs
                relevant_sections = []
                for section in sections:
                    if any(word in section.lower() for word in query_words):
                        relevant_sections.append(section.strip())
                
                if relevant_sections:
                    relevant_parts.append(f"From {filename}:\n" + '\n\n'.join(relevant_sections[:2]))

        # Put function parts first
        all_parts = function_parts + relevant_parts
        context = "\n\n".join(all_parts)
        return context[:max_length] if len(context) > max_length else context

    def get_full_context(self, max_length=8000):
        """Get all local knowledge as context, truncated if too long"""
        context_parts = []
        for filename, content in self.local_knowledge.items():
            context_parts.append(f"=== {filename} ===\n{content}\n")
        
        full_context = "\n".join(context_parts)
        return full_context[:max_length] if len(full_context) > max_length else full_context