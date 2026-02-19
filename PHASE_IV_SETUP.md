# Phase IV: Microservice & Containerization Setup Guide

## 📋 Prerequisites

Before you proceed, ensure you have:
- Python 3.10+
- Docker (for containerization)
- Git
- A GitHub account
- `protobuf-compiler` or `grpcio-tools`

---

## 🚀 Local Setup (Before GitHub)

### Step 1: Train and Save the Model

First, make sure the trigram model is trained and saved:

```bash
python trigram_lm.py
```

✅ This will:
- Train the trigram model on tokenized corpus
- Calculate lambdas using dev set
- Save model to `trigram_model.pkl`

**Expected output:**
```
[✓] Model saved to trigram_model.pkl
```

---

### Step 2: Generate gRPC Python Files from Proto

You MUST run this command to generate the gRPC Python code from the proto definition:

```bash
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. generate.proto
```

✅ This creates:
- `generate_pb2.py` (message definitions)
- `generate_pb2_grpc.py` (service definitions)

**Without these files, the server will not run!**

---

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- `grpcio` - gRPC framework
- `grpcio-tools` - gRPC code generator
- `protobuf` - Protocol buffers

---

### Step 4: Run gRPC Server Locally

```bash
python grpc_server.py
```

✅ Expected output:
```
[✓] Model initialized successfully

======================================================================
gRPC STORY GENERATION SERVER
======================================================================
[✓] Server listening on port 50051
    Service: StoryGenerator
    Methods: Generate, GetModelInfo
======================================================================
```

**Server is now running on `localhost:50051`**

---

### Step 5: Test with gRPC Client (in another terminal)

```bash
python grpc_client.py
```

This will test:
- Getting model information
- Generating stories without prefix
- Generating stories with prefix

---

## 🐳 Docker Setup

### Step 1: Build Docker Image

```bash
docker build -t urdu-story-service:latest .
```

This will:
- Use Python 3.10 slim image
- Install dependencies
- Generate gRPC files
- Prepare the container

### Step 2: Run Docker Container

```bash
docker run -d --name story-service -p 50051:50051 urdu-story-service:latest
```

This runs the container in detached mode, mapping port 50051.

### Step 3: Check Logs

```bash
docker logs story-service
```

### Step 4: Stop Container

```bash
docker stop story-service
```

---

## 🔧 GitHub Setup (Manual Steps Required)

### Step 1: Initialize Git Repository

```bash
cd c:\Users\Hanzlah\Downloads\nlp\nlp
git init
```

### Step 2: Create GitHub Repository

1. Go to https://github.com/new
2. Create a new repository:
   - **Name**: `urdu-story-generation`
   - **Description**: "Urdu Children's Story Generation with BPE Tokenizer & Trigram Model"
   - **Visibility**: Public (required for free CI/CD)
   - **Initialize with**: README (optional)

3. Copy the repository URL (should look like: `https://github.com/YourUsername/urdu-story-generation.git`)

### Step 3: Push Code to GitHub

```bash
git remote add origin https://github.com/YourUsername/urdu-story-generation.git
git branch -M main
git add .
git commit -m "Phase IV: gRPC Microservice with Docker & CI/CD"
git push -u origin main
```

### Step 4: Verify GitHub Actions

1. Go to your repository on GitHub
2. Click on **"Actions"** tab
3. You should see the `CI/CD Pipeline` workflow running
4. Wait for it to complete (green checkmark = success)

---

## 📦 Project Structure

```
nlp/
├── bpe.py                      # Phase II: BPE Tokenizer
├── corpus.txt                  # Preprocessed corpus
├── preprocessing.py            # Data preprocessing
├── tokenized_corpus.txt        # Tokenized text
├── trigram_lm.py              # Phase III: Trigram Model
├── model_persistence.py        # Save/Load model
├── generate.proto             # gRPC service definition
├── grpc_server.py             # Phase IV: gRPC Server
├── grpc_client.py             # Test client
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Docker image definition
├── .dockerignore              # Docker ignore file
├── .github/
│   └── workflows/
│       └── ci-cd.yml          # GitHub Actions pipeline
├── trigram_model.pkl          # Trained model (auto-generated)
├── generate_pb2.py            # gRPC messages (auto-generated)
└── generate_pb2_grpc.py       # gRPC service (auto-generated)
```

---

## 🌐 Deployment Options

### Option 1: Render.com (Recommended)

1. Go to https://render.com
2. Sign up with GitHub
3. Click "New +" → "Web Service"
4. Connect your GitHub repository
5. Set:
   - **Name**: `urdu-story-service`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt && python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. generate.proto`
   - **Start Command**: `python grpc_server.py`
   - **Instance Type**: Free tier

6. Click "Create Web Service"
7. Wait for deployment (5-10 minutes)
8. Get the service URL from Render dashboard

### Option 2: Railway.app

1. Go to https://railway.app
2. Sign up with GitHub
3. Create new project
4. Select "Deploy from GitHub repo"
5. Choose your repository
6. Railway auto-detects Python and Dockerfile
7. Click "Deploy"

### Option 3: Google Cloud Run

1. Install Google Cloud SDK
2. Authenticate: `gcloud auth login`
3. Deploy: `gcloud run deploy urdu-story-service --source . --platform managed --allow-unauthenticated`

---

## ✅ Verification Checklist

- [ ] Installed grpcio, grpcio-tools, protobuf
- [ ] Ran `python trigram_lm.py` to train model
- [ ] Generated gRPC files: `python -m grpc_tools.protoc ...`
- [ ] Started server: `python grpc_server.py`
- [ ] Tested locally: `python grpc_client.py`
- [ ] Built Docker image: `docker build ...`
- [ ] Created GitHub repository
- [ ] Pushed code to GitHub
- [ ] GitHub Actions workflow completed successfully
- [ ] (Optional) Deployed to Render/Railway/Google Cloud

---

## 🐛 Troubleshooting

**Error: "ModuleNotFoundError: No module named 'generate_pb2'"**
→ Run: `python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. generate.proto`

**Error: "FileNotFoundError: Model file not found"**
→ Run: `python trigram_lm.py` to train and save model

**Docker build fails**
→ Ensure `requirements.txt` exists and protobuf-compiler is in apt packages

**GitHub Actions fails**
→ Check logs in Actions tab. Usually missing dependencies or protoc failure

---

## 📞 Next Steps

After Phase IV completion:
- **Phase V**: Build React frontend to consume gRPC service
- **Phase VI**: Full deployment on Vercel + cloud backend

