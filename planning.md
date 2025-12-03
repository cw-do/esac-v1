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

