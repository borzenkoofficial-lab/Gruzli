from nexum_core.api.app import app

def test_project_api_surface():
    paths = {route.path for route in app.routes}
    required = {
        "/projects/clone",
        "/projects/open",
        "/projects/run",
        "/projects/inspect",
        "/projects/lifecycle",
        "/projects/checkpoint",
        "/projects/restore",
        "/projects/repair-plan",
        "/projects/verify-repair",
        "/projects/preview/start",
        "/projects/preview/stop",
    }
    assert required <= paths
