from nexum_core.api.app import app

def test_live_terminal_endpoint_exists():
    paths = {route.path for route in app.routes}
    assert "/terminal/stream" in paths
