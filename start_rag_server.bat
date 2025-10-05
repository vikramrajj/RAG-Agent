@echo off
title RAG Agent Server
cd /d "C:\Users\vikra\Downloads\RAG Agent"
echo Starting RAG Agent Server...
echo.
echo Server will be available at: http://localhost:8000
echo Press Ctrl+C to stop the server
echo.
"C:\Users\vikra\Downloads\RAG Agent\.venv\Scripts\python.exe" agent_bridge.py
pause