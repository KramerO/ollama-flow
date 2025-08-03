import ollama from 'ollama';
export class Worker {
    model;
    constructor(model = 'llama3') {
        this.model = model;
    }
    async performTask(prompt) {
        try {
            const response = await ollama.chat({
                model: this.model,
                messages: [{ role: 'user', content: prompt }],
            });
            return response.message.content;
        }
        catch (error) {
            console.error('Error performing task:', error);
            throw error;
        }
    }
}
//# sourceMappingURL=worker.js.map