/**
 * VintedBot Popup Script
 * Handles authentication and stats display
 * 
 * SECURITY: XSS Protection
 * - ✅ Uses textContent instead of innerHTML
 * - ✅ Input sanitization
 * - ✅ URL validation
 * - ✅ No JWT token in console logs
 */

// SECURITY: Sanitize text
function sanitizeText(text) {
  if (typeof text !== 'string') return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.textContent;
}

// SECURITY: Validate URL
function isValidUrl(url) {
  try {
    const parsed = new URL(url);
    return parsed.protocol === 'https:' || (parsed.protocol === 'http:' && parsed.hostname === 'localhost');
  } catch {
    return false;
  }
}

// Check if user is logged in
async function checkAuthStatus() {
  const token = await getToken();
  
  if (token) {
    showDashboard();
    await loadStats();
  } else {
    showLogin();
  }
}

// Get token from storage
async function getToken() {
  return new Promise((resolve) => {
    chrome.storage.local.get(['vintedbot_token'], (result) => {
      resolve(result.vintedbot_token || null);
    });
  });
}

// Get API URL from storage
async function getApiUrl() {
  return new Promise((resolve) => {
    chrome.storage.local.get(['vintedbot_api_url'], (result) => {
      resolve(result.vintedbot_api_url || 'https://vintedbot-staging.fly.dev');
    });
  });
}

// Save token and API URL
async function saveAuth(token, apiUrl) {
  return new Promise((resolve) => {
    chrome.storage.local.set({ 
      vintedbot_token: token,
      vintedbot_api_url: apiUrl
    }, resolve);
  });
}

// Clear auth
async function clearAuth() {
  return new Promise((resolve) => {
    chrome.storage.local.remove(['vintedbot_token', 'vintedbot_api_url'], resolve);
  });
}

// Show login view
function showLogin() {
  document.getElementById('login-view').style.display = 'block';
  document.getElementById('dashboard-view').style.display = 'none';
}

// Show dashboard view
function showDashboard() {
  document.getElementById('login-view').style.display = 'none';
  document.getElementById('dashboard-view').style.display = 'block';
}

// Handle login
async function handleLogin() {
  const apiUrlInput = document.getElementById('api-url');
  const loginBtn = document.getElementById('login-btn');
  
  const apiUrl = apiUrlInput.value.trim();
  
  // SECURITY FIX: Validate URL
  if (!isValidUrl(apiUrl)) {
    alert('Invalid API URL. Must be HTTPS.');
    return;
  }
  
  // SECURITY FIX: Use textContent
  const originalText = loginBtn.textContent;
  loginBtn.disabled = true;
  loginBtn.textContent = 'Opening...';
  
  // Save API URL
  await saveAuth(null, apiUrl);
  
  // Open login page in new tab
  chrome.tabs.create({
    url: `${apiUrl}/extension-auth`
  });
  
  // SECURITY FIX: Use textContent
  loginBtn.textContent = 'Waiting for login...';
  
  // Listen for auth message from the auth page
  chrome.runtime.onMessage.addListener(function listener(message) {
    if (message.type === 'AUTH_SUCCESS' && message.token) {
      // SECURITY FIX: Don't log token to console
      console.log('✅ Authentication successful');
      
      // Save token
      saveAuth(message.token, apiUrl).then(() => {
        showDashboard();
        loadStats();
        chrome.runtime.onMessage.removeListener(listener);
      });
    }
  });
  
  // Reset button after timeout
  setTimeout(() => {
    loginBtn.disabled = false;
    loginBtn.textContent = originalText;
  }, 5000);
}

// Load user stats
async function loadStats() {
  const token = await getToken();
  const apiUrl = await getApiUrl();
  
  if (!token || !apiUrl) return;
  
  try {
    const response = await fetch(`${apiUrl}/api/v1/listings/stats`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    if (!response.ok) throw new Error('Failed to load stats');
    
    const data = await response.json();
    
    // SECURITY FIX: Use textContent to prevent XSS
    document.getElementById('listings-count').textContent = data.total_listings || 0;
    document.getElementById('views-count').textContent = data.total_views || 0;
    document.getElementById('plan-name').textContent = sanitizeText(data.plan || 'Free');
    
  } catch (error) {
    console.error('Error loading stats:', error);
    
    // SECURITY FIX: Use textContent
    document.getElementById('listings-count').textContent = '!';
    document.getElementById('views-count').textContent = '!';
    document.getElementById('plan-name').textContent = 'Error';
  }
}

// Handle logout
async function handleLogout() {
  await clearAuth();
  showLogin();
}

// Initialize popup
document.addEventListener('DOMContentLoaded', () => {
  // Check auth status
  checkAuthStatus();
  
  // Login button
  document.getElementById('login-btn').addEventListener('click', handleLogin);
  
  // Logout button
  document.getElementById('logout-btn').addEventListener('click', handleLogout);
});
