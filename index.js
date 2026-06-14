const express = require('express');
const Redis = require('ioredis');

const app = express();
app.use(express.json());

// ใช้ PORT จาก Railway หรือ default 3000
const PORT = process.env.PORT || 3000;

// เชื่อมต่อ Redis
const redis = new Redis(process.env.REDIS_URL || 'redis://localhost:6379');

redis.on('connect', () => {
  console.log('✅ Redis connected');
});

redis.on('error', (err) => {
  console.log('❌ Redis error:', err.message);
});

// Health check
app.get('/', (req, res) => {
  res.json({ status: 'ok', redis: redis.status });
});

// Webhook endpoint
app.post('/webhook', async (req, res) => {
  try {
    const { message } = req.body;
    await redis.set('last_message', JSON.stringify(message));
    res.json({ status: 'success', message });
  } catch (err) {
    console.error('Webhook error:', err);
    res.status(500).json({ status: 'error', message: err.message });
  }
});

app.listen(PORT, () => {
  console.log(`🚀 Server running on port ${PORT}
  `);
});
