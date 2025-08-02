import { BaseAgent, type AgentMessage } from './agent.ts';
import { OllamaAgent } from './worker.ts';
import ollama from 'ollama'; // Import ollama

export class SubQueenAgent extends BaseAgent {
  private groupOllamaAgents: OllamaAgent[] = [];
  private currentAgentIndex: number = 0;
  private model: string; // Ollama model for decomposition

  constructor(id: string, name: string, model: string = 'llama3') {
    super(id, name);
    this.model = model;
  }

  initializeGroupAgents(agents: OllamaAgent[]): void {
    this.groupOllamaAgents = agents;
    console.log(`SubQueenAgent ${this.name} initialized with ${this.groupOllamaAgents.length} OllamaAgents.`);
  }

  private async decomposeTask(task: string): Promise<string[]> {
    const decompositionPrompt = `Given the sub-task: '${task}'. Decompose this into a list of smaller, actionable subtasks for an OllamaAgent. Respond only with a JSON array of strings, where each string is a subtask. Example: ['Subtask 1', 'Subtask 2']`;
    try {
      const response = await ollama.chat({
        model: this.model,
        messages: [{ role: 'user', content: decompositionPrompt }],
      });
      const rawResponse = response.message.content;
      console.log(`[SubQueenAgent] Decomposition LLM Raw Response: ${rawResponse}`);
      // Attempt to parse JSON, fallback to single task if parsing fails
      try {
        const subtasks = JSON.parse(rawResponse);
        if (Array.isArray(subtasks) && subtasks.every(item => typeof item === 'string')) {
          return subtasks;
        } else {
          console.warn(`[SubQueenAgent] LLM response is not a valid JSON array of strings. Falling back to single task.`);
          return [task];
        }
      } catch (jsonError) {
        console.error(`[SubQueenAgent] JSON parsing failed: ${jsonError}. Falling back to single task.`);
        return [task];
      }
    } catch (error) {
      console.error(`[SubQueenAgent] Error during task decomposition: ${error instanceof Error ? error.message : String(error)}. Falling back to single task.`);
      return [task];
    }
  }

  async receiveMessage(message: AgentMessage): Promise<void> {
    console.log(`SubQueenAgent ${this.name} (${this.id}) received message from ${message.senderId}: ${message.content}`);

    if (message.type === 'sub-task-to-subqueen') {
      const subtasks = await this.decomposeTask(message.content);
      console.log(`[SubQueenAgent] Decomposed into subtasks: ${JSON.stringify(subtasks)}`);

      for (const subtask of subtasks) {
        if (this.groupOllamaAgents.length === 0) {
          console.warn(`SubQueenAgent ${this.name}: No OllamaAgents in group to delegate tasks.`);
          await this.sendMessage(message.senderId, 'error', `No OllamaAgents in group for ${this.name}`);
          return;
        }

        // Delegate task to an OllamaAgent in the group (round-robin)
        const targetAgent = this.groupOllamaAgents[this.currentAgentIndex];
        this.currentAgentIndex = (this.currentAgentIndex + 1) % this.groupOllamaAgents.length;

        if (!targetAgent) {
          console.error('No valid OllamaAgent found in group for delegation.');
          await this.sendMessage(message.senderId, 'error', 'No valid OllamaAgent found in group.');
          return;
        }

        const delegatedTask = `Delegated by ${this.name} to ${targetAgent.name}: ${subtask}`;
        console.log(`SubQueenAgent ${this.name} delegating task to ${targetAgent.name} (${targetAgent.id})`);
        await this.sendMessage(targetAgent.id, 'sub-task', delegatedTask);
      }
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
