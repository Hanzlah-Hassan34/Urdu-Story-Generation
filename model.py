"""Save and load trained trigram model"""

import pickle
from pathlib import Path
from collections import Counter, defaultdict

MODEL_PATH = Path("trigram_model.pkl")

def save_model(uni_count, bi_count, tri_count, lambdas, vocab):
    """Save trained model to disk
    
    Args:
        uni_count: Counter of unigrams
        bi_count: defaultdict of bigrams
        tri_count: defaultdict of trigrams
        lambdas: dict with lambda3, lambda2, lambda1
        vocab: set of vocabulary tokens
    """
    model_data = {
        'uni_count': uni_count,
        'bi_count': dict(bi_count),
        'tri_count': dict(tri_count),
        'lambdas': lambdas,
        'vocab': vocab,
        'total_uni': sum(uni_count.values())
    }
    
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model_data, f)
    
    print(f"[✓] Model saved to {MODEL_PATH}")

def load_model():
    """Load trained model from disk
    
    Returns:
        (uni_count, bi_count, tri_count, lambdas, vocab, total_uni)
    """
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model not found: {MODEL_PATH}\nRun 'python train_model.py' first.")
    
    with open(MODEL_PATH, 'rb') as f:
        data = pickle.load(f)
    
    uni_count = Counter(data['uni_count'])
    bi_count = defaultdict(int, data['bi_count'])
    tri_count = defaultdict(int, data['tri_count'])
    
    print(f"[✓] Model loaded | Vocab: {len(data['vocab'])} | λ: {data['lambdas']}")
    
    return (uni_count, bi_count, tri_count, data['lambdas'], data['vocab'], data['total_uni'])
