# ESAC v1 - EQ-SANS Assisting Chatbot

ESAC v1 is an AI-powered desktop application designed to assist with creating, editing, and executing Python scripts for EQ-SANS (Extended Q-range Small Angle Neutron Scattering) experiments at SNS (Spallation Neutron Source). It features a split-pane interface with a Python script editor on the left and an interactive chat window on the right, powered by large language models via OpenRouter API.

## Features

- **AI-Powered Chat**: Interactive chatbot that understands EQ-SANS functions and helps write/edit scripts based on experimental plans.
- **In-Context Learning (ICL)**: Default mode using full knowledge base context for more comprehensive responses.
- **Retrieval-Augmented Generation (RAG)**: Smart retrieval mode that provides targeted, relevant context for specific queries.
- **Q-Range Calculator**: Instant calculation of Q-ranges, wavelengths, and beam parameters for specific instrument configurations (e.g., "what is q range of 4m 2.5a config"). Loads config files from `/home/controls/var/QRangeConfigurations` and computes values using beamline-specific formulas.
- **Token & Cost Tracking**: Real-time monitoring of API usage and costs with reset functionality.
- **Script Editor**: Advanced Python editor with syntax highlighting, line numbers, and code execution.
- **Knowledge Integration**: Access to historical scripts, instrument documentation, and EQ-SANS specific functions.
- **File Search**: Quickly find and load past scripts for repeated use, with non-blocking background processing to maintain responsive UI during searches.
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
   # Default mode (ICL - comprehensive context)
   python main.py

   # RAG mode (smart retrieval for specific queries)
   python main.py --rag
   ```

The application window will open with the script editor on the left and chat interface on the right.

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
- Query Q-ranges for configurations (e.g., "what is q range of 4m 2.5a config", "show me q range of 9m 15a configuration")

### Q-Range Calculator

The chatbot includes a specialized Q-range calculator that can instantly compute scattering parameters for EQ-SANS configurations:

- **Query Format**: Ask natural language questions like "q range of 4m 2.5a config" or "what's the Q-range for the 9m setup at 15Å"
- **Automatic Matching**: Uses AI to match your query to available instrument configurations
- **Calculated Parameters**: Returns QMin, QMax, QMaxEdge, wavelength ranges, TOF ranges, and beam diameter
- **Config Sources**: Loads parameters from `.sav` files in `/home/controls/var/QRangeConfigurations/`
- **Frequency Handling**: Automatically selects 60Hz configurations by default; supports both 30Hz and 60Hz modes

Example output:
```
QMin: 0.0025 Å⁻¹
QMax: 0.45 Å⁻¹  
QMaxEdge: 0.38 Å⁻¹
Wavelength Min: 10.0 Å
Wavelength Max: 15.2 Å
...
```

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
- **Q-Range Configs**: Configurations loaded from `/home/controls/var/QRangeConfigurations/` for calculator functionality.

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
- **Q-Range Calculation Errors**: Check that config files exist in `/home/controls/var/QRangeConfigurations/` and are readable.
- **Script Execution Issues**: Check Python path and permissions for script execution.

## Development

For developers interested in contributing:

- Code structure follows MVC pattern with GUI, services, and core logic separated.
- Main entry point: `main.py`
- GUI components: `gui/` directory
- Services: `services/` directory
- Knowledge files: `knowledge/` directory
- Q-Range Calculator: `services/qrange_calculator.py`

## License

[Specify license if applicable]

## Contact

For questions or support, contact [your contact information].

