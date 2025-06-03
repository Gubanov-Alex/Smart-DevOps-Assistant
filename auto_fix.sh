#!/bin/bash
# auto_fix.sh - Автоматическое исправление проблем с кодом

set -e

echo "🔧 Автоматическое исправление проблем с кодом..."
echo "=============================================="

# Проверяем Poetry
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry не найден. Установите Poetry сначала."
    exit 1
fi

echo "📦 Устанавливаем зависимости..."
poetry install --no-interaction

echo ""
echo "🎨 Применяем Black форматирование..."
echo "-----------------------------------"
poetry run black tests/ app/ || echo "Black завершен"

echo ""
echo "📋 Исправляем порядок импортов..."
echo "-------------------------------"
poetry run isort tests/ app/ || echo "isort завершен"

echo ""
echo "🔍 Проверяем результат с flake8..."
echo "--------------------------------"
poetry run flake8 tests/ app/ || {
    echo ""
    echo "⚠️  Остались некоторые проблемы с flake8."
    echo "Скорее всего, это можно исправить обновлением файлов тестов."
}

echo ""
echo "🧪 Запускаем тесты для проверки..."
echo "-------------------------------"
poetry run pytest tests/ --tb=short -q

echo ""
echo "✅ Автоисправление завершено!"
echo ""
echo "📝 Следующие шаги:"
echo "1. Скопируйте обновленные тестовые файлы из артефактов"
echo "2. Обновите pyproject.toml с конфигурацией flake8"
echo "3. Запустите: ./quality_check.sh"
