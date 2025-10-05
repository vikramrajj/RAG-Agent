"""
Launch Browser-Use WebUI
Standalone launcher for the browser-use WebUI interface
"""

import os
import sys
from pathlib import Path

# Add browser-use-webui to path
BROWSER_UI_PATH = Path(__file__).parent / "browser-use-webui"
if BROWSER_UI_PATH.exists():
    sys.path.insert(0, str(BROWSER_UI_PATH))
else:
    print("❌ Error: browser-use-webui directory not found!")
    print(f"   Expected at: {BROWSER_UI_PATH}")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
    
    from src.webui.interface import create_ui, theme_map  # type: ignore
    
    def main():
        import argparse
        
        parser = argparse.ArgumentParser(description="Launch Browser-Use WebUI")
        parser.add_argument("--ip", type=str, default="127.0.0.1", help="IP address to bind to")
        parser.add_argument("--port", type=int, default=7788, help="Port to listen on")
        parser.add_argument("--theme", type=str, default="Ocean", choices=theme_map.keys(), help="Theme to use")
        parser.add_argument("--share", action="store_true", help="Create a public shareable link")
        args = parser.parse_args()
        
        print("=" * 60)
        print("🌐 Browser-Use WebUI")
        print("=" * 60)
        print(f"   IP Address: {args.ip}")
        print(f"   Port: {args.port}")
        print(f"   Theme: {args.theme}")
        print(f"   Share: {'Yes' if args.share else 'No'}")
        print("=" * 60)
        print(f"\n   Opening WebUI at: http://{args.ip}:{args.port}")
        print("   Press Ctrl+C to stop the server\n")
        
        demo = create_ui(theme_name=args.theme)
        demo.queue().launch(
            server_name=args.ip, 
            server_port=args.port,
            share=args.share,
            show_error=True
        )
    
    if __name__ == '__main__':
        main()
        
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("\n📦 Please install browser-use-webui dependencies:")
    print("   cd browser-use-webui")
    print("   pip install -r requirements.txt")
    print("   playwright install chromium")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
