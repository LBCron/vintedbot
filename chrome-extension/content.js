/**
 * VintedBot Content Script
 * Auto-fills Vinted listing forms with AI-generated data
 */

// Configuration
const BACKEND_URL = 'https://vintedbot-staging.fly.dev';
let authToken = null;
let vintedBotButton = null;

// Initialize
async function init() {
  console.log('🤖 VintedBot Assistant loaded');

  // Get auth token from storage
  chrome.storage.sync.get(['authToken'], (result) => {
    authToken = result.authToken;

    if (authToken) {
      console.log('✅ Authenticated');
      checkForListingForm();
    } else {
      console.log('⚠️ Not authenticated - Please login in popup');
    }
  });

  // Watch for URL changes (SPA navigation)
  observeUrlChanges();
}

// Detect listing form page
function checkForListingForm() {
  const isListingPage = window.location.pathname.includes('/items/new') ||
                        window.location.pathname.includes('/items/upload') ||
                        document.querySelector('[data-testid="item-upload-form"]');

  if (isListingPage) {
    console.log('📝 Listing form detected');
    injectAutoFillButton();
  }
}

// Inject AI auto-fill button
function injectAutoFillButton() {
  // Avoid duplicate buttons
  if (vintedBotButton) return;

  // Find form container
  const formContainer = document.querySelector('[data-testid="item-upload-form"]') ||
                        document.querySelector('form') ||
                        document.querySelector('.item-box');

  if (!formContainer) {
    console.log('⚠️ Form container not found');
    setTimeout(injectAutoFillButton, 1000);
    return;
  }

  // Create button
  vintedBotButton = document.createElement('button');
  vintedBotButton.className = 'vintedbot-autofill-btn';
  vintedBotButton.innerHTML = `
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <path d="M8 0L10 6L16 8L10 10L8 16L6 10L0 8L6 6L8 0Z" fill="currentColor"/>
    </svg>
    <span>Auto-fill with AI</span>
  `;

  vintedBotButton.onclick = handleAutoFill;

  // Insert at top of form
  formContainer.insertBefore(vintedBotButton, formContainer.firstChild);

  console.log('✅ Auto-fill button injected');
}

// Handle auto-fill action
async function handleAutoFill(e) {
  e.preventDefault();

  if (!authToken) {
    alert('❌ Please login to VintedBot first (click extension icon)');
    return;
  }

  vintedBotButton.disabled = true;
  vintedBotButton.innerHTML = '<span>🤖 Generating...</span>';

  try {
    // Get uploaded images info
    const images = extractUploadedImages();

    if (images.length === 0) {
      alert('⚠️ Please upload at least one image first');
      resetButton();
      return;
    }

    // Get user description if any
    const descriptionField = findField('description');
    const userDescription = descriptionField ? descriptionField.value : '';

    // Call backend AI generation
    const aiData = await generateAIListing(images, userDescription);

    if (aiData) {
      fillFormWithAIData(aiData);
      vintedBotButton.innerHTML = '<span>✅ Auto-filled!</span>';

      setTimeout(() => {
        resetButton();
      }, 2000);
    } else {
      resetButton();
    }

  } catch (error) {
    console.error('❌ Auto-fill error:', error);
    alert('❌ Auto-fill failed: ' + error.message);
    resetButton();
  }
}

// Extract uploaded images
function extractUploadedImages() {
  const images = [];

  // Try to find image upload section
  const imageElements = document.querySelectorAll('[data-testid="item-photo"]') ||
                        document.querySelectorAll('.item-photo img') ||
                        document.querySelectorAll('input[type="file"]');

  imageElements.forEach(img => {
    if (img.src && !img.src.includes('placeholder')) {
      images.push(img.src);
    }
  });

  console.log(`📸 Found ${images.length} images`);
  return images;
}

// Generate AI listing via backend
async function generateAIListing(images, userDescription) {
  try {
    const response = await fetch(`${BACKEND_URL}/drafts/ai-generate`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        account_id: 'chrome_extension',
        user_description: userDescription || 'Generate listing from images',
        images: images.slice(0, 5)  // Max 5 images
      })
    });

    if (!response.ok) {
      throw new Error(`Backend error: ${response.status}`);
    }

    const data = await response.json();
    console.log('✅ AI data received:', data);

    return data;

  } catch (error) {
    console.error('❌ AI generation error:', error);
    throw error;
  }
}

// Fill form with AI data
function fillFormWithAIData(data) {
  console.log('📝 Filling form with AI data');

  // Title
  if (data.title) {
    const titleField = findField('title');
    if (titleField) {
      setFieldValue(titleField, data.title);
    }
  }

  // Description
  if (data.description) {
    const descField = findField('description');
    if (descField) {
      setFieldValue(descField, data.description);
    }
  }

  // Price
  if (data.price) {
    const priceField = findField('price');
    if (priceField) {
      setFieldValue(priceField, data.price.toString());
    }
  }

  // Category
  if (data.category) {
    const categoryField = findField('category');
    if (categoryField) {
      selectDropdownOption(categoryField, data.category);
    }
  }

  // Brand
  if (data.brand) {
    const brandField = findField('brand');
    if (brandField) {
      setFieldValue(brandField, data.brand);
    }
  }

  // Size
  if (data.size) {
    const sizeField = findField('size');
    if (sizeField) {
      selectDropdownOption(sizeField, data.size);
    }
  }

  // Color
  if (data.color) {
    const colorField = findField('color');
    if (colorField) {
      selectDropdownOption(colorField, data.color);
    }
  }

  // Condition
  if (data.condition) {
    const conditionField = findField('condition');
    if (conditionField) {
      selectDropdownOption(conditionField, data.condition);
    }
  }

  console.log('✅ Form filled successfully');
}

// Find form field by name/id/label
function findField(fieldName) {
  const selectors = [
    `input[name*="${fieldName}" i]`,
    `textarea[name*="${fieldName}" i]`,
    `select[name*="${fieldName}" i]`,
    `input[id*="${fieldName}" i]`,
    `textarea[id*="${fieldName}" i]`,
    `select[id*="${fieldName}" i]`,
    `[data-testid*="${fieldName}" i]`
  ];

  for (const selector of selectors) {
    const field = document.querySelector(selector);
    if (field) return field;
  }

  return null;
}

// Set field value with events
function setFieldValue(field, value) {
  if (!field) return;

  // Focus field
  field.focus();

  // Set value
  field.value = value;

  // Trigger events (for React/Vue)
  const events = ['input', 'change', 'blur'];
  events.forEach(eventType => {
    const event = new Event(eventType, { bubbles: true });
    field.dispatchEvent(event);
  });

  console.log(`✅ Set field value: ${field.name || field.id} = ${value}`);
}

// Select dropdown option
function selectDropdownOption(field, value) {
  if (!field) return;

  if (field.tagName === 'SELECT') {
    // Native select
    const options = Array.from(field.options);
    const match = options.find(opt =>
      opt.text.toLowerCase().includes(value.toLowerCase()) ||
      opt.value.toLowerCase().includes(value.toLowerCase())
    );

    if (match) {
      field.value = match.value;
      field.dispatchEvent(new Event('change', { bubbles: true }));
      console.log(`✅ Selected option: ${match.text}`);
    }
  } else {
    // Custom dropdown - try to click matching option
    field.click();
    setTimeout(() => {
      const option = document.querySelector(`[role="option"]:contains("${value}")`);
      if (option) option.click();
    }, 300);
  }
}

// Reset button state
function resetButton() {
  if (vintedBotButton) {
    vintedBotButton.disabled = false;
    vintedBotButton.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
        <path d="M8 0L10 6L16 8L10 10L8 16L6 10L0 8L6 6L8 0Z" fill="currentColor"/>
      </svg>
      <span>Auto-fill with AI</span>
    `;
  }
}

// Observe URL changes
function observeUrlChanges() {
  let lastUrl = location.href;

  new MutationObserver(() => {
    const url = location.href;
    if (url !== lastUrl) {
      lastUrl = url;
      checkForListingForm();
    }
  }).observe(document.body, { subtree: true, childList: true });
}

// Listen for messages from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'authUpdated') {
    authToken = request.token;
    console.log('✅ Auth token updated');
    checkForListingForm();
  }

  if (request.action === 'fillForm') {
    handleAutoFill({ preventDefault: () => {} });
  }
});

// Initialize on load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
