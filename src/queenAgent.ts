import { AgentMessage, BaseAgent } from './agent.ts';

export class QueenAgent extends BaseAgent {
  constructor(id: string, name: string) {
    super(id, name);
  }

  async receiveMessage(message: AgentMessage): Promise<void> {
    console.log(`QueenAgent ${this.name} (${this.id}) received message from ${message.senderId}: ${message.content}`);

    // Example: QueenAgent processes a task and delegates it to another agent
    if (message.type === 'task') {
      const delegatedTask = `Delegated task from Queen: ${message.content}`;
      // For now, hardcode sending to a specific OllamaAgent for demonstration
      await this.sendMessage('ollama-agent-1', 'sub-task', delegatedTask);
    } else if (message.type === 'response') {
      console.log(`QueenAgent received response from ${message.senderId}: ${message.content}`);
      // In a real scenario, the Queen might aggregate responses or send them back to the original requester
    }
  }
}
