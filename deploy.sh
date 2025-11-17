#!/bin/bash
# 🚀 Script de déploiement automatique VintedBot
# Version 2.0.0 - 100% Impeccable

set -e  # Exit on error

echo "🚀 VintedBot - Déploiement Automatique"
echo "======================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Step 1: Build frontend
echo -e "${BLUE}📦 Étape 1/5: Construction du frontend...${NC}"
cd frontend
if [ ! -d "node_modules" ]; then
    echo "  📥 Installation des dépendances npm..."
    npm install --legacy-peer-deps
fi

echo "  🔨 Build du frontend..."
npm run build

if [ ! -d "dist" ]; then
    echo -e "${RED}❌ Erreur: dist/ n'a pas été créé${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Frontend construit avec succès${NC}"
cd ..

# Step 2: Deploy backend (with frontend inside)
echo ""
echo -e "${BLUE}🚀 Étape 2/5: Déploiement sur Fly.io...${NC}"
echo "  📤 Déploiement..."

flyctl deploy --config fly.toml

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Déployé avec succès${NC}"
else
    echo -e "${RED}❌ Erreur lors du déploiement${NC}"
    exit 1
fi

# Step 3: Verify deployment
echo ""
echo -e "${BLUE}🔍 Étape 3/5: Vérification...${NC}"
sleep 5

HEALTH=$(curl -s https://vintedbot-backend.fly.dev/health || echo "FAILED")

if echo "$HEALTH" | grep -q "healthy"; then
    echo -e "${GREEN}✅ Application en ligne${NC}"
else
    echo -e "${YELLOW}⚠️  Vérifier les logs: flyctl logs --app vintedbot-backend${NC}"
fi

echo ""
echo -e "${GREEN}✅ DÉPLOIEMENT TERMINÉ${NC}"
echo ""
echo "📋 Prochaines étapes:"
echo "  1. Vider le cache navigateur (Ctrl+Shift+R)"
echo "  2. Ouvrir: https://vintedbot-frontend.fly.dev"
echo "  3. Logs: flyctl logs --app vintedbot-backend"
echo ""
