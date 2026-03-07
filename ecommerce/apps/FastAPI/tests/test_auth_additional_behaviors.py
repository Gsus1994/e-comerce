from __future__ import annotations

from fastapi.testclient import TestClient


def test_recover_password_unknown_email_returns_generic_message(client: TestClient) -> None:
    response = client.post(
        "/v1/auth/recover-password",
        json={"email": "missing@example.com", "new_password": "newstrongpass1"},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "If the account exists, password has been updated."}


def test_auth_flows_normalize_email_case_and_whitespace(client: TestClient) -> None:
    register_response = client.post(
        "/v1/auth/register",
        json={"email": "  MiXeD@Example.com  ", "password": "strongpass1"},
    )
    assert register_response.status_code == 201
    register_payload = register_response.json()
    assert register_payload["user"]["email"] == "mixed@example.com"

    login_response = client.post(
        "/v1/auth/login",
        json={"email": "mixed@example.com", "password": "strongpass1"},
    )
    assert login_response.status_code == 200

    recover_response = client.post(
        "/v1/auth/recover-password",
        json={"email": "  MIXED@EXAMPLE.COM  ", "new_password": "newstrongpass1"},
    )
    assert recover_response.status_code == 200

    old_login = client.post(
        "/v1/auth/login",
        json={"email": "mixed@example.com", "password": "strongpass1"},
    )
    assert old_login.status_code == 401

    new_login = client.post(
        "/v1/auth/login",
        json={"email": "mixed@example.com", "password": "newstrongpass1"},
    )
    assert new_login.status_code == 200
