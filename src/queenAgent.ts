import { AgentMessage, BaseAgent } from './agent.ts';
import { OllamaAgent } from './worker.ts'; // Import OllamaAgent to use its type

export class QueenAgent extends BaseAgent {
  private ollamaAgents: OllamaAgent[] = [];
  private currentAgentIndex: number = 0;

  constructor(id: string, name: string) {
    super(id, name);
  }

  // This method will be called by the Orchestrator after all agents are registered
  // and the orchestrator reference is set.
  initializeAgents(): void {
    if (this.orchestrator) {
      this.ollamaAgents = this.orchestrator.getAgentsByType(OllamaAgent);
      console.log(`QueenAgent ${this.name} found ${this.ollamaAgents.length} OllamaAgents.`);
    }
  }

  async receiveMessage(message: AgentMessage): Promise<void> {
    console.log(`QueenAgent ${this.name} (${this.id}) received message from ${message.senderId}: ${message.content}`);

    if (message.type === 'task') {
      if (this.ollamaAgents.length === 0) {
        console.warn('No OllamaAgents available to delegate tasks.');
        return;
      }

      // Select an OllamaAgent in a round-robin fashion
      const targetAgent = this.ollamaAgents[this.currentAgentIndex];
      this.currentAgentIndex = (this.currentAgentIndex + 1) % this.ollamaAgents.length;

      const delegatedTask = `Delegated task from Queen to ${targetAgent.name}: ${message.content}`;
      console.log(`QueenAgent delegating task to ${targetAgent.name} (${targetAgent.id})`);
      await this.sendMessage(targetAgent.id, 'sub-task', delegatedTask);

    } else if (message.type === 'response') {
      console.log(`QueenAgent received response from ${message.senderId}: ${message.content}`);
      // In a fully connected architecture, the Queen might just log the response
      // or forward it to the original sender (e.g., the orchestrator or another agent).
      // For now, we'll just log it.
      await this.sendMessage('orchestrator', 'final-response', `Response from ${message.senderId}: ${message.content}`);
    } else if (message.type === 'error') {
      console.error(`QueenAgent received error from ${message.senderId}: ${message.content}`);
      await this.sendMessage('orchestrator', 'final-error', `Error from ${message.senderId}: ${message.content}`);
    }
  }
}
