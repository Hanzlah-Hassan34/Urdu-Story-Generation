from collections import Counter
from pathlib import Path
import sys

CORPUS = Path("corpus.txt")
VOCAB_SIZE = 250
SPECIAL = {"\uE000": "<EOS>", "\uE001": "<EOP>", "\uE002": "<EOT>"}
sys.stdout.reconfigure(encoding="utf-8")

lines = [l.strip() for l in CORPUS.read_text(encoding="utf-8").splitlines() if l.strip()]
freq = Counter(w for ln in lines for w in ln.split())

def to_syms(w):
    return (w,) if w.startswith("<") and w.endswith(">") else tuple(list(w))

vocab = {to_syms(w): n for w,n in freq.items()}
symbols = {s for w in vocab for s in w}
merges = []

def pair_stats():
    c = Counter()
    for w,n in vocab.items():
        for i in range(len(w)-1):
            c[(w[i],w[i+1])] += n
    return c

def merge(pair):
    global vocab
    merged = "".join(pair)
    new = {}
    for w,n in vocab.items():
        out,i=[],0
        while i<len(w):
            if i+1<len(w) and (w[i],w[i+1])==pair:
                out.append(merged); i+=2
            else:
                out.append(w[i]); i+=1
        new[tuple(out)] = n
    vocab = new

max_merges = VOCAB_SIZE - len(symbols)
while len(merges) < max_merges:
    stats = pair_stats()
    if not stats: break
    best = stats.most_common(1)[0][0]
    merges.append(best)
    merge(best)

# encode
def encode(w):
    if w.startswith("<") and w.endswith(">"): return [w]
    syms = list(w)
    for a,b in merges:
        merged,out,i=a+b,[],0
        while i<len(syms):
            if i+1<len(syms) and syms[i]==a and syms[i+1]==b:
                out.append(merged); i+=2
            else:
                out.append(syms[i]); i+=1
        syms=out
    return syms

token_lines=[]
for ln in lines:
    toks=[]
    for w in ln.split():
        toks+=encode(w)
    token_lines.append(" ".join(toks))

def show(t): return SPECIAL.get(t, t)

token_lines = [" ".join(show(t) for t in ln.split()) for ln in token_lines]
vocab_dict = {tok: i for i, tok in enumerate(sorted({show(t) for ln in token_lines for t in ln.split()}))}
print("=== merges ===")
print(merges)
print("=== vocab ===")
print(vocab_dict)
print("=== tokens ===")
#print(token_lines)
print("Merges:",len(merges),"| Final vocab:",len(vocab_dict),"| Token lines:",len(token_lines))

# Save tokenized corpus
with open("tokenized_corpus.txt", "w", encoding="utf-8") as f:
    for line in token_lines:
        f.write(line + "\n")
