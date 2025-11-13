#!/bin/bash

# ═══════════════════════════════════════════════════════════════════════════
# Script de Validation Pré-Déploiement - Système de Stockage Multi-Tier
# ═══════════════════════════════════════════════════════════════════════════

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Icons
CHECK="✓"
CROSS="✗"
INFO="ℹ"
WARN="⚠"

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Validation Système de Stockage Multi-Tier${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

ERRORS=0
WARNINGS=0

# ═══════════════════════════════════════════════════════════════════════════
# 1. Vérifier les fichiers du système de stockage
# ═══════════════════════════════════════════════════════════════════════════

echo -e "${BLUE}[1/6] Vérification des fichiers...${NC}"

FILES=(
    "backend/storage/__init__.py"
    "backend/storage/storage_manager.py"
    "backend/storage/tier1_local.py"
    "backend/storage/tier2_r2.py"
    "backend/storage/tier3_b2.py"
    "backend/storage/compression.py"
    "backend/storage/lifecycle_manager.py"
    "backend/storage/metrics.py"
    "backend/storage/README.md"
    "backend/api/v1/routers/storage.py"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "  ${GREEN}${CHECK}${NC} $file"
    else
        echo -e "  ${RED}${CROSS}${NC} $file ${RED}(MANQUANT)${NC}"
        ERRORS=$((ERRORS + 1))
    fi
done

echo ""

# ═══════════════════════════════════════════════════════════════════════════
# 2. Vérifier les dépendances Python
# ═══════════════════════════════════════════════════════════════════════════

echo -e "${BLUE}[2/6] Vérification des dépendances Python...${NC}"

DEPENDENCIES=(
    "boto3"
    "b2sdk"
    "Pillow"
)

cd backend

for dep in "${DEPENDENCIES[@]}"; do
    if grep -q "$dep" requirements.txt; then
        echo -e "  ${GREEN}${CHECK}${NC} $dep (dans requirements.txt)"
    else
        echo -e "  ${RED}${CROSS}${NC} $dep ${RED}(MANQUANT dans requirements.txt)${NC}"
        ERRORS=$((ERRORS + 1))
    fi
done

cd ..

echo ""

# ═══════════════════════════════════════════════════════════════════════════
# 3. Vérifier la configuration du cron job
# ═══════════════════════════════════════════════════════════════════════════

echo -e "${BLUE}[3/6] Vérification du cron job...${NC}"

if grep -q "storage_lifecycle_job" backend/jobs.py; then
    echo -e "  ${GREEN}${CHECK}${NC} Fonction storage_lifecycle_job définie"
else
    echo -e "  ${RED}${CROSS}${NC} Fonction storage_lifecycle_job non trouvée"
    ERRORS=$((ERRORS + 1))
fi

if grep -q "storage_lifecycle" backend/jobs.py && grep -q "CronTrigger(hour=3" backend/jobs.py; then
    echo -e "  ${GREEN}${CHECK}${NC} Cron job configuré (daily at 3 AM)"
else
    echo -e "  ${RED}${CROSS}${NC} Cron job non configuré correctement"
    ERRORS=$((ERRORS + 1))
fi

echo ""

# ═══════════════════════════════════════════════════════════════════════════
# 4. Vérifier le schéma de base de données
# ═══════════════════════════════════════════════════════════════════════════

echo -e "${BLUE}[4/6] Vérification du schéma de base de données...${NC}"

if grep -q "photo_metadata" backend/core/storage.py; then
    echo -e "  ${GREEN}${CHECK}${NC} Table photo_metadata définie"
else
    echo -e "  ${RED}${CROSS}${NC} Table photo_metadata non trouvée"
    ERRORS=$((ERRORS + 1))
fi

REQUIRED_COLUMNS=(
    "photo_id"
    "user_id"
    "tier"
    "file_size_bytes"
    "compressed_size_bytes"
    "scheduled_deletion"
    "published_to_vinted"
)

for col in "${REQUIRED_COLUMNS[@]}"; do
    if grep -q "$col" backend/core/storage.py; then
        echo -e "  ${GREEN}${CHECK}${NC} Colonne $col"
    else
        echo -e "  ${YELLOW}${WARN}${NC} Colonne $col non trouvée"
        WARNINGS=$((WARNINGS + 1))
    fi
done

echo ""

# ═══════════════════════════════════════════════════════════════════════════
# 5. Vérifier l'enregistrement du router
# ═══════════════════════════════════════════════════════════════════════════

echo -e "${BLUE}[5/6] Vérification de l'enregistrement du router...${NC}"

if grep -q "storage" backend/app.py && grep -q "app.include_router(storage.router" backend/app.py; then
    echo -e "  ${GREEN}${CHECK}${NC} Router storage enregistré dans app.py"
else
    echo -e "  ${RED}${CROSS}${NC} Router storage non enregistré"
    ERRORS=$((ERRORS + 1))
fi

if grep -q "from backend.api.v1.routers import.*storage" backend/app.py; then
    echo -e "  ${GREEN}${CHECK}${NC} Import storage dans app.py"
else
    echo -e "  ${RED}${CROSS}${NC} Import storage manquant dans app.py"
    ERRORS=$((ERRORS + 1))
fi

echo ""

# ═══════════════════════════════════════════════════════════════════════════
# 6. Variables d'environnement requises (checklist)
# ═══════════════════════════════════════════════════════════════════════════

echo -e "${BLUE}[6/6] Variables d'environnement requises...${NC}"

echo -e "${YELLOW}${INFO}${NC} Les secrets suivants doivent être configurés sur Fly.io:"
echo ""
echo -e "  Cloudflare R2 (obligatoire) :"
echo -e "    - R2_ENDPOINT_URL"
echo -e "    - R2_ACCESS_KEY_ID"
echo -e "    - R2_SECRET_ACCESS_KEY"
echo -e "    - R2_BUCKET_NAME"
echo -e "    - R2_CDN_DOMAIN (optionnel)"
echo ""
echo -e "  Backblaze B2 (optionnel mais recommandé) :"
echo -e "    - B2_APPLICATION_KEY_ID"
echo -e "    - B2_APPLICATION_KEY"
echo -e "    - B2_BUCKET_NAME"
echo ""
echo -e "${YELLOW}${WARN}${NC} Exécuter après le déploiement :"
echo -e "    ${BLUE}flyctl secrets list --app vintedbot-backend${NC}"
echo ""

# ═══════════════════════════════════════════════════════════════════════════
# Résumé
# ═══════════════════════════════════════════════════════════════════════════

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Résumé de la validation${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}${CHECK} Aucune erreur détectée${NC}"
    echo -e "${GREEN}${CHECK} Système prêt pour le déploiement !${NC}"
    echo ""
    echo -e "Prochaines étapes :"
    echo -e "  1. Configurer les secrets R2/B2 sur Fly.io"
    echo -e "  2. Exécuter : ${BLUE}flyctl deploy --app vintedbot-backend${NC}"
    echo -e "  3. Tester : ${BLUE}curl https://vintedbot-backend.fly.dev/api/storage/tiers/info${NC}"
    echo ""
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}${WARN} $WARNINGS avertissement(s) détecté(s)${NC}"
    echo -e "${GREEN}${CHECK} Aucune erreur critique${NC}"
    echo -e "${YELLOW}Vous pouvez déployer, mais vérifiez les avertissements ci-dessus${NC}"
    echo ""
    exit 0
else
    echo -e "${RED}${CROSS} $ERRORS erreur(s) détectée(s)${NC}"
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}${WARN} $WARNINGS avertissement(s) détecté(s)${NC}"
    fi
    echo ""
    echo -e "${RED}Corrigez les erreurs avant de déployer${NC}"
    echo ""
    exit 1
fi
