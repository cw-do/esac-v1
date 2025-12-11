import requests
import json
from services.config_manager import ConfigManager

class LLMService:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.provider = self.config_manager.get("provider", "openrouter")
        self.base_url = self.config_manager.get("base_url", "https://openrouter.ai/api/v1")
        self.model = self.config_manager.get("model", "openai/gpt-4o-mini")
        self.api_key = self.config_manager.get("api_key", "")

    def update_config(self, provider, base_url, model, api_key):
        self.provider = provider
        self.base_url = base_url
        self.model = model
        self.api_key = api_key

    def generate_response_stream(self, message, context="", callback=None, conversation_history=None, icl=False):
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        if icl:
            system_prompt = f"""You are the EQ-SANS experiment assistant. Use the provided knowledge base below to generate scripts and answer questions. Consider the conversation history when responding to follow-up questions or when referring to previous messages. Follow all rules from the modules.

Knowledge Base:
{context}

Core Rules:
- Follow real EQ-SANS instrument commands only.
- Apply sequence: imports → setipts → transmission → scattering.
- Enforce temperature rules, safety limits, and correct configuration order.
- When uncertain, ask for clarification.
- Handle missing details using defaults: IPTS=99999, ITEMS=0, etc.
- Always prefer rules over examples. Do not invent commands.

When providing templates:
1. Copy the exact template code from the knowledge base
2. Do not add comments, explanations, or modifications unless they appear in the original template
3. Replace placeholder values (like CONFIG) with appropriate values from the knowledge base
4. If no exact template matches, search for the knowledge base again and provide the closest match without modification

When answering questions about functions:
1. Look for function definitions in the Python files (starting with 'def function_name(parameters):')
2. Read the docstrings and comments within each function to understand its purpose
3. Use the exact function names, parameters, and behaviors as defined in the code
4. Reference the scan functions and instrument controls exactly as they appear in eqsans_scanfunctions_live.py
5. For any question about a function, quote directly from its definition and docstring in the knowledge base
6. When listing available functions, scan through the Python code and extract function names with their purposes

When generating scripts:
- Use only the functions that are explicitly defined in the eqsans_scanfunctions_live.py file
- Do not create new functions or modify existing function signatures
- Follow the exact calling conventions shown in the code examples"""
        else:
            system_prompt = f"""You are the EQ-SANS experiment assistant. Use ONLY the retrieved RAG documents below to generate scripts and answer questions. Follow all rules from the modules.

CRITICAL RESTRICTIONS:
- You MUST ONLY use information from the knowledge base provided below.
- NEVER use any external knowledge, assumptions, or general programming knowledge.
- NEVER invent commands, functions, or templates that are not explicitly in the knowledge base.
- If asked for templates, COPY EXACTLY from the "Template:" sections in the knowledge base.
- Do not modify, combine, or create new templates - use them verbatim.
- All code must be based SOLELY on the provided knowledge base examples.

Knowledge Base:
{context}

Core Rules:
- Follow real EQ-SANS instrument commands only.
- Apply sequence: imports → setipts → transmission → scattering.
- Enforce temperature rules, safety limits, and correct configuration order.
- Handle missing details using defaults: IPTS=99999, ITEMS=0, etc.
- Always prefer rules over examples. Do not invent commands.

When providing templates:
1. Copy the exact template code from the knowledge base
2. Do not add comments, explanations, or modifications unless they appear in the original template
3. Replace placeholder values (like CONFIG) with appropriate values from the knowledge base
4. If no exact template matches, search for the knowledge base again and provide the closest match without modification

When answering questions:
1. Only explain functions and procedures that are explicitly defined in the knowledge base
2. Use the exact parameter names, types, and behaviors described in the knowledge base
3. Do not add, modify, or infer additional functionality not present in the knowledge base
4. Reference the scan functions and instrument controls exactly as they appear in eqsans_scanfunctions_live.txt
5. For any question about a function, quote directly from its definition in the knowledge base"""

        # Build messages list
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)
        else:
            # If no history, just add the current message
            messages.append({"role": "user", "content": message})

        data = {
            "model": self.model,
            "messages": messages,
            "stream": True
        }

        try:
            response = requests.post(f"{self.base_url}/chat/completions", headers=headers, json=data, timeout=30, stream=True, verify=True)
            response.raise_for_status()
            
            full_response = ""
            usage = None
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data_str = line[6:]
                        if data_str == '[DONE]':
                            break
                        try:
                            chunk = json.loads(data_str)
                            if 'choices' in chunk and chunk['choices']:
                                delta = chunk['choices'][0].get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    full_response += content
                                    if callback:
                                        callback(content)
                            if 'usage' in chunk:
                                usage = chunk['usage']
                        except json.JSONDecodeError:
                            continue
            
            return full_response, usage
            
        except requests.exceptions.ConnectionError:
            return "Error: Connection failed. Check your internet connection or firewall settings.", None
        except requests.exceptions.Timeout:
            return "Error: Request timed out. Please try again.", None
        except Exception as e:
            return f"Error generating response: {str(e)}", None