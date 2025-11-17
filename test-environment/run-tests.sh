#!/bin/bash

echo "🧪 VINTEDBOT - EXÉCUTION COMPLÈTE DES TESTS"
echo "============================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Use 'docker compose' or 'docker-compose' based on availability
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

# Step 1: Verify environment is running
echo -e "\n${YELLOW}1. Vérification environnement...${NC}"

backend_health=$(docker inspect --format='{{.State.Health.Status}}' vintedbot_test_backend 2>/dev/null || echo "not_running")
frontend_health=$(docker inspect --format='{{.State.Health.Status}}' vintedbot_test_frontend 2>/dev/null || echo "not_running")

if [ "$backend_health" != "healthy" ] || [ "$frontend_health" != "healthy" ]; then
    echo -e "${RED}❌ Environment not healthy. Running setup first...${NC}"
    ./test-environment/setup.sh
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Setup failed${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✅ Environment ready${NC}"

# Step 2: Run human simulator
echo -e "\n${YELLOW}2. Lancement simulation utilisateur humain...${NC}"
echo -e "${BLUE}   This will test the application like a real user${NC}"

# Install playwright in host if needed
if ! python3 -c "import playwright" 2>/dev/null; then
    echo -e "${YELLOW}   Installing Playwright...${NC}"
    pip3 install playwright asyncio --quiet || true
    playwright install chromium --with-deps 2>/dev/null || true
fi

# Run simulator
python3 test-environment/human_simulator.py --headless

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Human simulation completed${NC}"
else
    echo -e "${RED}❌ Human simulation failed${NC}"
    exit 1
fi

# Step 3: Display results summary
echo -e "\n${YELLOW}3. Résumé des résultats...${NC}"

if [ -f "test-results/report.json" ]; then
    # Parse JSON results
    total_tests=$(cat test-results/report.json | python3 -c "import sys, json; print(json.load(sys.stdin)['summary']['total_tests'])")
    passed=$(cat test-results/report.json | python3 -c "import sys, json; print(json.load(sys.stdin)['summary']['passed'])")
    failed=$(cat test-results/report.json | python3 -c "import sys, json; print(json.load(sys.stdin)['summary']['failed'])")
    bugs=$(cat test-results/report.json | python3 -c "import sys, json; print(json.load(sys.stdin)['summary']['bugs_found'])")
    critical=$(cat test-results/report.json | python3 -c "import sys, json; print(json.load(sys.stdin)['summary']['critical_bugs'])")

    echo -e "\n${GREEN}╔════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║          RÉSULTATS DES TESTS           ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "  Tests executés:     $total_tests"
    echo -e "  ${GREEN}✅ Passed:${NC}          $passed"
    echo -e "  ${RED}❌ Failed:${NC}          $failed"
    echo -e "  ${RED}🐛 Bugs found:${NC}      $bugs"
    echo -e "  ${RED}🔴 Critical bugs:${NC}   $critical"
    echo ""

    if [ "$critical" -gt 0 ]; then
        echo -e "${RED}⚠️  ATTENTION: ${critical} bugs critiques trouvés!${NC}"
    elif [ "$bugs" -gt 0 ]; then
        echo -e "${YELLOW}⚠️  ${bugs} bugs trouvés (non-critiques)${NC}"
    else
        echo -e "${GREEN}🎉 Aucun bug trouvé!${NC}"
    fi
else
    echo -e "${RED}❌ Report not found${NC}"
fi

# Step 4: Display next steps
echo -e "\n${BLUE}📊 Rapports générés:${NC}"
echo "  - HTML: file://$(pwd)/test-results/report.html"
echo "  - JSON: $(pwd)/test-results/report.json"
echo ""
echo -e "${BLUE}📸 Screenshots:${NC}"
ls -1 test-results/screenshots/*.png 2>/dev/null | wc -l | xargs echo "  " screenshots saved
echo ""
echo -e "${BLUE}🔍 Prochaines étapes:${NC}"
echo "  1. Ouvrir le rapport HTML dans votre navigateur"
echo "  2. Corriger les bugs critiques en priorité"
echo "  3. Implémenter les améliorations suggérées"
echo "  4. Relancer les tests après corrections"
echo ""
echo -e "${GREEN}✅ Tests terminés!${NC}"
echo ""

# Open report in browser (optional)
read -p "Ouvrir le rapport HTML maintenant? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v xdg-open &> /dev/null; then
        xdg-open test-results/report.html
    elif command -v open &> /dev/null; then
        open test-results/report.html
    else
        echo "Please open test-results/report.html manually"
    fi
fi
