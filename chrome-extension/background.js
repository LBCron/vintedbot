/**
 * VintedBot Background Service Worker
 * Handles background tasks and message passing
 */

console.log('🤖 VintedBot background service worker loaded');

// Installation
chrome.runtime.onInstalled.addListener((details) => {
  if (details.reason === 'install') {
    console.log('✅ VintedBot installed');

    // Open welcome page
    chrome.tabs.create({
      url: 'https://vintedbot-staging.fly.dev'
    });
  } else if (details.reason === 'update') {
    console.log('✅ VintedBot updated to', chrome.runtime.getManifest().version);
  }
});

// Listen for messages from content scripts and popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('📨 Message received:', request);

  if (request.action === 'notification') {
    // Show notification
    chrome.notifications.create({
      type: 'basic',
      iconUrl: 'icons/icon128.png',
      title: request.title || 'VintedBot',
      message: request.message || '',
      priority: 2
    });
  }

  if (request.action === 'openTab') {
    // Open new tab
    chrome.tabs.create({
      url: request.url
    });
  }

  if (request.action === 'getAuthToken') {
    // Get auth token from storage
    chrome.storage.sync.get(['authToken'], (result) => {
      sendResponse({ token: result.authToken });
    });
    return true; // Keep channel open for async response
  }

  return true;
});

// Monitor tab updates to detect Vinted pages
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && tab.url) {
    // Check if it's a Vinted page
    if (tab.url.includes('vinted.')) {
      console.log('📍 Vinted page detected:', tab.url);

      // Inject content script if needed (already done via manifest)
      // Could send message to content script here if needed
    }
  }
});

// Context menu (right-click menu)
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: 'vintedbot-autofill',
    title: 'Auto-fill with VintedBot AI',
    contexts: ['page'],
    documentUrlPatterns: ['https://www.vinted.*/*']
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === 'vintedbot-autofill') {
    // Send message to content script to trigger auto-fill
    chrome.tabs.sendMessage(tab.id, {
      action: 'fillForm'
    });
  }
});

// Keep service worker alive (important for Manifest v3)
const keepAlive = () => {
  setInterval(() => {
    chrome.storage.local.get(['heartbeat'], () => {
      // Just accessing storage keeps service worker alive
    });
  }, 20000); // Every 20 seconds
};

keepAlive();

// Analytics (optional)
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'trackEvent') {
    console.log('📊 Event tracked:', request.event, request.data);
    // Could send to analytics service here
  }
});

console.log('✅ VintedBot background service worker ready');
