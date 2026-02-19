# Urdu Story Generator

AI-powered Urdu story generation using BPE tokenization and trigram language modeling.

## Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- pip/npm

### Backend

```bash
# Install dependencies
pip install -r requirements.txt

# Preprocess corpus
python preprocess.py

# Tokenize with BPE
python tokenizer.py

# Train and save model
python train_model.py

# Start gRPC server
python server.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit http://localhost:3000 to generate stories.

## Architecture

- **Tokenizer**: BPE-based subword tokenization
- **Model**: Interpolated trigram language model trained on Urdu stories
- **Backend**: Python gRPC microservice
- **Frontend**: Next.js with real-time streaming via SSE

## Project Files

- `preprocess.py` - Clean and normalize Urdu text
- `tokenizer.py` - BPE tokenization
- `train_model.py` - Train trigram model
- `model.py` - Save/load model weights
- `server.py` - gRPC service
- `client.py` - Test client
