"""
Phase IV: gRPC Microservice for Trigram Story Generation
Serves the trained model via gRPC protocol
"""

import sys
import random
from concurrent import futures

import grpc
from collections import defaultdict, Counter

from model_persistence import load_model
import generate_pb2
import generate_pb2_grpc

sys.stdout.reconfigure(encoding="utf-8")

# Global model state
MODEL_STATE = {
    'uni_count': None,
    'bi_count': None,
    'tri_count': None,
    'lambdas': None,
    'vocab': None,
    'total_uni': None
}


def initialize_model():
    """Load model from disk on startup"""
    print("[*] Initializing gRPC server...")
    print("[*] Loading model from disk...")
    
    try:
        uni_count, bi_count, tri_count, lambdas, vocab, total_uni = load_model()
        
        MODEL_STATE['uni_count'] = uni_count
        MODEL_STATE['bi_count'] = bi_count
        MODEL_STATE['tri_count'] = tri_count
        MODEL_STATE['lambdas'] = lambdas
        MODEL_STATE['vocab'] = vocab
        MODEL_STATE['total_uni'] = total_uni
        
        print(f"[✓] Model initialized successfully")
        return True
    except FileNotFoundError as e:
        print(f"[✗] Error: {e}")
        return False


def generate_story(prefix="", max_length=500):
    """
    Generate story using loaded model, yielding chunks
    
    Args:
        prefix: Starting phrase (space-separated tokens)
        max_length: Maximum tokens to generate
    
    Yields:
        Partial story chunks
    """
    uni_count = MODEL_STATE['uni_count']
    bi_count = MODEL_STATE['bi_count']
    tri_count = MODEL_STATE['tri_count']
    lambdas = MODEL_STATE['lambdas']
    vocab = MODEL_STATE['vocab']
    total_uni = MODEL_STATE['total_uni']
    
    lambda3 = lambdas['lambda3']
    lambda2 = lambdas['lambda2']
    lambda1 = lambdas['lambda1']
    
    # Initialize with prefix
    tokens = prefix.split() if prefix else []
    
    # If no prefix, sample first token from unigram
    if len(tokens) == 0:
        first_tok = random.choices(
            list(uni_count.keys()),
            weights=[uni_count[t] for t in uni_count.keys()]
        )[0]
        tokens.append(first_tok)
        yield " ".join(tokens)  # Yield first token
    
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
            
            # Compute interpolated probabilities
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
                # Fallback to unigram
                next_tok = random.choices(
                    list(uni_count.keys()),
                    weights=[uni_count[t] for t in uni_count.keys()]
                )[0]
        
        tokens.append(next_tok)
        yield " ".join(tokens)  # Yield updated story
        
        # Stop if we reach EOT
        if next_tok == "<EOT>":
            break


class StoryGeneratorServicer(generate_pb2_grpc.StoryGeneratorServicer):
    """gRPC service implementation"""
    
    def Generate(self, request, context):
        """
        Generate a story based on prefix and max_length, streaming chunks
        
        Args:
            request: GenerateRequest with prefix and max_length
            context: gRPC context
        
        Yields:
            GenerateResponse with story chunks
        """
        try:
            print(f"[*] Generating story with prefix: '{request.prefix}', max_length: {request.max_length}")
            
            lambdas = MODEL_STATE['lambdas']
            num_tokens = 0
            
            for chunk in generate_story(
                prefix=request.prefix,
                max_length=request.max_length
            ):
                num_tokens = len(chunk.split())
                is_final = chunk.endswith("<EOT>") or num_tokens >= request.max_length
                
                response = generate_pb2.GenerateResponse(
                    chunk=chunk,
                    is_final=is_final,
                    num_tokens=num_tokens,
                    lambda3=lambdas['lambda3'],
                    lambda2=lambdas['lambda2'],
                    lambda1=lambdas['lambda1']
                )
                
                yield response
                
                if is_final:
                    break
            
            print(f"[✓] Story generation completed: {num_tokens} tokens")
        
        except Exception as e:
            print(f"[✗] Error in Generate: {e}")
            context.set_details(f"Error: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            yield generate_pb2.GenerateResponse()
    
    def GetModelInfo(self, request, context):
        """
        Get model information
        
        Returns:
            ModelInfo with vocab size and lambdas
        """
        try:
            lambdas = MODEL_STATE['lambdas']
            vocab_size = len(MODEL_STATE['vocab'])
            
            response = generate_pb2.ModelInfo(
                vocab_size=vocab_size,
                lambda3=lambdas['lambda3'],
                lambda2=lambdas['lambda2'],
                lambda1=lambdas['lambda1'],
                model_version="1.0-trigram"
            )
            
            print(f"[✓] Model info requested")
            return response
        
        except Exception as e:
            print(f"[✗] Error in GetModelInfo: {e}")
            context.set_details(f"Error: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            return generate_pb2.ModelInfo()


def serve():
    """Start gRPC server"""
    # Initialize model
    if not initialize_model():
        print("[✗] Failed to initialize model. Exiting.")
        sys.exit(1)
    
    # Create server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    generate_pb2_grpc.add_StoryGeneratorServicer_to_server(
        StoryGeneratorServicer(), server
    )
    
    # Bind to port
    port = "50051"
    server.add_insecure_port(f"[::]:{port}")
    
    # Start server
    print(f"\n{'='*70}")
    print("gRPC STORY GENERATION SERVER")
    print(f"{'='*70}")
    print(f"[✓] Server listening on port {port}")
    print(f"    Service: StoryGenerator")
    print(f"    Methods: Generate, GetModelInfo")
    print(f"{'='*70}\n")
    
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
