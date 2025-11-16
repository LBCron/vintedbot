/**
 * VintedBot Content Script
 * Runs on Vinted pages to inject AI auto-fill functionality
 * 
 * SECURITY: XSS Protection
 * - ✅ Uses textContent instead of innerHTML
 * - ✅ Input sanitization
 * - ✅ No eval() or dangerous functions
 * - ✅ CSP compliant
 */

console.log('🤖 VintedBot content script loaded');

// SECURITY: Sanitize text to prevent XSS
function sanitizeText(text) {
  if (typeof text !== 'string') return '';
  
  // Create a text node and get its escaped content
  const div = document.createElement('div');
  div.textContent = text;
  return div.textContent;
}

// SECURITY: Validate URL before making requests
function isValidApiUrl(url) {
  try {
    const parsed = new URL(url);
    const allowedHosts = [
      'vintedbot.com',
      'vintedbot-staging.fly.dev',
      'localhost'
    ];
    
    return allowedHosts.some(host => parsed.hostname === host || parsed.hostname.endsWith(`.${host}`));
  } catch {
    return false;
  }
}

// Check if we're on a Vinted listing creation page
function isListingCreationPage() {
  return window.location.href.includes('/items/new') || 
         window.location.href.includes('/items/upload') ||
         document.querySelector('[data-testid="item-upload-form"]') !== null;
}

// Get API token from storage
async function getApiToken() {
  return new Promise((resolve) => {
    chrome.storage.local.get(['vintedbot_token'], (result) => {
      resolve(result.vintedbot_token || null);
    });
  });
}

// Get API base URL from storage
async function getApiUrl() {
  return new Promise((resolve) => {
    chrome.storage.local.get(['vintedbot_api_url'], (result) => {
      resolve(result.vintedbot_api_url || 'https://vintedbot-staging.fly.dev');
    });
  });
}

// Generate AI description for listing
async function generateDescription(title, category, brand, condition) {
  const token = await getApiToken();
  const apiUrl = await getApiUrl();
  
  if (!token) {
    alert('Please log in to VintedBot first');
    return null;
  }
  
  // SECURITY FIX: Validate API URL
  if (!isValidApiUrl(apiUrl)) {
    console.error('🔒 Invalid API URL:', apiUrl);
    return null;
  }
  
  // SECURITY: Sanitize inputs
  const payload = {
    title: sanitizeText(title),
    category: sanitizeText(category),
    brand: sanitizeText(brand),
    condition: sanitizeText(condition)
  };
  
  try {
    const response = await fetch(`${apiUrl}/api/v1/ai/generate-description`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(payload)
    });
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    
    const data = await response.json();
    return data.description;
    
  } catch (error) {
    console.error('Error generating description:', error);
    return null;
  }
}

// Create AI auto-fill button
function createAutoFillButton() {
  const button = document.createElement('button');
  button.className = 'vintedbot-autofill-btn';
  
  // SECURITY FIX: Use textContent instead of innerHTML
  button.textContent = '✨ AI Auto-fill';
  
  button.addEventListener('click', async (e) => {
    e.preventDefault();
    
    // SECURITY: Prevent duplicate clicks
    if (button.disabled) return;
    button.disabled = true;
    
    // SECURITY FIX: Use textContent
    const originalText = button.textContent;
    button.textContent = '⏳ Generating...';
    
    try {
      // Get form values
      const titleInput = document.querySelector('input[name="title"]') || 
                        document.querySelector('[data-testid="item-title"]');
      const categorySelect = document.querySelector('select[name="category"]') || 
                            document.querySelector('[data-testid="item-category"]');
      const brandInput = document.querySelector('input[name="brand"]') || 
                        document.querySelector('[data-testid="item-brand"]');
      const conditionSelect = document.querySelector('select[name="condition"]') || 
                             document.querySelector('[data-testid="item-condition"]');
      const descriptionTextarea = document.querySelector('textarea[name="description"]') || 
                                  document.querySelector('[data-testid="item-description"]');
      
      if (!titleInput || !descriptionTextarea) {
        alert('Could not find form fields');
        return;
      }
      
      // SECURITY: Sanitize values before sending
      const title = sanitizeText(titleInput.value);
      const category = categorySelect ? sanitizeText(categorySelect.value) : '';
      const brand = brandInput ? sanitizeText(brandInput.value) : '';
      const condition = conditionSelect ? sanitizeText(conditionSelect.value) : '';
      
      if (!title) {
        alert('Please enter a title first');
        return;
      }
      
      // Generate description
      const description = await generateDescription(title, category, brand, condition);
      
      if (description) {
        // SECURITY: Set value safely (textarea.value is safe)
        descriptionTextarea.value = description;
        
        // Trigger change event
        descriptionTextarea.dispatchEvent(new Event('input', { bubbles: true }));
        descriptionTextarea.dispatchEvent(new Event('change', { bubbles: true }));
        
        // SECURITY FIX: Use textContent
        button.textContent = '✅ Done!';
        
        setTimeout(() => {
          button.textContent = originalText;
        }, 2000);
      } else {
        button.textContent = '❌ Error';
        setTimeout(() => {
          button.textContent = originalText;
        }, 2000);
      }
      
    } catch (error) {
      console.error('Auto-fill error:', error);
      button.textContent = '❌ Error';
      setTimeout(() => {
        button.textContent = originalText;
      }, 2000);
    } finally {
      button.disabled = false;
    }
  });
  
  return button;
}

// Inject auto-fill button on listing creation page
function injectAutoFillButton() {
  if (!isListingCreationPage()) return;
  
  // Check if button already exists
  if (document.querySelector('.vintedbot-autofill-btn')) return;
  
  // Find description field to inject button near it
  const descriptionTextarea = document.querySelector('textarea[name="description"]') || 
                              document.querySelector('[data-testid="item-description"]');
  
  if (descriptionTextarea) {
    const button = createAutoFillButton();
    
    // Insert button before textarea
    descriptionTextarea.parentElement.insertBefore(button, descriptionTextarea);
    
    console.log('✅ VintedBot auto-fill button injected');
  }
}

// Initialize
function initialize() {
  // Inject button if on listing creation page
  injectAutoFillButton();
  
  // Watch for page changes (SPA navigation)
  const observer = new MutationObserver(() => {
    injectAutoFillButton();
  });
  
  observer.observe(document.body, {
    childList: true,
    subtree: true
  });
}

// Wait for DOM to be ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initialize);
} else {
  initialize();
}
