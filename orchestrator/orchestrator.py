from typing import Dict, Any, Type, List, Optional
from agents.base_agent import BaseAgent, AgentMessage
import asyncio
import uuid
import ollama
import re
from db_manager import MessageDBManager # Import the new DB Manager

class Orchestrator:
    def __init__(self, db_manager: MessageDBManager, model: str = "codellama:7b"):
        self.agents: Dict[str, BaseAgent] = {}
        self.response_resolvers: Dict[str, asyncio.Future] = {}
        self.request_counter = 0
        self.db_manager = db_manager
        self.polling_task = None
        self.model = model

    def start_polling(self):
        if self.polling_task is None:
            self.polling_task = asyncio.create_task(self._orchestrator_polling_task())

    def register_agent(self, agent: BaseAgent):
        if agent.agent_id in self.agents:
            print(f"Warning: Agent with ID {agent.agent_id} already registered. Overwriting.")
        self.agents[agent.agent_id] = agent
        agent.set_orchestrator(self) # Still needed for final response handling
        agent.set_db_manager(self.db_manager)
        print(f"Agent {agent.name} ({agent.agent_id}) registered.")

    async def _orchestrator_polling_task(self):
        while True:
            try:
                messages = self.db_manager.get_pending_messages("orchestrator")
                for msg_data in messages:
                    message = AgentMessage(
                        sender_id=msg_data['sender_id'],
                        receiver_id=msg_data['receiver_id'],
                        message_type=msg_data['type'],
                        content=msg_data['content'],
                        request_id=msg_data['request_id'],
                        message_id=msg_data['id']
                    )
                    print(f"[Orchestrator.polling] Received message. Sender: {message.sender_id}, Type: {message.message_type}, RequestId: {message.request_id}")

                    request_id = message.request_id if message.request_id else message.sender_id
                    if message.message_type == "final-response":
                        if request_id in self.response_resolvers:
                            self.response_resolvers[request_id].set_result(message.content)
                            del self.response_resolvers[request_id]
                        else:
                            print(f"Warning: No resolver found for request_id {request_id}.")
                    elif message.message_type == "final-error":
                        if request_id in self.response_resolvers:
                            self.response_resolvers[request_id].set_exception(Exception(message.content))
                            del self.response_resolvers[request_id]
                        else:
                            print(f"Warning: No resolver found for request_id {request_id}.")
                    
                    self.db_manager.mark_message_as_processed(message.message_id)
            except Exception as e:
                print(f"Error in orchestrator polling task: {e}")
            await asyncio.sleep(0.1) # Poll every 100ms

    def get_agents_by_type(self, agent_type: Type[BaseAgent]) -> List[BaseAgent]:
        return [agent for agent in self.agents.values() if isinstance(agent, agent_type)]
    
    def _detect_german_language(self, text: str) -> bool:
        """Detect if text is in German language"""
        german_keywords = [
            'erstelle', 'erstellen', 'speichere', 'speichern', 'datei', 'ordner',
            'programmiere', 'entwickle', 'baue', 'schreibe', 'generiere',
            'implementiere', 'mache', 'führe', 'aus', 'benutze', 'verwende',
            'installiere', 'lade', 'herunter', 'öffne', 'schließe', 'starte',
            'beende', 'lösche', 'entferne', 'kopiere', 'verschiebe', 'umbenennen',
            'und', 'oder', 'aber', 'wenn', 'dann', 'sonst', 'für', 'mit', 'ohne',
            'eine', 'ein', 'der', 'die', 'das', 'den', 'dem', 'des'
        ]
        
        text_lower = text.lower()
        german_word_count = sum(1 for keyword in german_keywords if keyword in text_lower)
        
        # If more than 2 German words found, likely German
        return german_word_count >= 2
    
    async def _translate_german_to_english(self, german_text: str) -> str:
        """Translate German text to English using LLM"""
        try:
            translation_prompt = f"""
Translate the following German text to English. Keep the technical meaning exact and preserve any file names or technical terms.

German text: {german_text}

Provide only the English translation, no additional explanation:
"""
            
            response = ollama.chat(
                model=self.model,
                messages=[{"role": "user", "content": translation_prompt}]
            )
            
            english_text = response["message"]["content"].strip()
            
            # Clean up common translation artifacts
            english_text = re.sub(r'^(English translation:|Translation:|Here is the translation:)\s*', '', english_text, flags=re.IGNORECASE)
            english_text = english_text.strip('"\'')
            
            print(f"[Orchestrator] Translated: '{german_text}' -> '{english_text}'")
            return english_text
            
        except Exception as e:
            print(f"[Orchestrator] Translation failed: {e}")
            return german_text  # Fallback to original text

    async def run(self, prompt: str) -> str:
        print(f"Orchestrator received prompt: {prompt}")
        
        # Check if prompt is in German and translate if needed
        processed_prompt = prompt
        if self._detect_german_language(prompt):
            print(f"[Orchestrator] German language detected, translating...")
            processed_prompt = await self._translate_german_to_english(prompt)
        
        # For now, directly send to a QueenAgent (assuming one exists)
        queen_agents = self.get_agents_by_type(BaseAgent) # Placeholder, will be QueenAgent
        if not queen_agents:
            return "Error: No QueenAgent registered."
        
        target_receiver_id = queen_agents[0].agent_id # Assuming the first registered agent is the Queen

        request_id = f"request-{self.request_counter}"
        self.request_counter += 1

        # Insert initial message into DB with processed (possibly translated) prompt
        self.db_manager.insert_message("orchestrator", target_receiver_id, "task", processed_prompt, request_id)
        print(f"Orchestrator inserted initial task for {target_receiver_id} (Request ID: {request_id})")

        future = asyncio.Future()
        self.response_resolvers[request_id] = future

        return await future
