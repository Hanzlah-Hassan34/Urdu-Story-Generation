"""
gRPC Client: Test the story generation service
"""

import sys
import grpc

import generate_pb2
import generate_pb2_grpc

sys.stdout.reconfigure(encoding="utf-8")


def test_grpc_service():
    """Test gRPC service with sample requests"""
    
    # Connect to server
    channel = grpc.aio.aio.insecure_channel('localhost:50051')
    stub = generate_pb2_grpc.StoryGeneratorStub(channel)
    
    print("=" * 70)
    print("gRPC CLIENT - TESTING STORY GENERATION SERVICE")
    print("=" * 70)
    
    try:
        # Test 1: Get model info
        print("\n[Test 1] Getting model information...")
        request = generate_pb2.Empty()
        response = stub.GetModelInfo(request)
        print(f"[✓] Model Info:")
        print(f"    Vocabulary Size: {response.vocab_size}")
        print(f"    Lambda3: {response.lambda3:.4f}")
        print(f"    Lambda2: {response.lambda2:.4f}")
        print(f"    Lambda1: {response.lambda1:.4f}")
        print(f"    Version: {response.model_version}")
        
        # Test 2: Generate without prefix
        print("\n[Test 2] Generating story without prefix...")
        request = generate_pb2.GenerateRequest(
            prefix="",
            max_length=100
        )
        response = stub.Generate(request)
        print(f"[✓] Generated {response.num_tokens} tokens:")
        print(f"    Story: {response.story[:100]}...")
        
        # Test 3: Generate with prefix
        print("\n[Test 3] Generating story with prefix 'ایک دن'...")
        request = generate_pb2.GenerateRequest(
            prefix="ایک دن",
            max_length=100
        )
        response = stub.Generate(request)
        print(f"[✓] Generated {response.num_tokens} tokens:")
        print(f"    Story: {response.story}")
        
        print("\n" + "=" * 70)
        print("All tests passed!")
        print("=" * 70)
    
    except grpc.RpcError as e:
        print(f"[✗] RPC Error: {e.code()} - {e.details()}")
    except Exception as e:
        print(f"[✗] Error: {e}")


if __name__ == "__main__":
    test_grpc_service()
