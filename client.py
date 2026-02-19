"""Test client for gRPC story generation service"""

import sys
import grpc

import generate_pb2
import generate_pb2_grpc

sys.stdout.reconfigure(encoding="utf-8")

def test_service():
    """Test gRPC service"""
    channel = grpc.insecure_channel('localhost:50051')
    stub = generate_pb2_grpc.StoryGeneratorStub(channel)
    
    print("=" * 50)
    print("gRPC Story Generator Client")
    print("=" * 50)
    
    try:
        # Get model info
        print("\n[1] Model Info:")
        resp = stub.GetModelInfo(generate_pb2.Empty())
        print(f"    Vocab: {resp.vocab_size}")
        print(f"    λ₃: {resp.lambda3:.4f}, λ₂: {resp.lambda2:.4f}, λ₁: {resp.lambda1:.4f}")
        
        # Generate story without prefix
        print("\n[2] Generate without prefix:")
        req = generate_pb2.GenerateRequest(prefix="", max_length=50)
        for resp in stub.Generate(req):
            if resp.is_final:
                print(f"    {resp.chunk}")
        
        # Generate story with prefix
        print("\n[3] Generate with prefix 'ایک دن':")
        req = generate_pb2.GenerateRequest(prefix="ایک دن", max_length=50)
        for resp in stub.Generate(req):
            if resp.is_final:
                print(f"    {resp.chunk}")
        
        print("\n" + "=" * 50)
    
    except grpc.RpcError as e:
        print(f"[X] Error: {e.code()} - {e.details()}")
    except Exception as e:
        print(f"[X] Error: {e}")

if __name__ == "__main__":
    test_service()
