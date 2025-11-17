#!/bin/bash
set -e

echo "📦 BUILDING CHROME EXTENSION"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Directories
EXTENSION_DIR="/home/user/vintedbot/chrome-extension"
BUILD_DIR="/home/user/vintedbot/dist"
OUTPUT_FILE="vintedbot-extension.zip"

# Create build directory
echo -e "${BLUE}Creating build directory...${NC}"
mkdir -p "$BUILD_DIR"

# Clean previous build
if [ -f "$BUILD_DIR/$OUTPUT_FILE" ]; then
    echo -e "${BLUE}Removing previous build...${NC}"
    rm "$BUILD_DIR/$OUTPUT_FILE"
fi

# Create ZIP archive
echo -e "${BLUE}Creating ZIP archive...${NC}"
cd "$EXTENSION_DIR"

zip -r "$BUILD_DIR/$OUTPUT_FILE" . \
    -x "*.git*" \
    -x "README.md" \
    -x "*.DS_Store" \
    -x "__MACOSX/*"

cd -

# Verify ZIP
if [ -f "$BUILD_DIR/$OUTPUT_FILE" ]; then
    SIZE=$(du -h "$BUILD_DIR/$OUTPUT_FILE" | cut -f1)
    echo -e "${GREEN}✅ Extension built successfully!${NC}"
    echo -e "Output: ${BLUE}$BUILD_DIR/$OUTPUT_FILE${NC}"
    echo -e "Size: ${BLUE}$SIZE${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Test locally: Load unpacked in chrome://extensions/"
    echo "2. Upload to Chrome Web Store: https://chrome.google.com/webstore/devconsole/"
    echo ""
else
    echo -e "${RED}❌ Build failed${NC}"
    exit 1
fi
