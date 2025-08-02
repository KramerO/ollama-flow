
import express from 'express';
import { Orchestrator } from './orchestrator';

const app = express();
const port = 3000;
const orchestrator = new Orchestrator();

app.use(express.json());

app.post('/run', async (req, res) => {
  const { prompt } = req.body;
  if (!prompt) {
    return res.status(400).send('Prompt is required');
  }
  try {
    const result = await orchestrator.run(prompt);
    res.json({ result });
  } catch (error) {
    console.error('Error processing request:', error);
    res.status(500).json({ error: 'Internal Server Error' });
  }
});

app.listen(port, () => {
  console.log(`Ollama Flow server listening at http://localhost:${port}`);
});
