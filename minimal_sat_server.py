"""
Minimal SAT Server for Testing Action Templates
No heavy imports - starts instantly
"""
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from pathlib import Path

# Import ONLY the action sequence manager (no ML libraries)
try:
    from action_sequence_manager import get_sequence_manager
    TEMPLATES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import action_sequence_manager: {e}")
    TEMPLATES_AVAILABLE = False

app = FastAPI(title="Minimal SAT Server", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files if they exist
static_dir = Path("static")
if static_dir.exists():
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    """Serve main index page"""
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return JSONResponse({"message": "SAT Server Running", "templates": TEMPLATES_AVAILABLE})

@app.get("/sat")
async def sat_ui():
    """Serve SAT UI page"""
    if os.path.exists("sat_ui_improved.html"):
        return FileResponse("sat_ui_improved.html")
    elif os.path.exists("sat_ui.html"):
        return FileResponse("sat_ui.html")
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>SAT - Action Template System</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
            .status { padding: 20px; background: #e8f5e9; border-radius: 8px; margin-bottom: 20px; }
            .query-box { width: 100%; padding: 15px; font-size: 16px; border: 2px solid #ddd; border-radius: 8px; }
            button { padding: 15px 30px; font-size: 16px; background: #4CAF50; color: white; border: none; border-radius: 8px; cursor: pointer; }
            button:hover { background: #45a049; }
            .result { margin-top: 20px; padding: 20px; background: #f5f5f5; border-radius: 8px; white-space: pre-wrap; }
        </style>
    </head>
    <body>
        <h1>🚀 SAT - Smart Action Template System</h1>
        <div class="status">
            <h3>✅ Minimal Server Running</h3>
            <p>Action Templates: """ + ("✅ Available" if TEMPLATES_AVAILABLE else "❌ Not loaded") + """</p>
            <p>Status: Testing Mode</p>
        </div>
        
        <h2>Test a Query</h2>
        <input type="text" class="query-box" id="queryInput" placeholder="Try: 'open calculator' or 'google search for python'">
        <br><br>
        <button onclick="processQuery()">Process Query</button>
        
        <div id="result" class="result" style="display:none;"></div>
        
        <script>
            async function processQuery() {
                const query = document.getElementById('queryInput').value;
                const resultDiv = document.getElementById('result');
                
                resultDiv.style.display = 'block';
                resultDiv.textContent = 'Processing...';
                
                try {
                    const response = await fetch('/process', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ query: query })
                    });
                    
                    const data = await response.json();
                    resultDiv.textContent = JSON.stringify(data, null, 2);
                } catch (error) {
                    resultDiv.textContent = 'Error: ' + error.message;
                }
            }
            
            document.getElementById('queryInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') processQuery();
            });
        </script>
    </body>
    </html>
    """)

@app.post("/process")
async def process_query(request: Request):
    """Process query using action templates"""
    try:
        data = await request.json()
        query = data.get("query", "")
        
        if not query:
            return JSONResponse({
                "success": False,
                "error": "No query provided"
            })
        
        if not TEMPLATES_AVAILABLE:
            return JSONResponse({
                "success": False,
                "error": "Action templates not loaded",
                "suggestion": "Run: pip install browser-use windows-use"
            })
        
        # Get the sequence manager
        manager = get_sequence_manager()
        
        # Match template
        template_name = manager.match_template(query)
        
        if not template_name:
            return JSONResponse({
                "success": False,
                "query": query,
                "matched_template": None,
                "message": "No matching template found",
                "available_templates": list(manager.templates.keys())
            })
        
        # Extract variables
        variables = manager.extract_variables(query, template_name)
        
        # Get template info
        template = manager.templates[template_name]
        
        return JSONResponse({
            "success": True,
            "query": query,
            "matched_template": template_name,
            "variables": variables,
            "template_info": {
                "name": template_name,
                "description": template["description"],
                "keywords": template["keywords"],
                "automation_type": template.get("automation_type", template.get("type", "unknown")),
                "steps_count": len(template["steps"])
            },
            "message": f"✅ Matched template: {template_name}",
            "note": "Template matched! Execute via: manager.execute_template()"
        })
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e),
            "type": type(e).__name__
        }, status_code=500)

@app.post("/api/bridge")
async def api_bridge(request: Request):
    """Bridge endpoint for SAT UI compatibility with EXECUTION"""
    try:
        data = await request.json()
        # Support both 'query' and 'message' fields for compatibility
        query = data.get("query") or data.get("message", "")
        mode = data.get("mode", "smart")
        execute = data.get("execute", True)  # Default to executing templates
        
        if not query:
            return JSONResponse({
                "response": "❌ Error: No query provided",
                "success": False
            })
        
        if not TEMPLATES_AVAILABLE:
            return JSONResponse({
                "response": "❌ Error: Action templates not loaded. Please check server logs.",
                "success": False
            })
        
        # Get the sequence manager
        manager = get_sequence_manager()
        
        # Match template
        template_name = manager.match_template(query)
        
        if not template_name:
            return JSONResponse({
                "response": f"❌ No matching template found for: '{query}'\n\nAvailable templates:\n" + 
                           "\n".join([f"• {name}" for name in list(manager.templates.keys())[:10]]),
                "success": False
            })
        
        # Extract variables
        variables = manager.extract_variables(query, template_name)
        
        # Get template info
        template = manager.templates[template_name]
        automation_type = template.get('automation_type', template.get('type', 'unknown'))
        
        # EXECUTE THE TEMPLATE if requested
        execution_result = None
        execution_error = None
        
        if execute:
            try:
                print(f"\n🚀 EXECUTING TEMPLATE: {template_name}")
                print(f"📊 Variables: {variables}")
                print(f"🔧 Type: {automation_type}")
                
                # Execute the template asynchronously
                execution_result = await manager.execute_template(
                    template_name=template_name,
                    variables=variables,
                    automation_type=automation_type
                )
                
                print(f"✅ EXECUTION COMPLETE: {execution_result}")
                
            except Exception as exec_error:
                execution_error = str(exec_error)
                print(f"❌ EXECUTION FAILED: {execution_error}")
        
        # Format response based on execution result
        if execution_result and execution_result.get("success"):
            response_text = f"""✅ Template Executed Successfully: {template_name}

📋 Description: {template['description']}

🔧 Automation Type: {automation_type}

📊 Variables Used:
{chr(10).join([f"• {k}: {v}" for k, v in variables.items()]) if variables else "• None"}

✨ Execution Result:
{execution_result.get('message', 'Action completed successfully!')}

⚡ Steps Executed: {len(template['steps'])}

🎯 Route: {automation_type.upper()}"""
            
        elif execution_error:
            response_text = f"""⚠️ Template Matched but Execution Failed: {template_name}

📋 Description: {template['description']}

🔧 Automation Type: {automation_type}

📊 Variables Extracted:
{chr(10).join([f"• {k}: {v}" for k, v in variables.items()]) if variables else "• None"}

❌ Error: {execution_error}

💡 This may require:
• browser-use installation (for browser templates)
• windows-use installation (for Windows templates)
• Proper permissions to execute actions

Run: pip install browser-use windows-use"""
            
        else:
            # Template matched but not executed (execute=False)
            response_text = f"""✅ Template Matched: {template_name}

📋 Description: {template['description']}

🔧 Automation Type: {automation_type}

📊 Variables Extracted:
{chr(10).join([f"• {k}: {v}" for k, v in variables.items()]) if variables else "• None"}

⚡ Steps to Execute: {len(template['steps'])}

🎯 Keywords: {', '.join(template['keywords'][:5])}

ℹ️ Template ready but not executed (pass execute=true to run)"""
        
        return JSONResponse({
            "response": response_text,
            "success": True,
            "template_name": template_name,
            "variables": variables,
            "mode": "template",
            "route": automation_type,
            "executed": execution_result is not None,
            "execution_success": execution_result.get("success") if execution_result else False
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ API BRIDGE ERROR:\n{error_details}")
        
        return JSONResponse({
            "response": f"❌ Error: {str(e)}\n\nCheck server logs for details.",
            "success": False,
            "error_type": type(e).__name__
        })

@app.get("/templates")
async def list_templates():
    """List all available templates"""
    if not TEMPLATES_AVAILABLE:
        return JSONResponse({
            "success": False,
            "error": "Templates not loaded"
        })
    
    manager = get_sequence_manager()
    
    templates_info = {}
    for name, template in manager.templates.items():
        templates_info[name] = {
            "description": template["description"],
            "keywords": template["keywords"],
            "automation_type": template["automation_type"],
            "variables": template.get("variables", [])
        }
    
    return JSONResponse({
        "success": True,
        "count": len(templates_info),
        "templates": templates_info
    })

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "server": "minimal_sat_server",
        "templates_loaded": TEMPLATES_AVAILABLE,
        "version": "1.0.0"
    })

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 Starting Minimal SAT Server")
    print("="*60)
    print(f"Templates Available: {TEMPLATES_AVAILABLE}")
    print(f"Server URL: http://localhost:8000")
    print(f"SAT UI: http://localhost:8000/sat")
    print(f"API Docs: http://localhost:8000/docs")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
