import { Worker } from './worker';
export class Orchestrator {
    worker;
    constructor() {
        this.worker = new Worker();
    }
    async run(prompt) {
        console.log('Orchestrator running with prompt:', prompt);
        const result = await this.worker.performTask(prompt);
        console.log('Orchestrator finished with result:', result);
        return result;
    }
}
//# sourceMappingURL=orchestrator.js.map