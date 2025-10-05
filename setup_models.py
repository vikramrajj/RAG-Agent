"""
Quick Start Script for Lightweight Models
Sets up and tests the model manager with Mistral
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from model_manager import get_model_manager, load_model, chat
from lightweight_models_config import LIGHTWEIGHT_MODELS, list_all_models

def main():
    print("🤖 SAT - Lightweight Models Quick Start\n")
    print("=" * 60)
    
    # Initialize model manager
    print("\n📋 Step 1: Initializing Model Manager...")
    manager = get_model_manager()
    
    # Check Ollama status
    print("\n🔍 Step 2: Checking Ollama Status...")
    if not manager._check_ollama_status():
        print("❌ Ollama is not running!")
        print("\n💡 To fix this:")
        print("   1. Install Ollama from https://ollama.ai")
        print("   2. Start Ollama with: ollama serve")
        print("   3. Run this script again")
        return
    
    print("✅ Ollama is running!")
    
    # List downloaded models
    print("\n📦 Step 3: Checking Downloaded Models...")
    downloaded = manager.list_downloaded_models()
    
    if downloaded:
        print(f"✅ Found {len(downloaded)} downloaded models:")
        for model in downloaded:
            print(f"   - {model['display_name']} ({model['size_gb']}GB)")
            print(f"     Speed: {model['speed']}, Quality: {model['quality']}")
    else:
        print("ℹ️  No models downloaded yet")
    
    # Recommend and load a model
    print("\n🎯 Step 4: Loading Recommended Model...")
    print("   Recommended for students: Mistral 7B")
    print("   (Best balance of speed and quality)")
    
    model_to_load = "mistral"
    
    # Check if mistral is available, otherwise try phi3-mini
    if not manager.is_model_available(model_to_load):
        print(f"\n⬇️  Model '{model_to_load}' not found. Checking for alternatives...")
        
        # Try phi3-mini as fallback
        if manager.is_model_available("phi3-mini"):
            model_to_load = "phi3-mini"
            print(f"✅ Using {model_to_load} instead (faster, smaller)")
        else:
            print(f"\n📥 Downloading {model_to_load}...")
            print("   This will take a few minutes (4.1GB download)")
            
            user_input = input("\nProceed with download? (y/n): ")
            if user_input.lower() != 'y':
                print("\n❌ Download cancelled")
                print("\n💡 To download manually, run:")
                print(f"   ollama pull mistral:7b")
                return
    
    # Load the model
    print(f"\n🔄 Loading {model_to_load}...")
    success = load_model(model_to_load, auto_pull=True)
    
    if not success:
        print(f"❌ Failed to load {model_to_load}")
        return
    
    print(f"✅ Model loaded successfully!")
    
    # Show model info
    info = manager.get_model_info()
    print(f"\n📊 Model Information:")
    print(f"   Name: {info['display_name']}")
    print(f"   Size: {info['size_gb']}GB")
    print(f"   Context Length: {info['context_length']:,} tokens")
    print(f"   Speed Rating: {'⚡' * info['speed_rating']}")
    print(f"   Quality Rating: {'⭐' * info['quality_rating']}")
    print(f"   Best For: {', '.join(info['best_for'])}")
    
    # Test the model
    print("\n🧪 Step 5: Testing the Model...")
    print("   Sending test question: 'What is 2+2?'")
    
    response = chat(
        message="What is 2+2? Answer briefly.",
        system_prompt="You are a helpful tutor. Be concise."
    )
    
    if response['success']:
        print(f"\n✅ Test Successful!")
        print(f"   Response: {response['content']}")
        print(f"   Speed: {response['tokens_per_second']:.1f} tokens/sec")
        print(f"   Duration: {response['duration_seconds']:.2f}s")
    else:
        print(f"\n❌ Test Failed: {response['error']}")
        return
    
    # Show next steps
    print("\n" + "=" * 60)
    print("🎉 Setup Complete!")
    print("\n📚 Next Steps:")
    print("   1. Start the SAT interface: python agent_bridge.py")
    print("   2. Open browser: http://localhost:8000/sat")
    print("   3. Select your model from the dropdown")
    print("   4. Start chatting!")
    
    print("\n💡 Model Recommendations:")
    recommendations = manager.recommend_for_use_case("homework_help", 8)
    for rec in recommendations[:3]:
        status = "✅ Ready" if rec['is_downloaded'] else "⬇️  Not Downloaded"
        print(f"   {status} - {rec['display_name']} ({rec['size_gb']}GB)")
        print(f"      {rec['description']}")
    
    print("\n📖 For more information, see: LIGHTWEIGHT_MODELS_GUIDE.md")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Need help? Check:")
        print("   - Is Ollama installed? https://ollama.ai")
        print("   - Is Ollama running? Try: ollama serve")
        print("   - See LIGHTWEIGHT_MODELS_GUIDE.md for troubleshooting")
