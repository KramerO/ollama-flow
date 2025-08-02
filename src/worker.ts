
import ollama from 'ollama';
import { AgentMessage, BaseAgent } from './agent.ts';

export class OllamaAgent extends BaseAgent {
  private model: string;

  constructor(id: string, name: string, model: string = 'llama3') {
    super(id, name);
    this.model = model;
  }

  async receiveMessage(message: AgentMessage): Promise<void> {
    console.log(`Agent ${this.name} (${this.id}) received message from ${message.senderId}: ${message.content}`);
    // Assuming the content of the message is the prompt for the Ollama model
    try {
      const result = await this.performTask(message.content);
      console.log(`Agent ${this.name} (${this.id}) completed task with result: ${result}`);
      // Example of sending a response back to the sender
      await this.sendMessage(message.senderId, 'response', result);
    } catch (error) {
      console.error(`Agent ${this.name} (${this.id}) failed to perform task:`, error);
      await this.sendMessage(message.senderId, 'error', `Failed to perform task: ${error.message}`);
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
