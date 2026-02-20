import path from 'path';
import { NextRequest } from 'next/server';
import * as grpc from '@grpc/grpc-js';
import * as protoLoader from '@grpc/proto-loader';

// Proto: use local copy for Vercel, fallback to parent for local dev
const PROTO_PATH = path.resolve(process.cwd(), 'generate.proto');

const packageDefinition = protoLoader.loadSync(PROTO_PATH, {
  keepCase: true,
  longs: String,
  enums: String,
  defaults: true,
  oneofs: true,
});

const protoDescriptor = grpc.loadPackageDefinition(packageDefinition) as any;
const storyGenerator = protoDescriptor.urdu_story.StoryGenerator;

function getGrpcClient() {
  let url = process.env.GRPC_BACKEND_URL || 'localhost:50051';
  url = url.replace(/^https?:\/\//, '').trim(); // strip https:// or http://
  const isSecure = !url.includes('localhost') && !url.includes('127.0.0.1');
  const creds = isSecure ? grpc.credentials.createSsl() : grpc.credentials.createInsecure();
  const host = url.includes(':') ? url : `${url}:443`;
  return new storyGenerator(host, creds);
}

export async function POST(request: NextRequest) {
  const { prefix, maxLength = 500 } = await request.json();
  const client = getGrpcClient();

  const responseStream = new ReadableStream({
    start(controller) {
      let closed = false;
      const safeClose = () => {
        if (!closed) {
          closed = true;
          try {
            controller.close();
          } catch (_) {}
        }
      };
      const safeError = (err: unknown) => {
        if (!closed) {
          closed = true;
          try {
            controller.error(err);
          } catch (_) {}
        }
      };

      const call = client.Generate({
        prefix: prefix || '',
        max_length: maxLength,
      });

      call.on('data', (response: any) => {
        const data = `data: ${JSON.stringify({
          chunk: response.chunk,
          isFinal: response.is_final,
          numTokens: response.num_tokens,
        })}\n\n`;
        controller.enqueue(new TextEncoder().encode(data));
      });

      call.on('end', () => safeClose());
      call.on('error', (error: any) => {
        console.error('gRPC error:', error);
        safeError(error);
      });
    },
  });

  return new Response(responseStream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
    },
  });
}