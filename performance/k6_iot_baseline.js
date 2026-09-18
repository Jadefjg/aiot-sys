import http from 'k6/http';
import { check, sleep } from 'k6';

const base = __ENV.BASE_URL || 'http://localhost:8000';
const vus = Number(__ENV.VUS || 10);
const token = __ENV.TOKEN || '';
const devicePrefix = __ENV.DEVICE_PREFIX || 'perf-local';
export const options = {
  vus,
  duration: __ENV.DURATION || '30s',
  thresholds: { http_req_failed: ['rate<0.01'], http_req_duration: ['p(95)<500'] },
};

export default function () {
  const health = http.get(`${base}/health`);
  check(health, { 'health 2xx': (r) => r.status >= 200 && r.status < 300 });
  const deviceId = `${devicePrefix}-${String((__VU - 1) % Number(__ENV.DEVICE_COUNT || 100)).padStart(6, '0')}`;
  const body = JSON.stringify({ device_id: deviceId, ts: Date.now(), msg_type: 'telemetry', payload: { temperature: 25.6 } });
  const res = http.post(`${base}/api/v1/devices/${deviceId}/data`, body, { headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) } });
  check(res, { 'telemetry endpoint reachable': (r) => r.status < 500 });
  sleep(1);
}
