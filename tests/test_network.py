from nexum_core.tools.web import NetworkPolicy

def test_network_blocks_private_targets():
    policy = NetworkPolicy("research")
    for url in ("http://127.0.0.1:8000", "http://localhost:8000"):
        try:
            policy.check(url)
        except PermissionError:
            pass
        else:
            raise AssertionError("private/local target was not blocked")

def test_network_off_blocks_public():
    policy = NetworkPolicy("off")
    try:
        policy.check("https://example.com")
    except PermissionError:
        pass
    else:
        raise AssertionError("network off mode did not block access")
