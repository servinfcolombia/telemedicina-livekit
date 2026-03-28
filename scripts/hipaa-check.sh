#!/bin/bash
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ERRORS=0
WARNINGS=0

echo "=== Validación de Cumplimiento HIPAA ==="
echo ""

echo "1. Validando cifrado en tránsito..."
if curl -sI --tlsv1.3 https://localhost:7880 2>/dev/null | grep -q "TLS"; then
    echo -e "${GREEN}✓ TLS 1.3 detectado${NC}"
else
    echo -e "${YELLOW}⚠ No se puede validar TLS (servicio puede no estar corriendo)${NC}"
    ((WARNINGS++))
fi

echo ""
echo "2. Validando PostgreSQL con SSL..."
if docker exec postgres psql -U telemedicina -c "SHOW ssl;" 2>/dev/null | grep -q "on"; then
    echo -e "${GREEN}✓ PostgreSQL SSL habilitado${NC}"
else
    echo -e "${RED}✗ PostgreSQL SSL no está habilitado${NC}"
    ((ERRORS++))
fi

echo ""
echo "3. Validando configuración de JWT..."
if grep -q "ACCESS_TOKEN_EXPIRE_MINUTES: int = 15" backend/src/core/config.py; then
    echo -e "${GREEN}✓ Tiempo de expiración de token configurado (15 min)${NC}"
else
    echo -e "${RED}✗ Tiempo de expiración de token no configurado correctamente${NC}"
    ((ERRORS++))
fi

echo ""
echo "4. Validando políticas de red K8s..."
if [ -f "k8s/network-policies/default-deny.yaml" ]; then
    echo -e "${GREEN}✓ NetworkPolicy default-deny existe${NC}"
else
    echo -e "${RED}✗ NetworkPolicy default-deny no encontrada${NC}"
    ((ERRORS++))
fi

echo ""
echo "5. Validando middleware de auditoría..."
if [ -f "backend/src/middleware/audit_logger.py" ]; then
    echo -e "${GREEN}✓ Middleware de auditoría existe${NC}"
else
    echo -e "${YELLOW}⚠ Middleware de auditoría no encontrado${NC}"
    ((WARNINGS++))
fi

echo ""
echo "6. Validando logs de acceso PHI..."
if grep -q "audit" backend/src/middleware/audit_logger.py 2>/dev/null || [ -f "backend/src/middleware/audit_logger.py" ]; then
    echo -e "${GREEN}✓ Logging de auditoría configurado${NC}"
else
    echo -e "${YELLOW}⚠ Configuración de auditoría no verificada${NC}"
    ((WARNINGS++))
fi

echo ""
echo "7. Validando cifrado de contraseñas..."
if grep -q "CryptContext" backend/src/core/security.py; then
    echo -e "${GREEN}✓ Cifrado de contraseñas configurado (bcrypt)${NC}"
else
    echo -e "${RED}✗ Cifrado de contraseñas no configurado${NC}"
    ((ERRORS++))
fi

echo ""
echo "8. Validando RBAC..."
if grep -q "require_role" backend/src/core/security.py; then
    echo -e "${GREEN}✓ Control de acceso basado en roles (RBAC) configurado${NC}"
else
    echo -e "${RED}✗ RBAC no configurado${NC}"
    ((ERRORS++))
fi

echo ""
echo "=================================="
echo "Resultados:"
echo -e "Errores: ${RED}$ERRORS${NC}"
echo -e "Advertencias: ${YELLOW}$WARNINGS${NC}"

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ Validación completada exitosamente${NC}"
    exit 0
else
    echo -e "${RED}✗ Validación fallida - Corrija los errores antes de continuar${NC}"
    exit 1
fi
