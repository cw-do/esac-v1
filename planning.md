# title of the code: ESAC v1
ESAC is EQ-SANS Assisting Chatbot. LLM powered chatbot to help create script, edit and execute. This software package should create a python script editor style window on the left side. On the left side, there should a chat window just like the copilot chat window attached to the VSCODE. The chat window should help editing the script on the left following user's request. Once the script is satisfatory, users should be able to save and execute it by clicking 'run' button. There should also be a 'simulate' button if possible which will not execute, but only simulate and check for syntax errors or estimate time. 

# Functions
- The Chatbot should know all the previous scripts and knowledge located in the following locations

    1. /home/controls/var/tmp folder: There are subfolders named YYYYA or YYYYB such as 2021A or 2025B, indicating the operation cycle. Inside, python scripts can be found. they were used to run various experiments with various sample environment controls and experimental strategies.
    2. ./knowledge : There are text files explaining some example scripts and additional information about instruments. 
    3. /home/controls/var/tmp/scripting/dev/eqsans_scanfunctions_live.py : This file is the main python script file that contains all the scrip commands developed specifically for the operation of eq-sans. This is live document, often updated or modified.

- After understanding all these information, the chatbot should be able to write a script to run user experiment based on users' experimental plan. Also satisfy time-constraints if needed.

- the chat bot will use LLM via open router. the API key is here, this should be embeded in the .env file. 
openrouter_key = "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"

- The chat model should be selectable. give a few options such as gpt4o-mini or gemini-2.5-flash, deepseek, or grok. (this is suggestion, find correct names)

- chat should show the results (AI's responses) in real time rather than waiting full tokens are received. 

- Run button or run command from the chat window should execute current script in the editor window. In our system, python [script_file] submits the jobs. 

- show the estimated time for the current script in realtime. It can be displayed next to the run button. 

- When converting proton charge to time, it is currently 5.2 pc = 1 hour.  However, make a input space near the estimated time display so that users can define pc value for 1 hour. 


# Code Structure and Approach

## Overall Architecture
ESAC v1 will be implemented as a native Python desktop application using PyQt5/PySide6 for the GUI, providing a lightweight, fast interface without web browsers. The application features a split-pane layout with a Python script editor on the left and a chat window on the right. The architecture consists of:

- **Main Application**: PyQt-based GUI handling all user interactions, editor, and chat display.
- **LLM Service**: Asynchronous module for OpenRouter API calls with streaming support.
- **Knowledge Manager**: Module for loading and indexing historical scripts and documentation.
- **Script Executor**: Module for running Python scripts and estimating execution time.
- **Configuration Manager**: Handles API keys, model selection, and user preferences.

## Key Components

### 1. Main GUI (Python/PyQt)
- `main.py`: Application entry point, initializes GUI and connects signals.
- `gui/editor_widget.py`: Custom text editor widget with Python syntax highlighting.
- `gui/chat_widget.py`: Chat interface with message history and input field.
- `gui/main_window.py`: Main window layout with split panes, buttons, and status displays.
- `gui/settings_dialog.py`: Dialog for model selection, API key management, and proton charge settings.

### 2. Core Services (Python)
- `services/llm_service.py`: Handles OpenRouter API communication, model selection, and streaming responses.
- `services/knowledge_manager.py`: Loads and searches knowledge from specified directories.
- `services/script_executor.py`: Manages script execution via subprocess and time estimation.
- `services/qrange_calculator.py`: Calculates Q-range parameters for EQ-SANS configurations.

### 3. Q-Range Calculator Feature
The chatbot now supports direct Q-range calculations for instrument configurations. Users can query configurations like "what is q range of 4m 2.5a config" and receive calculated values including:
- QMin, QMaxEdge, QMaxCorner
- Wavelength ranges (WLMin, WLMax, WL2Min, WL2Max for frame-skipping)
- TOF ranges
- Beam diameter

The feature:
- Parses natural language queries for config names
- Loads configuration data from /home/controls/var/QRangeConfigurations/*.sav files
- Uses calculation logic adapted from qplan.py
- Returns formatted results directly in chat without LLM processing
- Handles config not found gracefully
- `services/config_manager.py`: Manages application settings and secure storage of API keys.

### 3. Knowledge Processing
- Initially load and index text files from `./knowledge` directory for immediate use.
- Provide optional access to `/home/controls/var/tmp` scripts and `eqsans_scanfunctions_live.py` when directories become accessible.
- Add a "Build Knowledge Base" button for users to optionally create a local vector store from accessible directories when updates occur, improving efficiency for repeated queries.
- Use simple text-based search for local knowledge injection, with vector store for enhanced performance when built.

## Implementation Approach

### Phase 1: Core Infrastructure
1. Set up PyQt5/PySide6 project with Python 3.8+.
2. Implement basic split-pane GUI with text editor and chat widgets.
3. Establish OpenRouter API integration with model selection.
4. Implement real-time streaming chat responses using QThread for async operations.

### Phase 2: Knowledge Integration
1. Develop knowledge loader for historical scripts and documentation.
2. Implement context injection into LLM prompts based on user queries.
3. Add intelligent script suggestions based on experimental plans.

### Phase 3: Execution and Simulation
1. Implement script execution using Python's subprocess module.
2. Add syntax checking using ast module for simulation mode.
3. Develop time estimation algorithm using proton charge conversion.
4. Add user-configurable proton charge input field.

### Phase 4: Advanced Features
1. Implement script history, undo/redo, and file management.
2. Add export/import functionality for scripts and chat logs.
3. Implement dark/light theme switching.
4. Add keyboard shortcuts and customizable keybindings.

## Technical Considerations

- **LLM Integration**: Use requests library for API calls. Implement streaming via Server-Sent Events or chunked responses.
- **Knowledge Base**: Use simple text indexing initially; consider SQLite for structured storage.
- **Security**: Store API keys encrypted in local config file. Validate all script execution.
- **Performance**: Use QThread for non-blocking operations. Cache knowledge queries.
- **User Experience**: Ensure responsive GUI with progress indicators, error handling, and intuitive navigation.
- **Cross-Platform**: Test on Linux, Windows, and macOS. Use PyQt's platform-specific features.

## Dependencies
- Python 3.8+
- PyQt5 or PySide6 (Qt GUI framework)
- requests (HTTP client for API calls)
- QScintilla (for advanced text editing features, optional)
- python-dotenv (for .env file handling)
- cryptography (for secure API key storage)

## Distribution
- Package using PyInstaller for standalone executables
- Create .deb/.rpm packages for Linux distribution
- Include requirements.txt and setup.py for easy installation
- Provide installation instructions for users

This native Python approach ensures fast startup and responsive performance on Linux systems, while maintaining all required functionality in a lightweight, self-contained application.


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
                        # Include context around the relevant line
                        start = max(0, i - 2)
                        end = min(len(lines), i + 3)
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