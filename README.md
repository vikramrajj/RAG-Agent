# RAG Agent - Intelligent Troubleshooting Assistant

A sophisticated Retrieval-Augmented Generation (RAG) agent designed to provide intelligent troubleshooting assistance for Microsoft Office applications. Built with modern Python frameworks and AI technologies, it combines semantic search, natural language processing, and web automation to deliver comprehensive support solutions.

## 🚀 Features

### Core Capabilities
- **Intelligent Troubleshooting**: AI-powered diagnosis and resolution for Office application issues
- **Semantic Search**: Advanced vector-based retrieval using FAISS and sentence transformers
- **Web Automation**: Browser-based task execution with Playwright integration
- **Real-time Chat Interface**: Interactive web-based chat system with streaming responses
- **Multi-modal Support**: Text, voice, and web interaction capabilities

### Technical Features
- **Robust Error Handling**: Comprehensive error management with standardized logging
- **Security-First Design**: Input validation, CSRF protection, and secure credential management
- **Performance Monitoring**: Built-in health checks, metrics collection, and performance tracking
- **Scalable Architecture**: Modular design with configurable components
- **Production Ready**: Comprehensive testing, logging, and monitoring capabilities

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [API Documentation](#api-documentation)
- [Architecture](#architecture)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

## 🛠 Installation

### Prerequisites

- Python 3.8 or higher
- Windows 10/11 (for Office integration)
- Microsoft Office 365 or Office 2019+
- Node.js 16+ (for web UI components)

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd RAG-Agent
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   # Production installation
   pip install -r requirements.txt
   
   # Development installation (includes testing tools)
   pip install -r requirements-dev.txt
   ```

4. **Install Playwright browsers**
   ```bash
   playwright install
   ```

5. **Set up configuration**
   ```bash
   # Copy and edit configuration files
   cp config/app.yaml.example config/app.yaml
   cp .env.example .env
   ```

## 🚀 Quick Start

### 1. Configuration Setup

Create a `.env` file in the project root:

```env
# Flask Configuration
FLASK_SECRET_KEY=your_secure_random_key_here
FLASK_DEBUG=false

# LLM Configuration
OLLAMA_MODEL=llama3
OLLAMA_BASE_URL=http://localhost:11434
LLM_TEMPERATURE=0.1
MAX_TOKENS=500

# RAG Configuration
EMBEDDING_MODEL=all-MiniLM-L6-v2
FAISS_INDEX_PATH=outlook_index.faiss
METADATA_PATH=metadata.json
MIN_RELEVANCE_SCORE=0.3
MAX_RETRIEVAL_RESULTS=5

# Outlook Credentials (for Office integration)
OUTLOOK_EMAIL=your_email@company.com
OUTLOOK_PASSWORD=your_app_specific_password

# Paths
SARA_PATH=C:\Program Files\Microsoft Support and Recovery Assistant\SaRA.exe
DIAGNOSTICS_OUTPUT_DIR=C:\Diagnostics\Outlook
LOG_DIRECTORY=logs

# Performance Settings
MAX_WORKER_THREADS=3
REQUEST_TIMEOUT_SECONDS=60
```

### 2. Initialize the System

```bash
# Generate FAISS index from your troubleshooting data
python rag_loader.py

# Start the application
python agent_bridge.py
```

### 3. Access the Web Interface

Open your browser and navigate to:
- **Main Interface**: http://localhost:5000
- **Health Check**: http://localhost:5000/health
- **API Documentation**: http://localhost:5000/docs

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `FLASK_SECRET_KEY` | Flask secret key for sessions | - | Yes |
| `OLLAMA_MODEL` | Ollama model name | `llama3` | No |
| `OLLAMA_BASE_URL` | Ollama server URL | `http://localhost:11434` | No |
| `EMBEDDING_MODEL` | Sentence transformer model | `all-MiniLM-L6-v2` | No |
| `OUTLOOK_EMAIL` | Outlook email address | - | Yes |
| `OUTLOOK_PASSWORD` | Outlook app password | - | Yes |

### Configuration Files

The system supports multiple configuration files in the `config/` directory:

- `app.yaml` - Main application configuration
- `app.development.yaml` - Development-specific settings
- `app.production.yaml` - Production-specific settings

## 📚 API Documentation

### Core Endpoints

#### Chat Interface
```http
POST /chat
Content-Type: application/json

{
  "message": "Outlook won't open",
  "context": [],
  "browser_mode": false
}
```

#### Web Search
```http
POST /search
Content-Type: application/json

{
  "query": "Outlook error 0x80042108"
}
```

#### Browser Actions
```http
POST /open
Content-Type: application/json

{
  "url": "https://outlook.office365.com"
}
```

#### Diagnostics
```http
POST /diagnostics
Content-Type: application/json

{}
```

### Health Monitoring

#### Basic Health Check
```http
GET /health
```

#### Detailed Health Check
```http
GET /health/detailed
```

#### Readiness Check
```http
GET /health/ready
```

#### Liveness Check
```http
GET /health/live
```

### Response Formats

All API responses follow a consistent format:

```json
{
  "type": "troubleshooting|browser|error",
  "content": "Response content",
  "metadata": {
    "request_id": "uuid",
    "timestamp": "2024-01-01T00:00:00Z",
    "confidence": 0.95,
    "sources": []
  }
}
```

## 🏗 Architecture

### System Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Interface │    │   Agent Bridge  │    │   RAG System    │
│                 │    │                 │    │                 │
│  - Chat UI      │◄──►│  - Flask API    │◄──►│  - Retriever    │
│  - Browser UI   │    │  - Auth/Validation│  │  - Reasoner     │
│  - Admin Panel  │    │  - Rate Limiting │  │  - Loader       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  External Tools │
                       │                 │
                       │  - Outlook      │
                       │  - SaRA         │
                       │  - Web Browsers │
                       └─────────────────┘
```

### Key Modules

- **`agent_bridge.py`** - Main Flask application and API endpoints
- **`retriever.py`** - FAISS-based semantic search and retrieval
- **`reasoner.py`** - LLM-based reasoning and response generation
- **`web_agent.py`** - Browser automation and web interaction
- **`tool_invoker.py`** - System tool execution and management
- **`config.py`** - Configuration management and validation
- **`security_utils.py`** - Security utilities and input validation
- **`standardized_error_handler.py`** - Unified error handling system

## 🧪 Development

### Development Setup

1. **Install development dependencies**
   ```bash
   pip install -r requirements-dev.txt
   ```

2. **Set up pre-commit hooks**
   ```bash
   pre-commit install
   ```

3. **Run in development mode**
   ```bash
   export FLASK_DEBUG=true
   python agent_bridge.py
   ```

### Code Quality

The project uses several tools to maintain code quality:

- **Black** - Code formatting
- **Flake8** - Linting
- **MyPy** - Type checking
- **Pytest** - Testing framework
- **Pre-commit** - Git hooks

### Running Tests

```bash
# Run all tests
python run_tests.py

# Run specific test categories
python run_tests.py --individual
python run_tests.py --coverage
python run_tests.py --performance

# Run with coverage report
python -m pytest --cov=. --cov-report=html
```

## 🚀 Deployment

### Docker Deployment

```bash
# Build the image
docker build -t rag-agent .

# Run the container
docker run -p 5000:5000 -e FLASK_SECRET_KEY=your_key rag-agent
```

### Production Configuration

1. **Set production environment variables**
2. **Configure reverse proxy (nginx/Apache)**
3. **Set up SSL/TLS certificates**
4. **Configure monitoring and logging**
5. **Set up backup procedures**

### Environment-Specific Configurations

- **Development**: `config/app.development.yaml`
- **Production**: `config/app.production.yaml`
- **Testing**: `config/app.testing.yaml`

## 📊 Monitoring and Logging

### Health Checks

The system provides comprehensive health monitoring:

- **System Resources**: CPU, memory, disk usage
- **Database Status**: FAISS index and metadata accessibility
- **External Services**: Ollama, Outlook connectivity
- **Application Metrics**: Request rates, error rates, response times

### Logging

Structured logging with multiple levels:

- **Application Logs**: `logs/rag_agent.log`
- **Error Logs**: `logs/rag_agent_errors.log`
- **Performance Logs**: `logs/rag_agent_performance.log`
- **Security Logs**: `logs/rag_agent_security.log`

### Metrics Collection

- Request/response times
- Error rates and types
- Cache hit/miss ratios
- Resource utilization
- User interaction patterns

## 🔒 Security

### Security Features

- **Input Validation**: Comprehensive sanitization and validation
- **CSRF Protection**: Token-based CSRF prevention
- **Rate Limiting**: Request rate limiting per IP/user
- **Secure Headers**: Security headers on all responses
- **Credential Management**: Secure storage and handling of credentials

### Security Best Practices

- Use strong, unique Flask secret keys
- Enable HTTPS in production
- Regularly update dependencies
- Monitor security logs
- Implement proper access controls

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

### Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Write comprehensive docstrings
- Include unit tests for new features
- Update documentation as needed

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Getting Help

- **Documentation**: Check this README and inline code documentation
- **Issues**: Report bugs and request features via GitHub Issues
- **Discussions**: Join community discussions in GitHub Discussions

### Troubleshooting

Common issues and solutions:

1. **Ollama Connection Issues**
   - Ensure Ollama is running on the correct port
   - Check firewall settings
   - Verify model availability

2. **Outlook Integration Problems**
   - Verify credentials in `.env` file
   - Check Outlook app password setup
   - Ensure Office applications are installed

3. **FAISS Index Issues**
   - Regenerate index with `python rag_loader.py`
   - Check file permissions
   - Verify embedding model compatibility

### Performance Optimization

- Adjust `MAX_WORKER_THREADS` based on system resources
- Configure cache sizes appropriately
- Monitor memory usage with large datasets
- Use GPU-accelerated models when available

## 🔄 Version History

- **v1.0.0** - Initial release with core RAG functionality
- **v1.1.0** - Added web automation and browser integration
- **v1.2.0** - Enhanced security and error handling
- **v1.3.0** - Performance improvements and monitoring
- **v2.0.0** - Complete architecture overhaul and standardization

---
## 🎬 Demo Video

[![YouTube](https://img.shields.io/badge/YouTube-Watch_Demo-red?style=for-the-badge&logo=youtube)](https://www.youtube.com/watch?v=VwiSWpLlWq8)

[![Demo Thumbnail](https://img.youtube.com/vi/VwiSWpLlWq8/maxresdefault.jpg)](https://www.youtube.com/watch?v=VwiSWpLlWq8)

**Built with ❤️ for intelligent troubleshooting assistance**
