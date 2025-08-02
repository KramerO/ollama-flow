import { AgentMessage, BaseAgent } from './agent.ts';
import { OllamaAgent } from './worker.ts';

export class SubQueenAgent extends BaseAgent {
  private groupOllamaAgents: OllamaAgent[] = [];
  private currentAgentIndex: number = 0;

  constructor(id: string, name: string) {
    super(id, name);
  }

  initializeGroupAgents(agents: OllamaAgent[]): void {
    this.groupOllamaAgents = agents;
    console.log(`SubQueenAgent ${this.name} initialized with ${this.groupOllamaAgents.length} OllamaAgents.`);
  }

  async receiveMessage(message: AgentMessage): Promise<void> {
    console.log(`SubQueenAgent ${this.name} (${this.id}) received message from ${message.senderId}: ${message.content}`);

    if (message.type === 'task') {
      if (this.groupOllamaAgents.length === 0) {
        console.warn(`SubQueenAgent ${this.name}: No OllamaAgents in group to delegate tasks.`);
        // Optionally, send an error back to the sender (Main Queen)
        await this.sendMessage(message.senderId, 'error', `No OllamaAgents in group for ${this.name}`);
        return;
      }

      // Delegate task to an OllamaAgent in the group (round-robin)
      const targetAgent = this.groupOllamaAgents[this.currentAgentIndex];
      this.currentAgentIndex = (this.currentAgentIndex + 1) % this.groupOllamaAgents.length;

      const delegatedTask = `Delegated by ${this.name} to ${targetAgent.name}: ${message.content}`;
      console.log(`SubQueenAgent ${this.name} delegating task to ${targetAgent.name} (${targetAgent.id})`);
      await this.sendMessage(targetAgent.id, 'sub-task', delegatedTask);

    } else if (message.type === 'response' || message.type === 'error') {
      console.log(`SubQueenAgent ${this.name} received ${message.type} from ${message.senderId}: ${message.content}`);
      // Aggregate or process response from group agent
      // For now, just forward it to the Main Queen
      await this.sendMessage('queen-agent-1', 'group-response', {
        fromSubQueen: this.id,
        originalSender: message.senderId,
        type: message.type,
        content: message.content,
      });
    }
  }
}
