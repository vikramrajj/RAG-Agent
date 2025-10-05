class RAGAssistant {
    constructor() {
        this.currentTool = 'chat';
        this.isProcessing = false;
        this.typingIndicator = null;
        this.apiEndpoints = {
            chat: '/chat',
            search: '/search',
            shop: '/shop',
            open: '/open',
            outlook: '/fallback/outlook'
        };
        this.setupElements();
        this.setupEventListeners();
        this.checkAgentStatus();
        this.setupWebSocket();
        this.initializeUI();
    }

    setupElements() {
        this.elements = {
            messages: document.getElementById('messages'),
            input: document.getElementById('userInput'),
            sendBtn: document.getElementById('sendBtn'),
            toolButtons: document.querySelectorAll('.quick-action-btn'),
            featureCards: document.querySelectorAll('.feature-card'),
            toolActions: document.getElementById('toolActions'),
            status: document.getElementById('agentStatus')
        };
    }

    setupEventListeners() {
        // Tool button listeners
        this.elements.toolButtons.forEach(btn => {
            btn.addEventListener('click', () => this.switchTool(btn.dataset.tool));
        });

        // Feature card listeners
        this.elements.featureCards.forEach(card => {
            card.addEventListener('click', () => {
                const action = card.dataset.action;
                this.switchTool(action);
                this.activateFeatureCard(card);
            });
        });

        // Chat interface listeners
        this.elements.sendBtn.addEventListener('click', () => this.handleMessage());
        this.elements.input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.handleMessage();
            }
        });
    }

    async checkAgentStatus() {
        try {
            const response = await fetch('/health');
            const status = await response.json();
            this.updateStatus(status.status === 'healthy');
        } catch (error) {
            this.updateStatus(false);
            console.error('Agent status check failed:', error);
        }
    }

    updateStatus(active, customText = null) {
        const statusEl = this.elements.status;
        let statusClass, statusText;

        if (customText) {
            statusClass = 'connecting';
            statusText = customText;
        } else if (active) {
            statusClass = 'active';
            statusText = 'Agent Ready';
        } else {
            statusClass = 'inactive';
            statusText = 'Agent Offline';
        }

        statusEl.className = `status-indicator ${statusClass}`;
        statusEl.querySelector('.status-text').textContent = statusText;
    }

    async switchTool(toolName) {
        this.currentTool = toolName;
        this.elements.toolButtons.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tool === toolName);
        });

        // Get tool-specific actions
        const actions = await this.getToolActions(toolName);
        this.updateToolActions(actions);
    }

    async getToolActions(tool) {
        try {
            const response = await fetch(`${this.apiEndpoints.tools}/${tool}/actions`);
            return await response.json();
        } catch (error) {
            console.error(`Failed to get actions for ${tool}:`, error);
            return [];
        }
    }

    updateToolActions(actions) {
        const actionsHtml = actions.map(action => `
            <button class="tool-action" data-action="${action.id}">
                ${action.icon} ${action.name}
            </button>
        `).join('');
        this.elements.toolActions.innerHTML = actionsHtml;
    }

    setupWebSocket() {
        try {
            this.ws = new WebSocket(`ws://${window.location.host}/chat/ws`);
            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleResponse(data);
            };
            this.ws.onopen = () => {
                this.updateStatus(true);
                console.log('WebSocket connected');
            };
            this.ws.onclose = () => {
                this.updateStatus(false);
                console.log('WebSocket disconnected, retrying in 5s...');
                setTimeout(() => this.setupWebSocket(), 5000);
            };
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateStatus(false);
            };
        } catch (error) {
            console.error('Failed to setup WebSocket:', error);
            this.updateStatus(false);
        }
    }

    async handleMessage() {
        if (this.isProcessing) return;

        const message = this.elements.input.value.trim();
        if (!message) return;

        this.addMessage(message, 'user');
        this.elements.input.value = '';
        this.setProcessingState(true);

        try {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify({
                    message,
                    tool: this.currentTool,
                    action: this.currentAction
                }));
            } else {
                // Fallback to HTTP if WebSocket is not available
                await this.sendHTTPRequest(message);
            }
        } catch (error) {
            console.error('Error sending message:', error);
            this.addMessage('Sorry, there was an error processing your request.', 'assistant');
            this.showToast('Error sending message', 'error');
        } finally {
            this.setProcessingState(false);
        }
    }

    async sendHTTPRequest(message) {
        try {
            const endpoint = this.apiEndpoints[this.currentTool] || this.apiEndpoints.chat;
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message,
                    tool: this.currentTool,
                    action: this.currentAction,
                    context: this.getMessageContext()
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();

            if (result.error) {
                throw new Error(result.error);
            }

            // Handle different response types
            if (result.type && result.content) {
                this.handleTypedResponse(result);
            } else if (result.response) {
                this.addMessage(result.response, 'assistant');
            }

            if (result.actions) {
                this.updateToolActions(result.actions);
            }
        } catch (error) {
            console.error('Message handling failed:', error);
            this.addMessage(`Error: ${error.message}`, 'assistant');
        }
    }

    getMessageContext() {
        // Get last 10 messages for context
        const messages = Array.from(this.elements.messages.children);
        return messages.slice(-10).map(msg => ({
            role: msg.classList.contains('user-message') ? 'user' : 'assistant',
            content: msg.textContent
        }));
    }

    addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', `${sender}-message`);

        if (sender === 'assistant') {
            messageDiv.innerHTML = `<strong>Agent:</strong> ${text}<div class="timestamp">${new Date().toLocaleTimeString()}</div>`;
        } else {
            messageDiv.innerHTML = `<strong>You:</strong> ${text}<div class="timestamp">${new Date().toLocaleTimeString()}</div>`;
        }

        this.elements.messages.appendChild(messageDiv);
        this.elements.messages.scrollTop = this.elements.messages.scrollHeight;
    }

    activateFeatureCard(card) {
        // Remove active state from all cards
        this.elements.featureCards.forEach(c => c.classList.remove('active'));
        // Add active state to clicked card
        card.classList.add('active');

        // Visual feedback
        card.style.transform = 'scale(0.98)';
        setTimeout(() => {
            card.style.transform = '';
        }, 150);
    }

    handleResponse(data) {
        // Handle the response from the WebSocket
        if (data.type === 'message') {
            this.addMessage(data.payload, 'assistant');
        } else if (data.type === 'actions') {
            this.updateToolActions(data.payload);
        }
    }

    handleTypedResponse(result) {
        const { type, content, metadata } = result;

        switch (type) {
            case 'browser_search':
                this.displaySearchResults(content);
                break;
            case 'browser_shopping':
                this.displayShoppingResults(content);
                break;
            case 'browser_open':
                this.displayOpenResult(content, metadata);
                break;
            default:
                this.addMessage(content, 'assistant');
        }
    }

    displaySearchResults(results) {
        if (!results || results.length === 0) {
            this.addMessage('No search results found.', 'assistant');
            return;
        }

        let html = '<div class="search-results">';
        html += '<h4>🔍 Search Results:</h4>';

        results.slice(0, 5).forEach(result => {
            html += `
                <div class="result-item">
                    <h4>${result.title || 'Untitled'}</h4>
                    <p>${result.description || result.snippet || 'No description available'}</p>
                    <a href="${result.url || '#'}" target="_blank" class="result-link">${result.url || ''}</a>
                </div>
            `;
        });

        html += '</div>';

        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', 'assistant-message');
        messageDiv.innerHTML = html;
        this.elements.messages.appendChild(messageDiv);
        this.elements.messages.scrollTop = this.elements.messages.scrollHeight;
    }

    displayShoppingResults(results) {
        if (!results || results.length === 0) {
            this.addMessage('No shopping results found.', 'assistant');
            return;
        }

        let html = '<div class="search-results">';
        html += '<h4>🛒 Shopping Results:</h4>';

        results.slice(0, 4).forEach(product => {
            html += `
                <div class="result-item">
                    <h4>${product.title || product.name || 'Product'}</h4>
                    <p><strong>Price:</strong> ${product.price || 'Price not available'}</p>
                    <p>${product.description || product.snippet || 'No description available'}</p>
                    <a href="${product.url || product.link || '#'}" target="_blank" class="result-link">View Product</a>
                </div>
            `;
        });

        html += '</div>';

        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', 'assistant-message');
        messageDiv.innerHTML = html;
        this.elements.messages.appendChild(messageDiv);
        this.elements.messages.scrollTop = this.elements.messages.scrollHeight;
    }

    displayOpenResult(content, metadata) {
        const url = metadata?.url || 'Unknown URL';
        this.addMessage(`✅ Successfully opened: ${url}`, 'assistant');

        if (content && typeof content === 'string' && content.length > 0) {
            this.addMessage(`Page content preview: ${content.substring(0, 200)}...`, 'assistant');
        }
    }

    initializeUI() {
        // Set initial status
        this.updateStatus(false, 'Connecting...');

        // Add welcome message
        setTimeout(() => {
            this.showToast('Welcome to RAG Agent! 🤖', 'success');
        }, 1000);
    }

    showTypingIndicator() {
        if (this.typingIndicator) return;

        this.typingIndicator = document.createElement('div');
        this.typingIndicator.className = 'typing-indicator';
        this.typingIndicator.innerHTML = `
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <span style="margin-left: 8px; color: var(--text-muted);">Agent is thinking...</span>
        `;

        this.elements.messages.appendChild(this.typingIndicator);
        this.elements.messages.scrollTop = this.elements.messages.scrollHeight;

        // Animate in
        setTimeout(() => {
            this.typingIndicator.classList.add('show');
        }, 10);
    }

    hideTypingIndicator() {
        if (this.typingIndicator) {
            this.typingIndicator.remove();
            this.typingIndicator = null;
        }
    }

    showToast(message, type = 'success') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;

        document.body.appendChild(toast);

        // Animate in
        setTimeout(() => {
            toast.classList.add('show');
        }, 10);

        // Auto remove after 3 seconds
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }, 3000);
    }

    setProcessingState(processing) {
        this.isProcessing = processing;

        if (processing) {
            this.elements.sendBtn.disabled = true;
            this.elements.sendBtn.innerHTML = '<span class="loading-spinner"></span>Sending...';
            this.elements.input.disabled = true;
            this.showTypingIndicator();
        } else {
            this.elements.sendBtn.disabled = false;
            this.elements.sendBtn.textContent = 'Send';
            this.elements.input.disabled = false;
            this.hideTypingIndicator();
        }
    }
}

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    new RAGAssistant();
});
