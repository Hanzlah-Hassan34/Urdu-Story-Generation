# Urdu-Story-Generation

AI-powered Urdu children's story generation using BPE tokenization and trigram language modeling.

## Phases Completed

### Phase I-IV: Backend & Microservice
- BPE Tokenizer implementation
- Trigram Language Model training
- gRPC microservice with Docker support
- GitHub Actions CI/CD pipeline

### Phase V: Reactive Frontend (Current)
- Next.js web application
- Real-time streaming story generation
- Urdu text input/output with RTL support
- Server-Sent Events for ChatGPT-like experience

## Quick Start

1. **Start the gRPC server:**
   ```bash
   python grpc_server.py
   ```

2. **Start the frontend:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. Open http://localhost:3000 and start generating stories!

## Architecture

- **Backend**: Python gRPC service with trigram model
- **Frontend**: Next.js with TypeScript, streaming via SSE
- **Communication**: gRPC between API routes and backend, SSE to browser

## Next Steps

- Phase VI: Full deployment on Vercel + cloud backend