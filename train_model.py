"""Trigram Language Model with Interpolation for Urdu Story Generation"""

from collections import defaultdict, Counter
import random
import sys
from model import save_model

sys.stdout.reconfigure(encoding="utf-8")

# Load tokenized corpus
print("[*] Loading tokenized corpus...")
with open("tokenized_corpus.txt", "r", encoding="utf-8") as f:
    lines = [line.strip().split() for line in f if line.strip()]

print(f"    Total lines: {len(lines)}")

# Split into train (90%) and dev (10%)
n_dev = len(lines) // 10
dev_lines = lines[:n_dev]
train_lines = lines[n_dev:]

print(f"    Train: {len(train_lines)} | Dev: {len(dev_lines)}")

# Build n-gram counts from training data
print("\n[*] Building n-gram counts...")

uni_count = Counter()
bi_count = defaultdict(int)
tri_count = defaultdict(int)

for line in train_lines:
    for i, word in enumerate(line):
        uni_count[word] += 1
        if i >= 1:
            bi_count[(line[i - 1], word)] += 1
        if i >= 2:
            tri_count[(line[i - 2], line[i - 1], word)] += 1

total_uni = sum(uni_count.values())
print(f"    Unigrams: {len(uni_count)} | Bigrams: {len(bi_count)} | Trigrams: {len(tri_count)}")

# Calculate lambda values using dev set
print("\n[*] Tuning lambda values...")

tri_wins = bi_wins = uni_wins = 0

for line in dev_lines:
    for i in range(2, len(line)):
        w_prev2, w_prev1, w_curr = line[i - 2], line[i - 1], line[i]
        
        p_tri = (tri_count[(w_prev2, w_prev1, w_curr)] / bi_count[(w_prev2, w_prev1)]) \
            if bi_count[(w_prev2, w_prev1)] > 0 else 0
        p_bi = (bi_count[(w_prev1, w_curr)] / uni_count[w_prev1]) \
            if uni_count[w_prev1] > 0 else 0
        p_uni = uni_count[w_curr] / total_uni
        
        max_p = max(p_tri, p_bi, p_uni)
        if max_p == p_tri and max_p > 0:
            tri_wins += 1
        elif max_p == p_bi and max_p > 0:
            bi_wins += 1
        elif max_p == p_uni and max_p > 0:
            uni_wins += 1

total_pos = tri_wins + bi_wins + uni_wins
lambda3 = tri_wins / total_pos if total_pos > 0 else 1/3
lambda2 = bi_wins / total_pos if total_pos > 0 else 1/3
lambda1 = uni_wins / total_pos if total_pos > 0 else 1/3

print(f"    λ₃ (Trigram): {lambda3:.4f}")
print(f"    λ₂ (Bigram): {lambda2:.4f}")
print(f"    λ₁ (Unigram): {lambda1:.4f}")

def generate_story(prefix="", max_length=500):
    """Generate story using interpolated trigram model"""
    tokens = prefix.split() if prefix else []
    
    if not tokens:
        tokens.append(random.choices(list(uni_count.keys()), 
                                    weights=[uni_count[t] for t in uni_count])[0])
    
    for _ in range(max_length):
        if len(tokens) < 2:
            next_tok = random.choices(list(uni_count.keys()), 
                                     weights=[uni_count[t] for t in uni_count])[0]
        else:
            w_prev2, w_prev1 = tokens[-2], tokens[-1]
            probs = {}
            
            for w_curr in uni_count.keys():
                p_tri = (tri_count[(w_prev2, w_prev1, w_curr)] / bi_count[(w_prev2, w_prev1)]) \
                    if bi_count[(w_prev2, w_prev1)] > 0 else 0
                p_bi = (bi_count[(w_prev1, w_curr)] / uni_count[w_prev1]) \
                    if uni_count[w_prev1] > 0 else 0
                p_uni = uni_count[w_curr] / total_uni
                
                probs[w_curr] = lambda3 * p_tri + lambda2 * p_bi + lambda1 * p_uni
            
            total_prob = sum(probs.values())
            if total_prob > 0:
                probs = {w: p / total_prob for w, p in probs.items()}
                next_tok = random.choices(list(probs.keys()), weights=list(probs.values()))[0]
            else:
                next_tok = random.choices(list(uni_count.keys()), 
                                         weights=[uni_count[t] for t in uni_count])[0]
        
        tokens.append(next_tok)
        if next_tok == "<EOT>":
            break
    
    return " ".join(tokens)

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("MODEL TRAINING COMPLETE")
    print("=" * 70)
    print(f"Vocabulary Size: {len(uni_count)}")
    
    # Save model
    print("\n[*] Saving model...")
    save_model(uni_count, bi_count, tri_count, 
               {'lambda3': lambda3, 'lambda2': lambda2, 'lambda1': lambda1},
               set(uni_count.keys()))
    print("=" * 70)
