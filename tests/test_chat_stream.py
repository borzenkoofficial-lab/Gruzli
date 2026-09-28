from nexum_core.api.app import app

def test_chat_stream_route_exists():
    routes={getattr(r,"path",None) for r in app.routes}
    assert "/chat/stream" in routes
