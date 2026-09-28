from nexum_core.tools.web import NetworkPolicy

def test_network_off_mode_requires_no_dns():
    policy = NetworkPolicy("off")
    try:
        policy.check("https://example.com")
    except PermissionError as exc:
        assert "disabled" in str(exc)
    else:
        raise AssertionError("offline mode must block before DNS resolution")
