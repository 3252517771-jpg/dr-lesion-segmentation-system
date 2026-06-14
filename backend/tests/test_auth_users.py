def test_auth_me_requires_login(anonymous_client):
    response = anonymous_client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


def test_default_admin_login_and_logout(anonymous_client):
    login_response = anonymous_client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert login_response.status_code == 200
    assert login_response.get_json()["user"]["role"] == "doctor"

    me_response = anonymous_client.get("/api/auth/me")
    assert me_response.status_code == 200
    assert me_response.get_json()["user"]["username"] == "admin"

    logout_response = anonymous_client.post("/api/auth/logout")
    assert logout_response.status_code == 200

    missing_response = anonymous_client.get("/api/auth/me")
    assert missing_response.status_code == 401


def test_doctor_can_manage_users(client):
    patient_response = client.post(
        "/api/patients",
        json={"name": "Patient User", "gender": "female", "age": 51, "patient_id": "PU001"},
    )
    patient_id = patient_response.get_json()["patient"]["id"]

    create_response = client.post(
        "/api/users",
        json={
            "username": "patient01",
            "display_name": "Patient 01",
            "password": "pass123",
            "role": "patient",
            "linked_patient_id": patient_id,
        },
    )
    assert create_response.status_code == 201
    user = create_response.get_json()["user"]
    assert user["linked_patient_id"] == patient_id
    assert "password_hash" not in user

    list_response = client.get("/api/users?search=patient01")
    assert list_response.status_code == 200
    assert list_response.get_json()["total"] == 1

    update_response = client.put(f"/api/users/{user['id']}", json={"display_name": "Updated Patient"})
    assert update_response.status_code == 200
    assert update_response.get_json()["user"]["display_name"] == "Updated Patient"

    delete_response = client.delete(f"/api/users/{user['id']}")
    assert delete_response.status_code == 200
    assert delete_response.get_json()["success"] is True


def test_patient_role_is_restricted(anonymous_client):
    anonymous_client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    own_patient = anonymous_client.post(
        "/api/patients",
        json={"name": "Own Patient", "gender": "female", "age": 48, "patient_id": "OWN001"},
    ).get_json()["patient"]
    other_patient = anonymous_client.post(
        "/api/patients",
        json={"name": "Other Patient", "gender": "male", "age": 62, "patient_id": "OTH001"},
    ).get_json()["patient"]
    anonymous_client.post(
        "/api/users",
        json={
            "username": "own_patient",
            "display_name": "Own Patient Account",
            "password": "patient123",
            "role": "patient",
            "linked_patient_id": own_patient["id"],
        },
    )
    anonymous_client.post("/api/auth/logout")

    login_response = anonymous_client.post("/api/auth/login", json={"username": "own_patient", "password": "patient123"})
    assert login_response.status_code == 200

    own_response = anonymous_client.get(f"/api/patients/{own_patient['id']}")
    assert own_response.status_code == 200

    other_response = anonymous_client.get(f"/api/patients/{other_patient['id']}")
    assert other_response.status_code == 403

    users_response = anonymous_client.get("/api/users")
    assert users_response.status_code == 403

    stats_response = anonymous_client.get("/api/stats/overview")
    assert stats_response.status_code == 403
