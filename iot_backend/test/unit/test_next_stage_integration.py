from app.main import app
from app.core.security import create_access_token, decode_access_token, get_password_hash, verify_password
from app.services.token_revocation import revoke, is_revoked


def test_next_stage_routes_registered():
    paths = {getattr(route, "path", "") for route in app.routes}
    assert "/api/v1/auth/logout" in paths
    assert "/api/v1/firmware/rollouts" in paths
    assert "/api/v1/scale/profile" in paths
    assert "/api/v1/firmware/rollouts/{rollout_id}/rollback" in paths
    assert "/api/v1/scenes/{scene_id}/executions" in paths


def test_jwt_revocation_flow():
    payload = decode_access_token(create_access_token({"sub": "integration"}))
    assert payload["jti"]
    revoke(payload["jti"], int(payload["exp"]))
    assert is_revoked(payload["jti"])


def test_long_password_round_trip():
    password = "x" * 10000
    assert verify_password(password, get_password_hash(password))
