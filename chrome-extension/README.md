# VintedBot Chrome Extension

AI-powered Chrome extension for Vinted sellers to automate listing creation and track performance.

## Features

- **AI Auto-fill**: Automatically fill Vinted listing forms with AI-generated content
- **Real-time Stats**: View your sales statistics directly in the extension
- **Quick Actions**: Access VintedBot features without leaving Vinted
- **Smart Integration**: Seamlessly integrates with VintedBot backend

## Installation

### For Development

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top right)
3. Click "Load unpacked"
4. Select the `chrome-extension` folder
5. The extension icon should appear in your browser

### For Production (Chrome Web Store)

1. Build the extension: `npm run build:extension` (or zip manually)
2. Go to [Chrome Web Store Developer Dashboard](https://chrome.google.com/webstore/devconsole/)
3. Upload the ZIP file
4. Fill in store listing details
5. Submit for review

## Files Structure

```
chrome-extension/
├── manifest.json         # Extension configuration (Manifest v3)
├── background.js         # Service worker for background tasks
├── content.js           # Injected into Vinted pages
├── content-styles.css   # Styles for auto-fill button
├── popup.html           # Extension popup UI
├── popup.js             # Popup logic
├── styles.css           # Popup styles
├── icons/               # Extension icons (16x16, 48x48, 128x128)
└── README.md           # This file
```

## Usage

### Login

1. Click the VintedBot extension icon
2. Enter your VintedBot credentials
3. Click "Login"

### Auto-fill Listing

1. Go to Vinted listing creation page
2. Upload product images
3. Click the "Auto-fill with AI" button
4. Review and adjust the generated content
5. Submit your listing

### View Stats

- Click the extension icon to see your 30-day statistics
- Click "Refresh" to update stats
- Click "Open Dashboard" to access full dashboard

## Configuration

The extension connects to the VintedBot backend at:
- Staging: `https://vintedbot-staging.fly.dev`
- Production: `https://vintedbot-backend.fly.dev`

To change the backend URL, update `BACKEND_URL` in:
- `content.js`
- `popup.js`

## Icons

Extension icons should be in PNG format:
- `icons/icon16.png` - 16x16px (toolbar)
- `icons/icon48.png` - 48x48px (extensions page)
- `icons/icon128.png` - 128x128px (Chrome Web Store)

Use the VintedBot logo with a transparent background.

## Building for Production

### Manual Build

1. Remove development files (README.md, etc.)
2. Minify JavaScript files (optional)
3. Create ZIP archive:

```bash
cd chrome-extension
zip -r ../vintedbot-extension.zip . -x "*.git*" "README.md"
```

### Automated Build

Use the build script:

```bash
cd scripts
./build-extension.sh
```

## Permissions

The extension requires:

- `storage` - Store auth token and user preferences
- `activeTab` - Access current tab to inject auto-fill
- `tabs` - Detect Vinted pages
- Host permissions for:
  - `https://www.vinted.*/*` - All Vinted domains
  - `https://*.fly.dev/*` - VintedBot backend

## Security

- Auth tokens are stored securely in Chrome's sync storage
- All API calls use HTTPS
- No sensitive data is logged
- Tokens are validated on each request

## Privacy

- Extension only activates on Vinted pages
- No user data is collected without consent
- All data is processed via VintedBot backend
- See VintedBot Privacy Policy for details

## Support

- Documentation: https://docs.vintedbot.com
- Issues: https://github.com/yourorg/vintedbot/issues
- Email: support@vintedbot.com

## Version History

### v1.0.0 (2025-11-16)
- Initial release
- AI auto-fill functionality
- Real-time statistics
- Dashboard integration

## License

Proprietary - All rights reserved

---

**Made with ❤️ by VintedBot Team**
