"""
Test Phase 1 API Integration

This script tests the video recording integration with api_server.py
Run this after starting the API server in another terminal.
"""

import requests
import json
import time
from pathlib import Path

API_URL = "http://localhost:8000/api/bridge"
RECORDINGS_DIR = Path("video_training/recordings")

def test_api_integration():
    """Test video recording integration with API"""
    
    print("=" * 70)
    print("PHASE 1 API INTEGRATION TEST")
    print("=" * 70)
    print()
    
    # Check if API is running
    print("1️⃣  Checking if API server is running...")
    try:
        response = requests.get("http://localhost:8000/api/bridge/status", timeout=5)
        print(f"   ✅ API server is running: {response.json()}")
    except requests.exceptions.ConnectionError:
        print("   ❌ ERROR: API server not running")
        print("   💡 Start the API server first: python api_server.py")
        return False
    
    print()
    
    # Test 1: Request without recording
    print("2️⃣  Test 1: Request WITHOUT recording...")
    request_payload = {
        "message": "test message",
        "smart_routing": False,
        "rag_only": True
    }
    
    try:
        response = requests.post(API_URL, json=request_payload, timeout=30)
        result = response.json()
        has_video = "video_recording" in str(result.get("metadata", {}))
        
        if has_video:
            print(f"   ⚠️  WARNING: Unexpected video in response")
        else:
            print(f"   ✅ Request successful - No video recorded (as expected)")
            print(f"   📊 Response type: {result.get('type')}")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False
    
    print()
    
    # Test 2: Request with recording
    print("3️⃣  Test 2: Request WITH recording enabled...")
    
    # Count existing recordings
    existing_recordings = len(list(RECORDINGS_DIR.glob("*.mp4")))
    
    request_payload = {
        "message": "test video recording",
        "smart_routing": False,
        "rag_only": True,
        "record_video": True
    }
    
    try:
        print("   ⏱️  Recording for 5 seconds...")
        start_time = time.time()
        
        response = requests.post(API_URL, json=request_payload, timeout=30)
        
        elapsed = time.time() - start_time
        result = response.json()
        
        print(f"   ✅ Request completed in {elapsed:.2f}s")
        
        # Check for video in response
        metadata = result.get("metadata", {})
        video_path = metadata.get("video_recording")
        
        if video_path:
            print(f"   📹 Video path in response: {video_path}")
            
            # Check if file exists
            if Path(video_path).exists():
                file_size = Path(video_path).stat().st_size
                print(f"   📁 File found: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
                print(f"   ✅ Video recording SUCCESSFUL")
                return True
            else:
                print(f"   ⚠️  WARNING: File path in response but file not found")
                return False
        else:
            print(f"   ❌ No video_recording in metadata")
            print(f"   📊 Metadata keys: {list(metadata.keys())}")
            return False
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()

if __name__ == "__main__":
    success = test_api_integration()
    
    print()
    print("=" * 70)
    if success:
        print("✅ PHASE 1 INTEGRATION TEST PASSED")
        print("📹 Video recording is working with the API!")
    else:
        print("❌ PHASE 1 INTEGRATION TEST FAILED")
        print("💡 Check the error messages above for details")
    print("=" * 70)
