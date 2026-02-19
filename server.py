"""gRPC server for trigram story generation"""

import sys
import random
from concurrent import futures

import grpc
from collections import defaultdict, Counter

from model import load_model
import generate_pb2
import generate_pb2_grpc

sys.stdout.reconfigure(encoding="utf-8")

# Global model state
MODEL_STATE = {}

def initialize_model():
    """Load model from disk on startup"""
    try:
        print("[*] Loading model...")
        uni_count, bi_count, tri_count, lambdas, vocab, total_uni = load_model()
        
        MODEL_STATE.update({
            'uni_count': uni_count,
            'bi_count': bi_count,
            'tri_count': tri_count,
            'lambdas': lambdas,
            'vocab': vocab,
            'total_uni': total_uni
        })
        return True
    except FileNotFoundError as e:
        print(f"[✗] {e}")
        return False

def generate_story(prefix="", max_length=500):
    """Generate story using interpolated trigram model"""
    uni = MODEL_STATE['uni_count']
    bi = MODEL_STATE['bi_count']
    tri = MODEL_STATE['tri_count']
    l3, l2, l1 = MODEL_STATE['lambdas'].values()
    total = MODEL_STATE['total_uni']
    
    tokens = prefix.split() if prefix else []
    
    if not tokens:
        tokens.append(random.choices(list(uni.keys()), weights=[uni[t] for t in uni])[0])
        yield " ".join(tokens)
    
    for _ in range(max_length):
        if len(tokens) < 2:
            next_tok = random.choices(list(uni.keys()), weights=[uni[t] for t in uni])[0]
        else:
            w_prev2, w_prev1 = tokens[-2], tokens[-1]
            probs = {}
            
            for w_curr in uni.keys():
                p_tri = (tri[(w_prev2, w_prev1, w_curr)] / bi[(w_prev2, w_prev1)]) if bi[(w_prev2, w_prev1)] > 0 else 0
                p_bi = (bi[(w_prev1, w_curr)] / uni[w_prev1]) if uni[w_prev1] > 0 else 0
                p_uni = uni[w_curr] / total
                
                probs[w_curr] = l3 * p_tri + l2 * p_bi + l1 * p_uni
            
            total_prob = sum(probs.values())
            if total_prob > 0:
                probs = {w: p / total_prob for w, p in probs.items()}
                next_tok = random.choices(list(probs.keys()), weights=list(probs.values()))[0]
            else:
                next_tok = random.choices(list(uni.keys()), weights=[uni[t] for t in uni])[0]
        
        tokens.append(next_tok)
        yield " ".join(tokens)
        
        if next_tok == "<EOT>":
            break

class StoryGeneratorServicer(generate_pb2_grpc.StoryGeneratorServicer):
    """gRPC story generator service"""
    
    def Generate(self, request, context):
        """Generate story from prefix"""
        try:
            num_tokens = 0
            for chunk in generate_story(prefix=request.prefix, max_length=request.max_length):
                num_tokens = len(chunk.split())
                is_final = chunk.endswith("<EOT>") or num_tokens >= request.max_length
                
                yield generate_pb2.GenerateResponse(
                    chunk=chunk,
                    is_final=is_final,
                    num_tokens=num_tokens,
                    lambda3=MODEL_STATE['lambdas']['lambda3'],
                    lambda2=MODEL_STATE['lambdas']['lambda2'],
                    lambda1=MODEL_STATE['lambdas']['lambda1']
                )
                
                if is_final:
                    break
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
    
    def GetModelInfo(self, request, context):
        """Get model information"""
        return generate_pb2.ModelInfo(
            vocab_size=len(MODEL_STATE['vocab']),
            lambda3=MODEL_STATE['lambdas']['lambda3'],
            lambda2=MODEL_STATE['lambdas']['lambda2'],
            lambda1=MODEL_STATE['lambdas']['lambda1'],
            model_version="1.0"
        )

def serve():
    """Start gRPC server"""
    if not initialize_model():
        sys.exit(1)
    
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    generate_pb2_grpc.add_StoryGeneratorServicer_to_server(StoryGeneratorServicer(), server)
    
    port = "50051"
    server.add_insecure_port(f"[::]:{port}")
    
    print(f"\n{'='*50}")
    print("gRPC Story Server")
    print(f"{'='*50}")
    print(f"[✓] Listening on port {port}")
    print(f"{'='*50}\n")
    
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
