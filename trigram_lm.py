"""
Phase III: Trigram Language Model with Interpolation
- Trains Maximum Likelihood Estimation (MLE) based trigram model
- Uses interpolation to smooth probabilities
- Generates variable-length stories until <EOT> token
"""

from collections import defaultdict, Counter
import random
import sys
from model_persistence import save_model

sys.stdout.reconfigure(encoding="utf-8")

# ============================================================================
# 1. LOAD TOKENIZED CORPUS
# ============================================================================

print("[*] Loading tokenized corpus...")
with open("tokenized_corpus.txt", "r", encoding="utf-8") as f:
    lines = [line.strip().split() for line in f if line.strip()]

print(f"    Total lines: {len(lines)}")

# ============================================================================
# 2. SPLIT INTO TRAIN (90%) AND DEV (10%)
# ============================================================================

n_dev = len(lines) // 10
dev_lines = lines[:n_dev]
train_lines = lines[n_dev:]

print(f"    Train lines: {len(train_lines)}")
print(f"    Dev lines: {len(dev_lines)}")

# ============================================================================
# 3. BUILD N-GRAM COUNTS FROM TRAINING DATA
# ============================================================================

print("\n[*] Building n-gram counts from training data...")

uni_count = Counter()  # P(w)
bi_count = defaultdict(int)  # P(w | w_prev)
tri_count = defaultdict(int)  # P(w | w_prev2, w_prev1)

for line in train_lines:
    for i in range(len(line)):
        w = line[i]
        uni_count[w] += 1
        
        if i >= 1:
            w_prev = line[i - 1]
            bi_count[(w_prev, w)] += 1
        
        if i >= 2:
            w_prev2 = line[i - 2]
            w_prev1 = line[i - 1]
            tri_count[(w_prev2, w_prev1, w)] += 1

total_uni = sum(uni_count.values())
print(f"    Unigram types: {len(uni_count)}")
print(f"    Bigram types: {len(bi_count)}")
print(f"    Trigram types: {len(tri_count)}")

# ============================================================================
# 4. CALCULATE LAMBDA VALUES USING DEV SET
# ============================================================================

print("\n[*] Tuning lambda values on dev set...")

tri_wins = 0
bi_wins = 0
uni_wins = 0
total_positions = 0

for line in dev_lines:
    for i in range(2, len(line)):
        w_prev2, w_prev1, w_curr = line[i - 2], line[i - 1], line[i]
        
        # Compute probabilities
        p_tri = (tri_count[(w_prev2, w_prev1, w_curr)] / bi_count[(w_prev2, w_prev1)]) \
            if bi_count[(w_prev2, w_prev1)] > 0 else 0
        
        p_bi = (bi_count[(w_prev1, w_curr)] / uni_count[w_prev1]) \
            if uni_count[w_prev1] > 0 else 0
        
        p_uni = uni_count[w_curr] / total_uni
        
        # Find which has highest probability
        max_p = max(p_tri, p_bi, p_uni)
        
        if max_p == p_tri and max_p > 0:
            tri_wins += 1
        elif max_p == p_bi and max_p > 0:
            bi_wins += 1
        elif max_p == p_uni and max_p > 0:
            uni_wins += 1
        
        total_positions += 1

# Calculate lambda as proportion of wins
lambda3 = tri_wins / total_positions if total_positions > 0 else 0
lambda2 = bi_wins / total_positions if total_positions > 0 else 0
lambda1 = uni_wins / total_positions if total_positions > 0 else 0

print(f"    Trigram wins: {tri_wins}, Lambda_3: {lambda3:.4f}")
print(f"    Bigram wins: {bi_wins}, Lambda_2: {lambda2:.4f}")
print(f"    Unigram wins: {uni_wins}, Lambda_1: {lambda1:.4f}")

# ============================================================================
# 5. STORY GENERATION WITH INTERPOLATION
# ============================================================================

def generate_story(prefix="", max_length=500):
    """
    Generate a story using interpolated trigram model.
    
    Args:
        prefix: Starting phrase (space-separated tokens)
        max_length: Maximum number of tokens to generate
    
    Returns:
        Generated story as string
    """
    # Initialize with prefix tokens
    tokens = prefix.split() if prefix else []
    
    # If no prefix, sample first token from unigram
    if len(tokens) == 0:
        first_tok = random.choices(
            list(uni_count.keys()),
            weights=[uni_count[t] for t in uni_count.keys()]
        )[0]
        tokens.append(first_tok)
    
    # Generate until <EOT> or max_length
    for _ in range(max_length):
        if len(tokens) < 2:
            # If we have < 2 tokens, sample from unigram
            next_tok = random.choices(
                list(uni_count.keys()),
                weights=[uni_count[t] for t in uni_count.keys()]
            )[0]
        else:
            # Get context
            w_prev2 = tokens[-2]
            w_prev1 = tokens[-1]
            
            # Compute interpolated probabilities for each token in vocab
            probs = {}
            for w_curr in uni_count.keys():
                # Trigram probability
                p_tri = (tri_count[(w_prev2, w_prev1, w_curr)] / bi_count[(w_prev2, w_prev1)]) \
                    if bi_count[(w_prev2, w_prev1)] > 0 else 0
                
                # Bigram probability
                p_bi = (bi_count[(w_prev1, w_curr)] / uni_count[w_prev1]) \
                    if uni_count[w_prev1] > 0 else 0
                
                # Unigram probability
                p_uni = uni_count[w_curr] / total_uni
                
                # Interpolation
                probs[w_curr] = lambda3 * p_tri + lambda2 * p_bi + lambda1 * p_uni
            
            # Normalize and sample
            total_prob = sum(probs.values())
            if total_prob > 0:
                probs = {w: p / total_prob for w, p in probs.items()}
                next_tok = random.choices(list(probs.keys()), weights=list(probs.values()))[0]
            else:
                # Fallback to unigram if all probs are 0
                next_tok = random.choices(
                    list(uni_count.keys()),
                    weights=[uni_count[t] for t in uni_count.keys()]
                )[0]
        
        tokens.append(next_tok)
        
        # Stop if we reach EOT token
        if next_tok == "<EOT>":
            break
    
    return " ".join(tokens)


# ============================================================================
# 6. DEMO: GENERATE STORIES
# ============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("TRIGRAM LANGUAGE MODEL - STORY GENERATION DEMO")
    print("=" * 70)
    
    # Generate without prefix
    print("\n[Story 1] Generated without prefix:")
    print("-" * 70)
    story1 = generate_story(max_length=200)
    print(story1)
    
    # Generate with prefix
    print("\n[Story 2] Generated with prefix 'ایک دن':")
    print("-" * 70)
    story2 = generate_story(prefix="ایک دن", max_length=200)
    print(story2)
    
    # Generate another with different prefix
    print("\n[Story 3] Generated with prefix 'ایک بچہ':")
    print("-" * 70)
    story3 = generate_story(prefix="ایک بچہ", max_length=200)
    print(story3)
    
    print("\n" + "=" * 70)
    print("Model Parameters:")
    print(f"  Vocabulary Size: {len(uni_count)}")
    print(f"  Lambda_3 (Trigram): {lambda3:.4f}")
    print(f"  Lambda_2 (Bigram): {lambda2:.4f}")
    print(f"  Lambda_1 (Unigram): {lambda1:.4f}")
    print("=" * 70)
    
    # Save model to disk
    print("\n[*] Saving model to disk...")
    save_model(
        uni_count,
        bi_count,
        tri_count,
        {
            'lambda3': lambda3,
            'lambda2': lambda2,
            'lambda1': lambda1
        },
        set(uni_count.keys())
    )
