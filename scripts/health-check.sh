#!/bin/bash
set -e

ERRORS=0

echo "=== Telemedicina Health Check ==="

echo -n "Checking LiveKit... "
if curl -sf http://localhost:7880/health > /dev/null 2>&1; then
    echo "OK"
else
    echo "FAIL"
    ERRORS=$((ERRORS + 1))
fi

echo -n "Checking Redis... "
if docker exec redis redis-cli ping > /dev/null 2>&1; then
    echo "OK"
else
    echo "FAIL"
    ERRORS=$((ERRORS + 1))
fi

echo -n "Checking PostgreSQL... "
if docker exec postgres pg_isready -U telemedicina > /dev/null 2>&1; then
    echo "OK"
else
    echo "FAIL"
    ERRORS=$((ERRORS + 1))
fi

echo -n "Checking MinIO... "
if curl -sf http://localhost:9000/minio/health/live > /dev/null 2>&1; then
    echo "OK"
else
    echo "FAIL"
    ERRORS=$((ERRORS + 1))
fi

echo -n "Checking Caddy... "
if curl -sf http://localhost:80 > /dev/null 2>&1; then
    echo "OK"
else
    echo "FAIL"
    ERRORS=$((ERRORS + 1))
fi

echo "==================================="
if [ $ERRORS -eq 0 ]; then
    echo "All services healthy!"
    exit 0
else
    echo "$ERRORS service(s) failed"
    exit 1
fi
