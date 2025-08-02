
import express from 'express';
import { Orchestrator } from './orchestrator.ts';

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

app.post('/configure_architecture', (req, res) => {
  const { architectureType, workerCount } = req.body;
  if (!architectureType || !workerCount) {
    return res.status(400).send('architectureType and workerCount are required');
  }
  try {
    orchestrator.reconfigureAgents(architectureType, workerCount);
    res.json({ message: 'Agent architecture reconfigured successfully' });
  } catch (error) {
    console.error('Error reconfiguring agents:', error);
    res.status(500).json({ error: 'Internal Server Error' });
  }
});

app.listen(port, () => {
  console.log(`Ollama Flow server listening at http://localhost:${port}`);
});
