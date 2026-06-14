def test_health_check(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert data["db"] is True
    assert data["model_backend"] == "auto"
    assert data["segmentation_classes"] == ["HE", "EX", "MA", "SE"]
