# SAT UI Improved - Model Selector Patch
# This file contains all the code snippets to add to sat_ui_improved.html

## PART 1: CSS ADDITIONS (Add after line ~600 in <style> section, before closing </style>)

```css
/* ============================================
   MODEL SELECTOR STYLING
   ============================================ */
.model-selector-container {
    display: flex;
    gap: 0.75rem;
    align-items: center;
    padding: 0.75rem 1.5rem;
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border);
    flex-wrap: wrap;
}

.model-selector-label {
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--text-secondary);
    display: flex;
    align-items: center;
    gap: 0.375rem;
}

.model-select {
    padding: 0.5rem 2.5rem 0.5rem 0.875rem;
    background: var(--bg-primary);
    border: 1px solid var(--border);
    border-radius: 8px;
    color: var(--text-primary);
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: var(--transition);
    appearance: none;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%2364748b' d='M6 8L2 4h8z'/%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 0.625rem center;
    background-size: 12px;
    min-width: 180px;
}

.model-select:hover {
    background: var(--slate-100);
    border-color: var(--slate-400);
}

.model-select:focus {
    outline: none;
    border-color: var(--accent-blue);
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.model-select option {
    background: var(--white);
    color: var(--text-primary);
    padding: 0.5rem;
}

.model-select optgroup {
    font-weight: 600;
    color: var(--text-secondary);
}

.model-status {
    font-size: 0.75rem;
    padding: 0.375rem 0.75rem;
    border-radius: 6px;
    background: var(--slate-100);
    color: var(--text-secondary);
    font-weight: 500;
    transition: var(--transition);
}

.model-status.active {
    background: #d1fae5;
    color: #065f46;
}

.model-status.loading {
    background: #dbeafe;
    color: #1e40af;
    animation: pulse 1.5s infinite;
}

.model-status.error {
    background: #fee2e2;
    color: #991b1b;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.6; }
}

/* Routing Indicator Badge */
.routing-indicator {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    font-size: 0.7rem;
    padding: 0.25rem 0.625rem;
    border-radius: 12px;
    background: var(--slate-100);
    color: var(--text-secondary);
    font-weight: 600;
    letter-spacing: 0.025rem;
    text-transform: uppercase;
}

.routing-indicator.mistral {
    background: #dbeafe;
    color: #1e40af;
}

.routing-indicator.rag_outlook {
    background: #fef3c7;
    color: #92400e;
}

.routing-indicator.browser_use,
.routing-indicator.browser_automation {
    background: #d1fae5;
    color: #065f46;
}

/* Add to message header for routing display */
.message-header .routing-indicator {
    margin-left: auto;
}

/* Smart Routing Toggle */
.smart-routing-toggle {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.75rem;
    color: var(--text-secondary);
    cursor: pointer;
    padding: 0.375rem 0.75rem;
    border-radius: 6px;
    transition: var(--transition);
}

.smart-routing-toggle:hover {
    background: var(--slate-100);
}

.smart-routing-toggle input[type="checkbox"] {
    width: 16px;
    height: 16px;
    cursor: pointer;
}

/* Responsive adjustments */
@media (max-width: 768px) {
    .model-selector-container {
        flex-direction: column;
        align-items: stretch;
        gap: 0.5rem;
        padding: 0.75rem 1rem;
    }
    
    .model-select {
        width: 100%;
    }
    
    .model-status,
    .smart-routing-toggle {
        width: 100%;
        text-align: center;
    }
}
```

## PART 2: HTML STRUCTURE (Add after .app-header section, before the main chat area)

Find the line with `<div class="app-header">` and after its closing `</div>`, add:

```html
<!-- ============================================
     MODEL SELECTOR & SMART ROUTING
     ============================================ -->
<div class="model-selector-container">
    <div class="model-selector-label">
        🤖 AI Model:
    </div>
    <select class="model-select" id="modelSelect" onchange="handleModelChange()">
        <option value="">Loading models...</option>
    </select>
    <div class="model-status" id="modelStatus">
        🔄 Loading...
    </div>
    <label class="smart-routing-toggle" title="Automatically route queries to the best AI system">
        <input type="checkbox" id="smartRoutingToggle" checked onchange="toggleSmartRouting()">
        <span>🔀 Smart Routing</span>
    </label>
</div>
```

## PART 3: JAVASCRIPT - MODEL MANAGEMENT (Add in <script> section, after state management)

```javascript
// ============================================
// AI MODEL MANAGEMENT
// ============================================
let availableModels = [];
let downloadedModels = [];
let currentModel = null;
let modelsData = {};
let smartRoutingEnabled = true;

/**
 * Load available AI models from the API
 */
async function loadModels() {
    try {
        const response = await fetch('/api/models');
        if (!response.ok) {
            throw new Error('Failed to load models');
        }

        modelsData = await response.json();
        availableModels = modelsData.all_models || [];
        downloadedModels = modelsData.downloaded_models || [];
        currentModel = modelsData.current_model || null;

        // Populate dropdown
        populateModelSelect();

        // Update status
        if (currentModel) {
            updateModelStatus('active', `✅ ${currentModel.display_name || currentModel.name}`);
        } else {
            updateModelStatus('inactive', '⚠️ No model loaded');
        }

        console.log('Models loaded:', { available: availableModels.length, downloaded: downloadedModels.length });

    } catch (error) {
        console.error('Error loading models:', error);
        const select = document.getElementById('modelSelect');
        select.innerHTML = '<option value="mistral">Mistral (Default)</option>';
        updateModelStatus('error', '❌ Error loading models');
    }
}

/**
 * Populate the model selector dropdown
 */
function populateModelSelect() {
    const select = document.getElementById('modelSelect');
    select.innerHTML = '';

    if (availableModels.length === 0) {
        select.innerHTML = '<option value="mistral">Mistral (Default)</option>';
        return;
    }

    // Add downloaded models first (ready to use)
    if (downloadedModels.length > 0) {
        const downloadedGroup = document.createElement('optgroup');
        downloadedGroup.label = '✅ Ready to Use';
        
        downloadedModels.forEach(model => {
            const option = document.createElement('option');
            option.value = model.name;
            
            // Format display text
            const displayName = model.display_name || model.name;
            const size = model.size ? ` (${model.size})` : '';
            option.textContent = `${displayName}${size}`;
            
            // Select current model
            if (currentModel && currentModel.name === model.name) {
                option.selected = true;
            }
            
            downloadedGroup.appendChild(option);
        });
        
        select.appendChild(downloadedGroup);
    }

    // Add available but not downloaded models
    const notDownloaded = availableModels.filter(model =>
        !downloadedModels.find(dm => dm.name === model.name)
    );

    if (notDownloaded.length > 0) {
        const availableGroup = document.createElement('optgroup');
        availableGroup.label = '⬇️ Available to Download';
        
        notDownloaded.forEach(model => {
            const option = document.createElement('option');
            option.value = model.name;
            
            const displayName = model.display_name || model.name;
            const size = model.size ? ` (${model.size})` : '';
            option.textContent = `${displayName}${size} - Not Downloaded`;
            
            availableGroup.appendChild(option);
        });
        
        select.appendChild(availableGroup);
    }
}

/**
 * Update the model status indicator
 */
function updateModelStatus(status, text) {
    const statusElement = document.getElementById('modelStatus');
    if (!statusElement) return;
    
    statusElement.textContent = text;
    statusElement.className = 'model-status ' + status;
}

/**
 * Handle model selection change
 */
async function handleModelChange() {
    const select = document.getElementById('modelSelect');
    const modelName = select.value;

    if (!modelName) return;

    // Check if model is downloaded
    const isDownloaded = downloadedModels.find(m => m.name === modelName);

    if (!isDownloaded) {
        // Offer to download
        const confirmDownload = confirm(
            `Model "${modelName}" needs to be downloaded first.\n\n` +
            `This may take several minutes depending on the model size.\n\n` +
            `Download now?`
        );
        
        if (confirmDownload) {
            await downloadModel(modelName);
        } else {
            // Revert selection to current model
            if (currentModel) {
                select.value = currentModel.name;
            }
        }
        return;
    }

    // Load the model
    await loadModel(modelName);
}

/**
 * Load a specific AI model
 */
async function loadModel(modelName) {
    try {
        updateModelStatus('loading', '🔄 Loading...');
        showToast(`🔄 Loading ${modelName}...`, 'info');
        
        const response = await fetch('/api/models/load', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ model_name: modelName })
        });

        if (!response.ok) {
            throw new Error('Failed to load model');
        }

        const result = await response.json();
        
        if (result.success) {
            currentModel = result.model;
            const displayName = result.model.display_name || modelName;
            updateModelStatus('active', `✅ ${displayName}`);
            showToast(`✅ ${displayName} loaded successfully!`, 'success');
            console.log('Model loaded:', currentModel);
        } else {
            throw new Error(result.error || 'Failed to load model');
        }

    } catch (error) {
        console.error('Error loading model:', error);
        updateModelStatus('error', '❌ Load failed');
        showToast(`❌ Failed to load model: ${error.message}`, 'error');
        
        // Revert to previous model
        if (currentModel) {
            document.getElementById('modelSelect').value = currentModel.name;
        }
    }
}

/**
 * Download a model from Ollama
 */
async function downloadModel(modelName) {
    try {
        updateModelStatus('loading', '⬇️ Downloading...');
        showToast(`⬇️ Downloading ${modelName}... This may take several minutes.`, 'info');
        
        const response = await fetch('/api/models/download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ model_name: modelName })
        });

        if (!response.ok) {
            throw new Error('Download request failed');
        }

        const result = await response.json();
        
        if (result.success) {
            showToast(`✅ ${modelName} downloaded successfully!`, 'success');
            
            // Reload models list
            await loadModels();
            
            // Auto-load the newly downloaded model
            await loadModel(modelName);
        } else {
            throw new Error(result.error || 'Download failed');
        }

    } catch (error) {
        console.error('Error downloading model:', error);
        updateModelStatus('error', '❌ Download failed');
        showToast(`❌ Download failed: ${error.message}`, 'error');
    }
}

/**
 * Toggle smart routing on/off
 */
function toggleSmartRouting() {
    const checkbox = document.getElementById('smartRoutingToggle');
    smartRoutingEnabled = checkbox.checked;
    
    const status = smartRoutingEnabled ? 'enabled' : 'disabled';
    showToast(`🔀 Smart routing ${status}`, 'info');
    
    console.log('Smart routing:', smartRoutingEnabled);
}

/**
 * Get the currently selected model
 */
function getSelectedModel() {
    const select = document.getElementById('modelSelect');
    return select ? select.value : 'mistral';
}
```

## PART 4: UPDATE sendMessage() FUNCTION

Find the `sendMessage()` function and update the fetch call to include model and smart_routing:

```javascript
// In sendMessage() function, find the fetch call and update it to:

const response = await fetch('/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        message: message,
        context: state.messages.slice(-10),
        model: getSelectedModel(),           // ADD THIS LINE
        smart_routing: smartRoutingEnabled   // ADD THIS LINE
    })
});
```

## PART 5: UPDATE addMessage() FUNCTION TO SHOW ROUTING

Find the `addMessage()` function and add routing indicator support:

```javascript
// In addMessage() function, after creating messageHeader, add:

function addMessage(sender, content, metadata = {}) {
    // ... existing code for creating messageDiv, messageHeader, etc. ...
    
    // ADD THIS BLOCK: Show routing indicator
    if (metadata && metadata.route) {
        const routeIndicator = document.createElement('span');
        routeIndicator.className = `routing-indicator ${metadata.route}`;
        
        const routeLabels = {
            'mistral': '🤖 Mistral',
            'rag_outlook': '📧 RAG + Reasoner',
            'browser_use': '🌐 Browser',
            'browser_automation': '🌐 Browser'
        };
        
        routeIndicator.textContent = routeLabels[metadata.route] || metadata.route;
        routeIndicator.title = `Routed to: ${routeLabels[metadata.route] || metadata.route}`;
        
        messageHeader.appendChild(routeIndicator);
    }
    
    // ... rest of existing code ...
}
```

## PART 6: UPDATE initializeApp() FUNCTION

Add model loading to initialization:

```javascript
function initializeApp() {
    // ... existing code ...
    
    // ADD THIS: Load available AI models
    loadModels();
    
    // ADD THIS: Set up smart routing toggle state
    const smartRoutingToggle = document.getElementById('smartRoutingToggle');
    if (smartRoutingToggle) {
        smartRoutingToggle.checked = smartRoutingEnabled;
    }
    
    // ... rest of initialization ...
}
```

## PART 7: HANDLE RESPONSE METADATA

In your message handling code where you process the API response, make sure to pass metadata:

```javascript
// When handling the response from /chat endpoint:
const data = await response.json();

// ADD THIS: Extract routing information
const metadata = {
    route: data.route || data.type,
    model: data.model,
    confidence: data.confidence,
    ...data.metadata
};

// Pass metadata to addMessage
addMessage('agent', data.content || data.response, metadata);
```

## INSTALLATION CHECKLIST

- [ ] Add Part 1 (CSS) to the `<style>` section
- [ ] Add Part 2 (HTML) after the app-header
- [ ] Add Part 3 (JavaScript) to the `<script>` section
- [ ] Update Part 4 (sendMessage function)
- [ ] Update Part 5 (addMessage function)
- [ ] Update Part 6 (initializeApp function)
- [ ] Update Part 7 (Response handling)
- [ ] Test model selector appears
- [ ] Test model loading
- [ ] Test smart routing indicators

## TESTING

1. **Model Selector Test:**
   - Open UI, verify dropdown appears
   - Select "Mistral" - should show ✅ Active
   - Try selecting undownloaded model - should prompt to download

2. **Smart Routing Test:**
   - Send: "My Outlook is not syncing" → Should show 📧 RAG + Reasoner
   - Send: "Find cheap flights" → Should show 🌐 Browser
   - Send: "What is 2+2?" → Should show 🤖 Mistral

3. **Toggle Test:**
   - Uncheck "Smart Routing"
   - All messages should route to Mistral only
   - Re-check to re-enable smart routing
