/**
 * VintedBot Background Service Worker
 * Handles background tasks and message passing
 * 
 * SECURITY: No sensitive data in logs
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

// Handle messages from content scripts
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  // Forward auth messages to popup
  if (message.type === 'AUTH_SUCCESS') {
    // SECURITY: Don't log sensitive data
    console.log('✅ Auth message received');
    
    // Broadcast to all extension contexts
    chrome.runtime.sendMessage(message).catch(() => {
      // Ignore errors if popup is not open
    });
    
    sendResponse({ success: true });
  }
  
  return true;
});
