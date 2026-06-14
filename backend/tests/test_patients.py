def test_patient_crud_flow(client):
    create_response = client.post(
        "/api/patients",
        json={"name": "Alice", "gender": "女", "age": 52, "patient_id": "P001"},
    )
    assert create_response.status_code == 201
    patient = create_response.get_json()["patient"]
    assert patient["name"] == "Alice"

    list_response = client.get("/api/patients?search=P001")
    assert list_response.status_code == 200
    assert list_response.get_json()["total"] == 1

    update_response = client.put(f"/api/patients/{patient['id']}", json={"age": 53})
    assert update_response.status_code == 200
    assert update_response.get_json()["patient"]["age"] == 53

    delete_response = client.delete(f"/api/patients/{patient['id']}")
    assert delete_response.status_code == 200
    assert delete_response.get_json()["success"] is True

    missing_response = client.get(f"/api/patients/{patient['id']}")
    assert missing_response.status_code == 404


def test_patient_validation(client):
    response = client.post("/api/patients", json={"name": "", "gender": "女", "age": 20, "patient_id": "P002"})

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "VALIDATION_ERROR"
