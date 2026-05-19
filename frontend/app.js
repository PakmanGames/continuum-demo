const API_BASE = 'http://localhost:5000';

// Logging functions
function log(message, type = 'info') {
    const logContainer = document.getElementById('response-log');
    const timestamp = new Date().toLocaleTimeString();
    const entry = document.createElement('p');
    entry.className = `log-entry ${type}`;
    entry.innerHTML = `<span class="timestamp">[${timestamp}]</span>${message}`;
    
    if (logContainer.firstChild && logContainer.firstChild.textContent === 'No requests yet...') {
        logContainer.innerHTML = '';
    }
    
    logContainer.insertBefore(entry, logContainer.firstChild);
}

// Check backend health
async function checkHealth() {
    const statusElement = document.getElementById('backend-status');
    try {
        const response = await fetch(`${API_BASE}/health`);
        const data = await response.json();
        
        if (data.status === 'healthy') {
            statusElement.textContent = '✅ Healthy';
            statusElement.className = 'status-indicator healthy';
            log('Backend health check: HEALTHY', 'success');
        } else {
            statusElement.textContent = '❌ Unhealthy';
            statusElement.className = 'status-indicator unhealthy';
            log('Backend health check: UNHEALTHY', 'error');
        }
    } catch (error) {
        statusElement.textContent = '❌ Offline';
        statusElement.className = 'status-indicator unhealthy';
        log(`Backend health check failed: ${error.message}`, 'error');
    }
}

// Load users
async function loadUsers() {
    const container = document.getElementById('users-container');
    try {
        const response = await fetch(`${API_BASE}/users`);
        const users = await response.json();
        
        if (users.length === 0) {
            container.innerHTML = '<p>No users found.</p>';
            return;
        }
        
        container.innerHTML = users.map(user => `
            <div class="user-card">
                <h3>${user.name}</h3>
                <p>📧 ${user.email}</p>
                <p>🆔 ID: ${user.id}</p>
            </div>
        `).join('');
        
        log(`Loaded ${users.length} users successfully`, 'success');
    } catch (error) {
        container.innerHTML = '<p>Error loading users.</p>';
        log(`Failed to load users: ${error.message}`, 'error');
    }
}

// Add a new user
async function addUser() {
    const name = document.getElementById('user-name').value.trim();
    const email = document.getElementById('user-email').value.trim();
    
    if (!name || !email) {
        log('Please enter both name and email', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/users`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name, email })
        });
        
        if (response.ok) {
            const user = await response.json();
            log(`✅ Added user: ${user.name} (${user.email})`, 'success');
            
            // Clear form
            document.getElementById('user-name').value = '';
            document.getElementById('user-email').value = '';
            
            // Reload users
            loadUsers();
        } else {
            const error = await response.json();
            log(`❌ Failed to add user: ${error.error}`, 'error');
        }
    } catch (error) {
        log(`❌ Error adding user: ${error.message}`, 'error');
    }
}

// Trigger crash endpoint (division by zero)
async function triggerCrash() {
    log('🚨 Sending crash request to /crash endpoint with value=0...', 'info');
    
    try {
        const response = await fetch(`${API_BASE}/crash?value=0`);
        
        if (response.ok) {
            const data = await response.json();
            log('🤔 Unexpected: Server returned a response (should have crashed)', 'info');
        }
    } catch (error) {
        log(`💥 CRASH TRIGGERED! Backend failed with: ${error.message}`, 'error');
        log('⚠️ The backend container may have crashed. Check with: docker ps', 'error');
        setTimeout(checkHealth, 1000);
    }
}

// Safe calculation endpoint
async function safeCalculation() {
    log('Sending safe request to /crash endpoint with value=5...', 'info');
    
    try {
        const response = await fetch(`${API_BASE}/crash?value=5`);
        
        if (response.ok) {
            const data = await response.json();
            log(`✅ Safe calculation successful: 100 / 5 = ${data.result}`, 'success');
        } else {
            log('❌ Request failed', 'error');
        }
    } catch (error) {
        log(`❌ Error: ${error.message}`, 'error');
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    log('Frontend application started', 'info');
    checkHealth();
    loadUsers();
    
    // Periodic health checks
    setInterval(checkHealth, 30000); // Check every 30 seconds
});
