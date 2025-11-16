/**
 * VintedBot Popup Script
 * Handles authentication and stats display
 */

const BACKEND_URL = 'https://vintedbot-staging.fly.dev';

let authToken = null;
let currentUser = null;

// Elements
const loginSection = document.getElementById('login-section');
const dashboardSection = document.getElementById('dashboard-section');
const loginForm = document.getElementById('login-form');
const statusDot = document.querySelector('.status-dot');
const statusText = document.getElementById('status-text');
const userNameEl = document.getElementById('user-name');
const userEmailEl = document.getElementById('user-email');
const logoutBtn = document.getElementById('logout-btn');
const autofillBtn = document.getElementById('autofill-btn');
const openDashboardBtn = document.getElementById('open-dashboard-btn');
const refreshStatsBtn = document.getElementById('refresh-stats-btn');

// Initialize
async function init() {
  console.log('🚀 VintedBot popup initialized');

  // Check if already logged in
  chrome.storage.sync.get(['authToken', 'currentUser'], async (result) => {
    if (result.authToken && result.currentUser) {
      authToken = result.authToken;
      currentUser = result.currentUser;

      // Verify token is still valid
      const valid = await verifyToken();
      if (valid) {
        showDashboard();
        loadStats();
      } else {
        showLogin();
      }
    } else {
      showLogin();
    }
  });

  // Event listeners
  loginForm.addEventListener('submit', handleLogin);
  logoutBtn.addEventListener('click', handleLogout);
  autofillBtn.addEventListener('click', handleAutofill);
  openDashboardBtn.addEventListener('click', openDashboard);
  refreshStatsBtn.addEventListener('click', loadStats);
}

// Show login section
function showLogin() {
  loginSection.style.display = 'block';
  dashboardSection.style.display = 'none';
  updateStatus('disconnected', 'Disconnected');
}

// Show dashboard section
function showDashboard() {
  loginSection.style.display = 'none';
  dashboardSection.style.display = 'block';
  updateStatus('connected', 'Connected');

  // Update user info
  if (currentUser) {
    userNameEl.textContent = currentUser.username || 'User';
    userEmailEl.textContent = currentUser.email || '';
  }
}

// Update status indicator
function updateStatus(status, text) {
  statusText.textContent = text;
  statusDot.className = 'status-dot';
  if (status === 'connected') {
    statusDot.classList.add('connected');
  } else if (status === 'loading') {
    statusDot.classList.add('loading');
  }
}

// Handle login
async function handleLogin(e) {
  e.preventDefault();

  const email = document.getElementById('email').value;
  const password = document.getElementById('password').value;
  const loginBtnText = document.getElementById('login-btn-text');

  loginBtnText.textContent = 'Logging in...';
  updateStatus('loading', 'Connecting...');

  try {
    const response = await fetch(`${BACKEND_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ email, password })
    });

    if (!response.ok) {
      throw new Error('Invalid credentials');
    }

    const data = await response.json();

    authToken = data.access_token;

    // Get user info
    const userResponse = await fetch(`${BACKEND_URL}/auth/me`, {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });

    if (!userResponse.ok) {
      throw new Error('Failed to get user info');
    }

    currentUser = await userResponse.json();

    // Save to storage
    chrome.storage.sync.set({
      authToken,
      currentUser
    }, () => {
      console.log('✅ Logged in successfully');

      // Notify content scripts
      chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (tabs[0]) {
          chrome.tabs.sendMessage(tabs[0].id, {
            action: 'authUpdated',
            token: authToken
          });
        }
      });

      showDashboard();
      loadStats();
    });

  } catch (error) {
    console.error('❌ Login error:', error);
    alert('Login failed: ' + error.message);
    updateStatus('disconnected', 'Login failed');
  } finally {
    loginBtnText.textContent = 'Login';
  }
}

// Verify token
async function verifyToken() {
  try {
    const response = await fetch(`${BACKEND_URL}/auth/me`, {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });

    return response.ok;

  } catch (error) {
    console.error('❌ Token verification error:', error);
    return false;
  }
}

// Handle logout
function handleLogout() {
  chrome.storage.sync.remove(['authToken', 'currentUser'], () => {
    authToken = null;
    currentUser = null;
    showLogin();
    console.log('✅ Logged out');
  });
}

// Load stats
async function loadStats() {
  if (!authToken) return;

  updateStatus('loading', 'Loading stats...');

  try {
    // Get first account ID
    const accountsResponse = await fetch(`${BACKEND_URL}/accounts`, {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });

    if (!accountsResponse.ok) {
      throw new Error('Failed to get accounts');
    }

    const accounts = await accountsResponse.json();

    if (accounts.length === 0) {
      // No accounts yet
      document.getElementById('stat-listings').textContent = '0';
      document.getElementById('stat-sales').textContent = '0';
      document.getElementById('stat-revenue').textContent = '€0';
      document.getElementById('stat-conversion').textContent = '0%';
      updateStatus('connected', 'Connected');
      return;
    }

    const accountId = accounts[0].id;

    // Get stats for first account
    const statsResponse = await fetch(
      `${BACKEND_URL}/accounts/${accountId}/stats?period=30d`,
      {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      }
    );

    if (!statsResponse.ok) {
      throw new Error('Failed to get stats');
    }

    const stats = await statsResponse.json();

    // Update UI
    document.getElementById('stat-listings').textContent = stats.active_listings || 0;
    document.getElementById('stat-sales').textContent = stats.total_sales || 0;
    document.getElementById('stat-revenue').textContent = `€${(stats.total_revenue || 0).toFixed(0)}`;
    document.getElementById('stat-conversion').textContent = `${(stats.conversion_rate || 0).toFixed(1)}%`;

    updateStatus('connected', 'Connected');

  } catch (error) {
    console.error('❌ Stats loading error:', error);
    updateStatus('connected', 'Stats unavailable');
  }
}

// Handle autofill button
function handleAutofill() {
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (tabs[0]) {
      chrome.tabs.sendMessage(tabs[0].id, {
        action: 'fillForm'
      });

      // Close popup
      window.close();
    }
  });
}

// Open dashboard
function openDashboard() {
  chrome.tabs.create({
    url: `${BACKEND_URL}`
  });
}

// Initialize on load
init();
