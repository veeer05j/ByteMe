const GROQ_URL = 'https://api.groq.com/openai/v1/chat/completions';
const MODEL = 'openai/gpt-oss-20b';

const SYSTEM_PROMPT = [
  'You are the Vitea Flow health coach for people living in Mauritius.',
  'Answer in plain text only. No markdown, no bullet symbols, no headings.',
  'Keep every reply under 120 words and give at most three concrete steps.',
  'Never diagnose, never name prescription medicines, never give dosages.',
  'Use Mauritian food and everyday ingredients when talking about meals.',
  'For anything urgent or medical, tell the person to contact the nearest hospital or dial 114.',
  'Stay on food, sleep, movement, stress and daily habits. Politely decline anything else.'
].join(' ');

module.exports = async function handler(req, res) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).json({ error: 'Method not allowed', reply: '' });
  }

  const key = process.env.GROQ_API_KEY;
  if (!key) {
    return res.status(500).json({ error: 'GROQ_API_KEY is not set', reply: '' });
  }

  let messages = [];
  try {
    const body = typeof req.body === 'string' ? JSON.parse(req.body) : req.body;
    messages = Array.isArray(body && body.messages) ? body.messages : [];
  } catch (e) {
    return res.status(400).json({ error: 'Invalid JSON body', reply: '' });
  }

  const cleaned = messages
    .filter(function (m) {
      return m && (m.role === 'user' || m.role === 'assistant') && typeof m.content === 'string' && m.content.trim();
    })
    .slice(-10)
    .map(function (m) {
      return { role: m.role, content: m.content.slice(0, 2000) };
    });

  if (!cleaned.length) {
    return res.status(400).json({ error: 'No messages supplied', reply: '' });
  }

  try {
    const upstream = await fetch(GROQ_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: 'Bearer ' + key
      },
      body: JSON.stringify({
        model: MODEL,
        messages: [{ role: 'system', content: SYSTEM_PROMPT }].concat(cleaned),
        temperature: 0.6,
        max_tokens: 500
      })
    });

    const data = await upstream.json();

    if (!upstream.ok) {
      const reason = (data && data.error && data.error.message) || 'Groq request failed';
      return res.status(upstream.status).json({ error: reason, reply: '' });
    }

    const reply =
      data &&
      data.choices &&
      data.choices[0] &&
      data.choices[0].message &&
      data.choices[0].message.content;

    if (!reply) {
      return res.status(502).json({ error: 'Empty response from Groq', reply: '' });
    }

    return res.status(200).json({ reply: reply.trim() });
  } catch (err) {
    return res.status(502).json({ error: (err && err.message) || 'Upstream error', reply: '' });
  }
};