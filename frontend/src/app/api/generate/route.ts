import path from 'path';
import { NextRequest } from 'next/server';
import * as grpc from '@grpc/grpc-js';
import * as protoLoader from '@grpc/proto-loader';

// Find proto file in project root, not frontend
const PROTO_PATH = path.resolve(process.cwd(), '../generate.proto');

const packageDefinition = protoLoader.loadSync(PROTO_PATH, {
  keepCase: true,
  longs: String,
  enums: String,
  defaults: true,
  oneofs: true,
});

const protoDescriptor = grpc.loadPackageDefinition(packageDefinition) as any;
const storyGenerator = protoDescriptor.urdu_story.StoryGenerator;

const client = new storyGenerator(
  'localhost:50051',
  grpc.credentials.createInsecure()
);

export async function POST(request: NextRequest) {
  const { prefix, maxLength = 500 } = await request.json();

  const responseStream = new ReadableStream({
    start(controller) {
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

      call.on('end', () => {
        controller.close();
      });

      call.on('error', (error: any) => {
        console.error('gRPC error:', error);
        controller.error(error);
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