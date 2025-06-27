set -e

echo "🔧 Fixing security setup issues..."

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}1. Creating all necessary directories...${NC}"
mkdir -p reports/security reports/coverage reports/benchmarks
mkdir -p logs/app logs/security logs/audit
mkdir -p models/checkpoints models/exports models/backups
mkdir -p data/raw data/processed data/temp
mkdir -p docs/api docs/user docs/dev
mkdir -p backups/db backups/models backups/configs
mkdir -p .secrets
touch .secrets/.gitkeep 2>/dev/null || true

echo -e "${GREEN}✅ Directories created${NC}"

echo -e "${BLUE}2. Checking directory structure...${NC}"
ls -la reports/
ls -la reports/security/

echo -e "${BLUE}3. Testing bandit command...${NC}"
if poetry run bandit -r app/ --version &> /dev/null; then
    echo -e "${GREEN}✅ Bandit is working${NC}"
else
    echo -e "${RED}❌ Bandit has issues${NC}"
fi

echo -e "${BLUE}4. Testing safety command...${NC}"
poetry run safety --version || echo -e "${YELLOW}⚠️ Safety version check failed${NC}"

echo -e "${BLUE}5. Testing safety format options...${NC}"
poetry run safety check --help | grep -A 10 "format" || echo -e "${YELLOW}⚠️ Could not get safety format help${NC}"

echo -e "${BLUE}6. Creating minimal bandit config...${NC}"
cat > .bandit << 'EOF'
[bandit]
targets = app/
exclude_dirs = */tests/*,*/migrations/*,*/venv/*,*/.venv/*
confidence = medium
severity = medium
skips =
tests =
EOF

echo -e "${GREEN}✅ Bandit config created${NC}"

echo -e "${BLUE}7. Testing basic bandit scan...${NC}"
poetry run bandit -r app/ -f txt || echo -e "${YELLOW}⚠️ Bandit scan completed with issues${NC}"

echo -e "${BLUE}8. Testing safety with different formats...${NC}"
echo "Testing safety --format json:"
poetry run safety check --format json 2>/dev/null || echo -e "${YELLOW}JSON format failed${NC}"

echo "Testing safety --output-format json:"
poetry run safety check --output-format json 2>/dev/null || echo -e "${YELLOW}Output-format failed${NC}"

echo "Testing safety basic check:"
poetry run safety check 2>/dev/null || echo -e "${YELLOW}Basic check failed${NC}"

echo -e "${BLUE}9. Checking safety version and downgrade if needed...${NC}"
SAFETY_VERSION=$(poetry run safety --version 2>/dev/null | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+' || echo "unknown")
echo "Current safety version: $SAFETY_VERSION"

if [[ "$SAFETY_VERSION" == "3."* ]]; then
    echo -e "${YELLOW}⚠️ Safety 3.x has API changes. Consider downgrading or updating commands${NC}"
    echo "To downgrade: poetry add --group dev 'safety<3.0.0'"
    echo "Or update Makefile to use new API"
fi

echo -e "${BLUE}10. Testing file creation in reports/security/...${NC}"
echo "test" > reports/security/test.txt
if [[ -f "reports/security/test.txt" ]]; then
    echo -e "${GREEN}✅ File creation works${NC}"
    rm reports/security/test.txt
else
    echo -e "${RED}❌ Cannot create files in reports/security/${NC}"
fi

echo -e "${BLUE}11. Fixing permissions...${NC}"
chmod -R u+w reports/ logs/ models/ data/ docs/ backups/ .secrets/ 2>/dev/null || true

echo -e "${GREEN}✅ Security setup fixes completed!${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Run: make security"
echo "2. If safety still fails, run: poetry add --group dev 'safety<3.0.0'"
echo "3. Check reports in: reports/security/"
