const Redis = require("ioredis");

let redis;
try {
  redis = new Redis(process.env.REDIS_URL, {
    maxRetriesPerRequest: null,
    enableReadyCheck: false
  });
  redis.on('error', (err) => console.log('Redis error', err));
} catch (e) {
  console.log('Redis connect failed:', e);
}
