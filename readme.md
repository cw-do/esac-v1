# ESAC v1 - EQ-SANS Assisting Chatbot

ESAC v1 is an AI-powered desktop application designed to assist with creating, editing, and executing Python scripts for EQ-SANS (Extended Q-range Small Angle Neutron Scattering) experiments at SNS (Spallation Neutron Source). It features a split-pane interface with a Python script editor on the left and an interactive chat window on the right, powered by large language models via OpenRouter API.

## Features

- **AI-Powered Chat**: Interactive chatbot that understands EQ-SANS functions and helps write/edit scripts based on experimental plans.
- **In-Context Learning (ICL)**: Default mode using full knowledge base context for more comprehensive responses.
- **Token & Cost Tracking**: Real-time monitoring of API usage and costs with reset functionality.
- **Agentic Mode (v1.5)**: Autonomous task processing with measurement planning, script generation, review, and automatic execution.
- **Script Editor**: Advanced Python editor with syntax highlighting, line numbers, and code execution.
- **Knowledge Integration**: Access to historical scripts, instrument documentation, and EQ-SANS specific functions.
- **Time Estimation**: Real-time estimation of script execution time based on proton charge and timing parameters.
- **Simulation Mode**: Check scripts for syntax errors without executing.
- **Model Selection**: Choose from multiple LLM models (GPT-4o-mini, Gemini Flash, DeepSeek, Grok).
- **Secure Configuration**: Encrypted storage of API keys and user preferences.

## Installation

### Prerequisites

- Python 3.8 or higher
- Linux, Windows, or macOS

### Steps

1. **Clone or download the repository**:
   ```bash
   git clone <repository-url>
   cd esac_v1
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv esac_env
   source esac_env/bin/activate  # On Windows: esac_env\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure API Key**:
   - Obtain an API key from [OpenRouter](https://openrouter.ai/)
   - Edit the `.env` file in the project root:
     ```
     OPENROUTER_API_KEY=your_api_key_here
     ```
   - The application will encrypt and store this securely on first run.

## Running the Application

1. **Activate the virtual environment** (if using one):
   ```bash
   source esac_env/bin/activate
   ```

2. **Run the application**:
   ```bash
   # Default mode (ICL with chat interface)
   python main.py

   # Traditional chat mode (RAG)
   python main.py --rag

   # Agentic mode (ESAC v1.5)
   python main.py --agent
   ```

The application window will open with the script editor on the left and chat interface on the right (or agent interface for --agent mode).

## Agentic Mode (ESAC v1.5)

The agentic mode provides autonomous EQ-SANS experiment planning and execution:

### Features
- **Task Description**: Describe your experimental needs in natural language
- **Automated Planning**: AI creates detailed measurement plans including sample prep, instrument config, and sequences
- **Script Generation**: Automatically generates complete, executable Python scripts
- **Quality Review**: AI reviews scripts for missing parameters, errors, and safety issues
- **Time Estimation**: Provides execution time estimates
- **User Confirmation**: Shows comprehensive review before execution
- **Automatic Execution**: Runs approved scripts without manual intervention

### Workflow
1. Enter task description (e.g., "Measure temperature series from 25°C to 75°C with 10°C steps")
2. Click "Run Agent" to start autonomous processing
3. Review the generated plan, script, and analysis
4. Confirm execution or modify the task
5. Agent automatically executes the approved script

## Usage

### Basic Workflow

1. **Describe your experiment** in the chat window (e.g., "Create a script for temperature-dependent measurement with 3 temperatures").
2. **Edit the generated script** in the left panel using the AI's suggestions.
3. **Check time estimation** displayed near the Run button (adjust proton charge conversion if needed).
4. **Simulate** the script to check for errors.
5. **Run** the script to execute the experiment.

### Chat Commands

- Ask questions about EQ-SANS functions (e.g., "What is runsampleid?")
- Request script modifications (e.g., "Add a delay of 600 seconds")
- Get help with experimental planning

### Token & Cost Tracking

- Monitor API usage in real-time with token count and USD cost display
- Reset counters with the "Reset" button
- Costs calculated based on current model pricing

### Settings

- Access settings via the menu or button to change LLM model, update API key, or adjust proton charge rate (default: 5.2 PC = 1 hour).

## Configuration

- **API Key**: Set in `.env` file or via settings dialog.
- **LLM Model**: Select from available models in the chat interface.
- **Proton Charge Rate**: Customize the PC to time conversion ratio.
- **Knowledge Base**: The app automatically loads knowledge from the `knowledge/` directory.

## Dependencies

- PyQt5: GUI framework
- requests: HTTP client for API calls
- python-dotenv: Environment variable management
- cryptography: Secure key storage
- PyPDF2: PDF document processing

See `requirements.txt` for exact versions.

## Troubleshooting

- **API Errors**: Check your OpenRouter API key and internet connection.
- **Import Errors**: Ensure all dependencies are installed.
- **Knowledge Not Loading**: Verify files in `knowledge/` directory are readable.
- **Script Execution Issues**: Check Python path and permissions for script execution.

## Development

For developers interested in contributing:

- Code structure follows MVC pattern with GUI, services, and core logic separated.
- Main entry point: `main.py`
- GUI components: `gui/` directory
- Services: `services/` directory
- Knowledge files: `knowledge/` directory

## License

[Specify license if applicable]

## Contact

For questions or support, contact [your contact information].

