
import { Worker } from './worker.ts';

export class Orchestrator {
  private worker: Worker;

  constructor() {
    this.worker = new Worker();
  }

  async run(prompt: string): Promise<string> {
    console.log('Orchestrator running with prompt:', prompt);
    const result = await this.worker.performTask(prompt);
    console.log('Orchestrator finished with result:', result);
    return result;
  }
}
