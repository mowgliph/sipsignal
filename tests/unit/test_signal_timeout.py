"""
Tests para signal timeout handler.
"""

from datetime import UTC, datetime, timedelta

import pytest


def test_timeout_threshold_comparison():
    """
    Test que verifica que el timeout threshold se puede comparar
    con datetimes de la base de datos (naive).
    """
    # Simular el cálculo del timeout threshold
    signal_timeout = 3600  # 1 hora en segundos

    # Threshold con timezone (offset-aware)
    threshold_aware = datetime.now(UTC) - timedelta(seconds=signal_timeout)

    # Threshold sin timezone (offset-naive) para comparar con DB
    threshold_naive = datetime.now(UTC).replace(tzinfo=None) - timedelta(seconds=signal_timeout)

    # Simular detected_at de la DB (offset-naive)
    detected_at_naive = datetime.now(UTC).replace(tzinfo=None) - timedelta(seconds=3700)

    # La comparación naive-naive DEBE funcionar
    assert detected_at_naive < threshold_naive

    # La comparación aware-naive DEBE fallar
    with pytest.raises(TypeError):
        assert detected_at_naive < threshold_aware
