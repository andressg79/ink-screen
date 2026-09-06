import pytest
from unittest.mock import patch, MagicMock
from src.miner import (
    format_diff,
    format_uptime_seconds,
    get_mock_miner_metrics,
    get_miner_metrics
)

def test_format_diff():
    assert format_diff(500) == "500"
    assert format_diff(1500) == "1.5K"
    assert format_diff(1280169) == "1.28M"
    assert format_diff(2500000000) == "2.50G"

def test_format_uptime_seconds():
    assert format_uptime_seconds(45) == "45s"
    assert format_uptime_seconds(125) == "2m"
    assert format_uptime_seconds(3665) == "1h 1m"
    assert format_uptime_seconds(90060) == "1d 1h 1m"

def test_get_mock_miner_metrics():
    metrics = get_mock_miner_metrics()
    assert metrics["status"] == "MINANDO"
    assert metrics["hashrate_10s"] == 124.5
    assert metrics["shares_good"] == 42
    assert metrics["shares_rejected"] == 0
    assert metrics["diff_formatted"] == "1.28M"
    assert metrics["threads"] == 8
    assert metrics["algo"] == "rx/0"

def test_get_miner_metrics_success():
    mock_payload = {
        "paused": False,
        "algo": "rx/0",
        "uptime": 3600,
        "hugepages": [1176, 1176],
        "cpu": {"threads": 8},
        "hashrate": {
            "total": [130.5, 125.0, 120.0],
            "highest": 150.0
        },
        "results": {
            "shares_good": 10,
            "shares_total": 10,
            "diff_current": 1000000
        },
        "connection": {
            "pool": "gulf.moneroocean.stream:20128",
            "rejected": 0
        }
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_payload

    with patch("src.miner.requests.get", return_value=mock_resp):
        with patch.dict("os.environ", {"INK_SCREEN_MOCK": "0"}):
            metrics = get_miner_metrics()
            assert metrics["status"] == "MINANDO"
            assert metrics["hashrate_10s"] == 130.5
            assert metrics["hashrate_60s"] == 125.0
            assert metrics["hashrate_max"] == 150.0
            assert metrics["shares_good"] == 10
            assert metrics["shares_rejected"] == 0
            assert metrics["diff_formatted"] == "1.00M"
            assert metrics["hugepages"] == "100%"

def test_get_miner_metrics_paused_by_watchdog():
    # Simulamos falla de conexión HTTP y proceso en estado 'T' (stopped por SIGSTOP)
    with patch("src.miner.requests.get", side_effect=Exception("Connection refused")):
        with patch("src.miner.check_xmrig_process_state", return_value="T"):
            with patch.dict("os.environ", {"INK_SCREEN_MOCK": "0"}):
                metrics = get_miner_metrics()
                assert metrics["status"] == "PAUSADO (Watchdog)"
                assert metrics["paused"] is True
                assert metrics["hashrate_10s"] == 0.0

def test_get_miner_metrics_offline():
    # Simulamos falla de conexión y sin proceso xmrig
    with patch("src.miner.requests.get", side_effect=Exception("Connection refused")):
        with patch("src.miner.check_xmrig_process_state", return_value=None):
            with patch("src.miner.sys.platform", "linux"):
                with patch.dict("os.environ", {"INK_SCREEN_MOCK": "0"}):
                    metrics = get_miner_metrics()
                    assert metrics["status"] == "OFFLINE"
                    assert metrics["hashrate_10s"] == 0.0
                    assert metrics["pool"] == "Desconectado"
