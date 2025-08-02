
import ollama from 'ollama';
import { Agent, AgentMessage } from './agent.ts';

export class OllamaAgent implements Agent {
  id: string;
  name: string;
  private model: string;

  constructor(id: string, name: string, model: string = 'llama3') {
    this.id = id;
    this.name = name;
    this.model = model;
  }

  async receiveMessage(message: AgentMessage): Promise<void> {
    console.log(`Agent ${this.name} (${this.id}) received message from ${message.senderId}: ${message.content}`);
    // Assuming the content of the message is the prompt for the Ollama model
    try {
      const result = await this.performTask(message.content);
      console.log(`Agent ${this.name} (${this.id}) completed task with result: ${result}`);
      // In a real multi-agent system, the agent would then send a response back
      // to the sender or another agent via the orchestrator.
      // For now, we just log the result.
    } catch (error) {
      console.error(`Agent ${this.name} (${this.id}) failed to perform task:`, error);
    }
  }

  private async performTask(prompt: string): Promise<string> {
    try {
      const response = await ollama.chat({
        model: this.model,
        messages: [{ role: 'user', content: prompt }],
      });
      return response.message.content;
    } catch (error) {
      console.error('Error performing task:', error);
      throw error;
    }
  }
}
