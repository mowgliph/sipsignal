#!/usr/bin/env bash
# scripts/test_chart_interactive.sh
# Manual test script for interactive chart feature

set -e

echo "🔍 Testing interactive chart feature..."

# Activate venv
source /home/mowgli/sipsignal/venv/bin/activate

# Run unit tests
echo "🧪 Running unit tests..."
pytest tests/unit/test_chart_generator.py -v
pytest tests/unit/test_chart_handler.py -v
pytest tests/unit/test_chart_capture.py -v

# Run integration tests
echo "🔗 Running integration tests..."
pytest tests/integration/test_chart_interactive.py -v

echo ""
echo "✅ All automated tests passed!"
echo ""
echo "📱 Manual testing required:"
echo "   1. Start bot: python bot/main.py"
echo "   2. Send: /chart BTCUSDT 4h"
echo "   3. Verify: Photo sent with inline keyboard below"
echo "   4. Click: Each timeframe button (1D, 4H, 1H, 15M, 30M)"
echo "   5. Click: Each indicator button (EMA, BB, RSI, Pivots)"
echo "   6. Verify: ✅ emoji appears/disappears on click"
echo "   7. Click: Refresh button"
echo "   8. Verify: Chart regenerates with same settings"
echo ""
echo "🎯 Success criteria:"
echo "   - All buttons respond within 3 seconds"
echo "   - ✅ emoji toggles correctly"
echo "   - Chart updates match button states"
echo "   - No errors in bot logs"
