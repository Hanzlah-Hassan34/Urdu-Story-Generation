"""Byte-Pair Encoding (BPE) Tokenizer for Urdu text"""

from collections import Counter
from pathlib import Path
import sys

CORPUS = Path("corpus.txt")
VOCAB_SIZE = 250
SPECIAL = {"\uE000": "<EOS>", "\uE001": "<EOP>", "\uE002": "<EOT>"}
sys.stdout.reconfigure(encoding="utf-8")

# Load corpus
lines = [l.strip() for l in CORPUS.read_text(encoding="utf-8").splitlines() if l.strip()]
freq = Counter(w for ln in lines for w in ln.split())

def to_syms(w):
    return (w,) if w.startswith("<") and w.endswith(">") else tuple(list(w))

vocab = {to_syms(w): n for w, n in freq.items()}
symbols = {s for w in vocab for s in w}
merges = []

def pair_stats():
    """Count occurrence of adjacent symbol pairs"""
    counts = Counter()
    for w, n in vocab.items():
        for i in range(len(w) - 1):
            counts[(w[i], w[i + 1])] += n
    return counts

def merge(pair):
    """Merge a pair of symbols in vocabulary"""
    global vocab
    merged = "".join(pair)
    new_vocab = {}
    for w, n in vocab.items():
        out, i = [], 0
        while i < len(w):
            if i + 1 < len(w) and (w[i], w[i + 1]) == pair:
                out.append(merged)
                i += 2
            else:
                out.append(w[i])
                i += 1
        new_vocab[tuple(out)] = n
    vocab = new_vocab

# Learn BPE merges
max_merges = VOCAB_SIZE - len(symbols)
while len(merges) < max_merges:
    stats = pair_stats()
    if not stats:
        break
    best = stats.most_common(1)[0][0]
    merges.append(best)
    merge(best)

def encode(word):
    """Encode a word using learned BPE merges"""
    if word.startswith("<") and word.endswith(">"):
        return [word]
    syms = list(word)
    for a, b in merges:
        merged = a + b
        out, i = [], 0
        while i < len(syms):
            if i + 1 < len(syms) and syms[i] == a and syms[i + 1] == b:
                out.append(merged)
                i += 2
            else:
                out.append(syms[i])
                i += 1
        syms = out
    return syms

# Tokenize corpus
token_lines = []
for line in lines:
    tokens = []
    for word in line.split():
        tokens.extend(encode(word))
    token_lines.append(" ".join(tokens))

def show(token):
    return SPECIAL.get(token, token)

token_lines = [" ".join(show(t) for t in ln.split()) for ln in token_lines]
vocab_dict = {tok: i for i, tok in enumerate(sorted({show(t) for ln in token_lines for t in ln.split()}))}

print(f"BPE Tokenization Complete:")
print(f"  Merges: {len(merges)} | Vocabulary: {len(vocab_dict)} | Lines: {len(token_lines)}")

# Save tokenized corpus
with open("tokenized_corpus.txt", "w", encoding="utf-8") as f:
    for line in token_lines:
        f.write(line + "\n")
