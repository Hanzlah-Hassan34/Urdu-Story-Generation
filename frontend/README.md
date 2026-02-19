# Urdu Story Generator Frontend

A React/Next.js frontend for the Urdu story generation service.

## Features

- Input starting phrase in Urdu
- Real-time streaming story generation (like ChatGPT)
- Clean, responsive UI with RTL support for Urdu text

## Setup

1. Ensure the gRPC server is running on `localhost:50051`
2. Install dependencies: `npm install`
3. Start development server: `npm run dev`
4. Open http://localhost:3000

## How it works

- The frontend sends a POST request to `/api/generate` with the prefix
- The API route connects to the gRPC server and streams responses
- Server-Sent Events (SSE) are used to stream the story chunks to the browser
- The story updates in real-time as tokens are generated

## Technologies

- Next.js 15 (App Router)
- TypeScript
- Tailwind CSS
- gRPC (via @grpc/grpc-js)
- Server-Sent Events for streaming
