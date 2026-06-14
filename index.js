const express = require('express');
const Redis = require('ioredis');
const app = express();

app.use(express.json());

// เชื่อมต่อ Redis ผ่านตัวแปรสภาพแวดล้อมที่ Railway เตรียมให้
const redis = new Redis(process.env.REDIS_URL);

app.post('/payment', async (req, res) => {
  const { idempotency_key, amount } = req.body;
  
  if (!idempotency_key) {
    return res.status(400).json({ status: 'error', message: 'idempotency_key required' });
  }

  // ตรวจสอบว่าเคยมี key นี้หรือยัง
  const exists = await redis.get(idempotency_key);
  if (exists) {
    return res.json({ status: 'duplicate', data: JSON.parse(exists) });
  }

  // ถ้ายังไม่มี ให้สร้างข้อมูลใหม่
  const result = { 
    amount, 
    tx_id: Date.now(), 
    status: 'paid' 
  };
  
  // บันทึกลง Redis พร้อมกำหนดอายุ 24 ชั่วโมง (86400 วินาที)
  await redis.set(idempotency_key, JSON.stringify(result), 'EX', 86400);
  
  res.json({ status: 'success', data: result });
});

const PORT = process.env.PORT || 8080;
app.listen(PORT, () => {
  console.log(`Server running on ${PORT}`)
    ;
});
