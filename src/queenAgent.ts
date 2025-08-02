import { BaseAgent, type AgentMessage, type ArchitectureType } from './agent.ts';
import { OllamaAgent } from './worker.ts'; // Import OllamaAgent to use its type
import { SubQueenAgent } from './subQueenAgent.ts';
import ollama from 'ollama'; // Import ollama

export class QueenAgent extends BaseAgent {
  private subQueenAgents: SubQueenAgent[] = [];
  private ollamaAgents: OllamaAgent[] = []; // Added for CENTRALIZED/FULLY_CONNECTED
  private currentSubQueenIndex: number = 0;
  private currentOllamaAgentIndex: number = 0; // Added for CENTRALIZED/FULLY_CONNECTED
  private architectureType: ArchitectureType;
  private model: string; // Ollama model for decomposition

  constructor(id: string, name: string, architectureType: ArchitectureType, model: string = 'llama3') {
    super(id, name);
    this.architectureType = architectureType;
    this.model = model;
  }

  // This method will be called by the Orchestrator after all agents are registered
  // and the orchestrator reference is set.
  initializeAgents(): void {
    if (this.orchestrator) {
      if (this.architectureType === 'HIERARCHICAL') {
        this.subQueenAgents = this.orchestrator.getAgentsByType(SubQueenAgent);
        console.log(`QueenAgent ${this.name} found ${this.subQueenAgents.length} SubQueenAgents.`);
      } else if (this.architectureType === 'CENTRALIZED' || this.architectureType === 'FULLY_CONNECTED') {
        this.ollamaAgents = this.orchestrator.getAgentsByType(OllamaAgent);
        console.log(`QueenAgent ${this.name} found ${this.ollamaAgents.length} OllamaAgents.`);
      }
    }
  }

  private async decomposeTask(task: string): Promise<string[]> {
    const decompositionPrompt = `Given the main task: '${task}'. Decompose this into a list of smaller, actionable subtasks. Respond only with a JSON array of strings, where each string is a subtask. Example: ['Subtask 1', 'Subtask 2']`;
    try {
      const response = await ollama.chat({
        model: this.model,
        messages: [{ role: 'user', content: decompositionPrompt }],
      });
      const rawResponse = response.message.content;
      console.log(`[QueenAgent] Decomposition LLM Raw Response: ${rawResponse}`);
      // Attempt to parse JSON, fallback to single task if parsing fails
      try {
        const subtasks = JSON.parse(rawResponse);
        if (Array.isArray(subtasks) && subtasks.every(item => typeof item === 'string')) {
          return subtasks;
        } else {
          console.warn(`[QueenAgent] LLM response is not a valid JSON array of strings. Falling back to single task.`);
          return [task];
        }
      } catch (jsonError) {
        console.error(`[QueenAgent] JSON parsing failed: ${jsonError}. Falling back to single task.`);
        return [task];
      }
    } catch (error) {
      console.error(`[QueenAgent] Error during task decomposition: ${error instanceof Error ? error.message : String(error)}. Falling back to single task.`);
      return [task];
    }
  }

  async receiveMessage(message: AgentMessage): Promise<void> {
    console.log(`QueenAgent ${this.name} (${this.id}) received message from ${message.senderId}: ${message.content}`);

    if (message.type === 'task') {
      const subtasks = await this.decomposeTask(message.content);
      console.log(`[QueenAgent] Decomposed into subtasks: ${JSON.stringify(subtasks)}`);

      for (const subtask of subtasks) {
        if (this.architectureType === 'HIERARCHICAL') {
          if (this.subQueenAgents.length === 0) {
            console.warn('No SubQueenAgents available to delegate tasks.');
            // Send error back to orchestrator if no sub-queens
            await this.sendMessage('orchestrator', 'final-error', 'No SubQueenAgents available.');
            return;
          }

          // Select a SubQueenAgent in a round-robin fashion
          const targetSubQueen = this.subQueenAgents[this.currentSubQueenIndex];
          this.currentSubQueenIndex = (this.currentSubQueenIndex + 1) % this.subQueenAgents.length;

          if (!targetSubQueen) {
            console.error('No valid SubQueenAgent found for delegation.');
            await this.sendMessage('orchestrator', 'final-error', 'No valid SubQueenAgent found.');
            return;
          }

          const delegatedTask = `Delegated task from Main Queen to ${targetSubQueen.name}: ${subtask}`;
          console.log(`QueenAgent delegating task to ${targetSubQueen.name} (${targetSubQueen.id})`);
          await this.sendMessage(targetSubQueen.id, 'sub-task-to-subqueen', delegatedTask, message.requestId);
        } else if (this.architectureType === 'CENTRALIZED' || this.architectureType === 'FULLY_CONNECTED') {
          if (this.ollamaAgents.length === 0) {
            console.warn('No OllamaAgents available to delegate tasks.');
            // Send error back to orchestrator if no ollama agents
            await this.sendMessage('orchestrator', 'final-error', 'No OllamaAgents available.', message.requestId);
            return;
          }

          // Select an OllamaAgent in a round-robin fashion
          const targetOllamaAgent = this.ollamaAgents[this.currentOllamaAgentIndex];
          this.currentOllamaAgentIndex = (this.currentOllamaAgentIndex + 1) % this.ollamaAgents.length;

          if (!targetOllamaAgent) {
            console.error('No valid OllamaAgent found for delegation.');
            await this.sendMessage('orchestrator', 'final-error', 'No valid OllamaAgent found.', message.requestId);
            return;
          }

          const delegatedTask = `Delegated task from Queen to ${targetOllamaAgent.name}: ${subtask}`;
          console.log(`QueenAgent delegating task to ${targetOllamaAgent.name} (${targetOllamaAgent.id})`);
          await this.sendMessage(targetOllamaAgent.id, 'sub-task', delegatedTask, message.requestId);
        }
      }
    } else if (message.type === 'group-response') {
      console.log(`QueenAgent received group response from ${message.senderId}: ${JSON.stringify(message.content)}`);
      // Process the response from the SubQueenAgent
      // For now, just forward it as a final response to the orchestrator
      await this.sendMessage('orchestrator', 'final-response', `Aggregated response from ${message.content.fromSubQueen}: ${message.content.content}`, message.requestId);
    } else if (message.type === 'response') {
      // This is a direct response from an OllamaAgent in CENTRALIZED or FULLY_CONNECTED
      console.log(`QueenAgent received direct response from ${message.senderId}: ${message.content}`);
      await this.sendMessage('orchestrator', 'final-response', `Response from ${message.senderId}: ${message.content}`, message.requestId);
    } else if (message.type === 'error') {
      console.error(`QueenAgent received error from ${message.senderId}: ${message.content}`);
      await this.sendMessage('orchestrator', 'final-error', `Error from ${message.senderId}: ${message.content}`, message.requestId);
    }
  }
}
