"""
Model Persistence: Save and Load Trained Trigram Model
Saves: uni_count, bi_count, tri_count, lambdas, vocabulary
"""

import pickle
from pathlib import Path
from collections import Counter, defaultdict

MODEL_PATH = Path("trigram_model.pkl")

def save_model(uni_count, bi_count, tri_count, lambdas, vocab):
    """
    Save trained model to disk
    
    Args:
        uni_count: Counter of unigrams
        bi_count: defaultdict of bigrams
        tri_count: defaultdict of trigrams
        lambdas: dict with {'lambda3', 'lambda2', 'lambda1'}
        vocab: set of vocabulary tokens
    """
    model_data = {
        'uni_count': uni_count,
        'bi_count': dict(bi_count),  # Convert defaultdict to dict for pickling
        'tri_count': dict(tri_count),
        'lambdas': lambdas,
        'vocab': vocab,
        'total_uni': sum(uni_count.values())
    }
    
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model_data, f)
    
    print(f"[✓] Model saved to {MODEL_PATH}")
    return MODEL_PATH


def load_model():
    """
    Load trained model from disk
    
    Returns:
        Tuple of (uni_count, bi_count, tri_count, lambdas, vocab, total_uni)
    """
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model file not found: {MODEL_PATH}\n"
            f"Run 'python trigram_lm.py' first to train and save the model."
        )
    
    with open(MODEL_PATH, 'rb') as f:
        model_data = pickle.load(f)
    
    # Convert dicts back to Counter/defaultdict
    uni_count = Counter(model_data['uni_count'])
    bi_count = defaultdict(int, model_data['bi_count'])
    tri_count = defaultdict(int, model_data['tri_count'])
    
    print(f"[✓] Model loaded from {MODEL_PATH}")
    print(f"    Vocabulary: {len(model_data['vocab'])} tokens")
    print(f"    Lambdas: {model_data['lambdas']}")
    
    return (
        uni_count,
        bi_count,
        tri_count,
        model_data['lambdas'],
        model_data['vocab'],
        model_data['total_uni']
    )
