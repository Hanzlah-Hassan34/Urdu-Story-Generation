import { NextRequest } from 'next/server';

export async function POST(request: NextRequest) {
  const { prefix, maxLength = 500 } = await request.json();
  let base = process.env.GRPC_BACKEND_URL || 'http://localhost:50051';
  base = base.replace(/\/$/, '');
  if (!base.startsWith('http')) base = `https://${base}`;

  const res = await fetch(`${base}/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prefix: prefix || '', maxLength }),
  });

  if (!res.ok || !res.body) {
    throw new Error(`Backend error: ${res.status}`);
  }

  return new Response(res.body, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
    },
  });
}
