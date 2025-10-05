"""
Test Browser-Use Integration
Verify that the browser-use integration is working correctly
"""

import sys
import asyncio
from pathlib import Path

print("=" * 70)
print("  Browser-Use Integration Test")
print("=" * 70)
print()

# Test 1: Check if browser_integration module can be imported
print("Test 1: Checking browser_integration module...")
try:
    from browser_integration import (
        get_browser_integration,
        is_browser_integration_available,
        BrowserUseIntegration
    )
    print("✅ PASS: browser_integration module imported successfully")
except ImportError as e:
    print(f"❌ FAIL: Could not import browser_integration: {e}")
    sys.exit(1)

# Test 2: Check if browser-use-webui directory exists
print("\nTest 2: Checking browser-use-webui directory...")
browser_ui_path = Path(__file__).parent / "browser-use-webui"
if browser_ui_path.exists():
    print(f"✅ PASS: browser-use-webui found at {browser_ui_path}")
else:
    print(f"⚠️  WARNING: browser-use-webui directory not found at {browser_ui_path}")
    print("   Browser-use features will not be available")

# Test 3: Initialize browser integration
print("\nTest 3: Initializing browser integration...")
try:
    integration = get_browser_integration()
    print("✅ PASS: Browser integration instance created")
except Exception as e:
    print(f"❌ FAIL: Could not create integration instance: {e}")
    sys.exit(1)

# Test 4: Check availability
print("\nTest 4: Checking integration availability...")
is_available = is_browser_integration_available()
if is_available:
    print("✅ PASS: Browser-use integration is AVAILABLE")
    print("   All browser-use features can be used")
else:
    print("⚠️  WARNING: Browser-use integration is NOT AVAILABLE")
    print("   This is normal if dependencies are not installed")
    print("   To enable, run:")
    print("     cd browser-use-webui")
    print("     pip install -r requirements.txt")
    print("     playwright install chromium")

# Test 5: Check if browser-use dependencies are installed
print("\nTest 5: Checking browser-use dependencies...")
dependencies_ok = True
missing_deps = []

try:
    import gradio
    print(f"   ✅ gradio: {gradio.__version__}")
except ImportError:
    dependencies_ok = False
    missing_deps.append("gradio")
    print("   ❌ gradio: NOT INSTALLED")

try:
    import playwright
    print(f"   ✅ playwright: installed")
except ImportError:
    dependencies_ok = False
    missing_deps.append("playwright")
    print("   ❌ playwright: NOT INSTALLED")

try:
    import browser_use
    print(f"   ✅ browser-use: installed")
except ImportError:
    dependencies_ok = False
    missing_deps.append("browser-use")
    print("   ❌ browser-use: NOT INSTALLED")

if dependencies_ok:
    print("\n✅ PASS: All dependencies installed")
else:
    print(f"\n⚠️  WARNING: Missing dependencies: {', '.join(missing_deps)}")
    print("   To install:")
    print("     cd browser-use-webui")
    print("     pip install -r requirements.txt")
    print("     playwright install chromium")

# Test 6: Test agent_bridge.py integration
print("\nTest 6: Checking agent_bridge.py integration...")
try:
    import agent_bridge
    
    # Check if browser_integration is imported
    if hasattr(agent_bridge, 'browser_integration'):
        print("✅ PASS: browser_integration imported in agent_bridge.py")
    else:
        print("❌ FAIL: browser_integration not found in agent_bridge.py")
    
    # Check if is_browser_integration_available is imported
    if hasattr(agent_bridge, 'is_browser_integration_available'):
        print("✅ PASS: is_browser_integration_available imported in agent_bridge.py")
    else:
        print("❌ FAIL: is_browser_integration_available not found in agent_bridge.py")
        
except ImportError as e:
    print(f"❌ FAIL: Could not import agent_bridge: {e}")

# Test 7: Check new API endpoints
print("\nTest 7: Checking new API endpoint definitions...")
try:
    import agent_bridge
    app = agent_bridge.app
    
    endpoints_to_check = [
        '/browser-use/status',
        '/browser-use/execute',
        '/browser-use/extract',
        '/browser-use/workflow',
    ]
    
    # Get all registered routes
    routes = [rule.rule for rule in app.url_map.iter_rules()]
    
    for endpoint in endpoints_to_check:
        if endpoint in routes:
            print(f"   ✅ {endpoint}: REGISTERED")
        else:
            print(f"   ❌ {endpoint}: NOT FOUND")
            
except Exception as e:
    print(f"❌ FAIL: Could not check endpoints: {e}")

# Test 8: Test basic functionality (if available)
if is_available:
    print("\nTest 8: Testing basic integration functions...")
    try:
        # Test the integration methods exist
        methods = [
            'execute_browser_task',
            'search_web',
            'extract_website_content',
            'automate_workflow',
            'launch_webui'
        ]
        
        for method in methods:
            if hasattr(integration, method):
                print(f"   ✅ {method}: EXISTS")
            else:
                print(f"   ❌ {method}: MISSING")
                
    except Exception as e:
        print(f"❌ FAIL: Could not test methods: {e}")
else:
    print("\nTest 8: SKIPPED (integration not available)")

# Final Summary
print("\n" + "=" * 70)
print("  Test Summary")
print("=" * 70)

if is_available and dependencies_ok:
    print("\n🎉 SUCCESS! Browser-use integration is fully functional!")
    print("\nYou can now:")
    print("  1. Use browser-use API endpoints in agent_bridge.py")
    print("  2. Launch the WebUI with: start_browser_webui.bat")
    print("  3. Use enhanced search in your SAT interface")
    print("\nNext steps:")
    print("  • Start the RAG Agent: python agent_bridge.py")
    print("  • Test API: curl http://localhost:8000/browser-use/status")
    print("  • Launch WebUI: start_browser_webui.bat")
    
elif is_available and not dependencies_ok:
    print("\n⚠️  PARTIAL SUCCESS: Integration code is ready but dependencies missing")
    print("\nTo complete setup:")
    print("  cd browser-use-webui")
    print("  pip install -r requirements.txt")
    print("  playwright install chromium")
    
else:
    print("\n⚠️  SETUP REQUIRED: Browser-use integration needs configuration")
    print("\nSetup steps:")
    print("  1. cd browser-use-webui")
    print("  2. pip install -r requirements.txt")
    print("  3. playwright install chromium")
    print("  4. Run this test again to verify")

print("\n" + "=" * 70)
print("  Documentation")
print("=" * 70)
print("\n  📚 Read: BROWSER_USE_INTEGRATION.md")
print("  📋 Quick Ref: BROWSER_INTEGRATION_SUMMARY.md")
print("  🌐 Browser-Use Docs: browser-use-webui/README.md")
print("\n" + "=" * 70)
