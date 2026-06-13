const express = require('express')
const Redis = require('ioredis')
const app = express()
app.use(express.json())

const redis = new Redis(process.env.REDIS_URL)

app.post('/payment', async (req, res) => {
  const { idempotency_key, amount } = req.body
  
  if (!idempotency_key) {
    return res.status(400).json({ status: 'error', message: 'idempotency_key required' })
  }

  const exists = await redis.get(idempotency_key)
  if (exists) {
    return res.json({ status: 'duplicate', data: JSON.parse(exists) })
  }

  const result = { 
    amount, 
    tx_id: Date.now(), 
    status: 'paid' 
  }
  
  await redis.set(idempotency_key, JSON.stringify(result), 'EX', 86400)
  res.json({ status: 'success', data: result })
})

const PORT = 8080
app.listen(PORT, () => {
  console.log(`Server running on ${PORT}`)
})
