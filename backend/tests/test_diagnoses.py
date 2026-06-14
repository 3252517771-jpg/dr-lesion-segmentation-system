def test_diagnosis_crud_flow(client):
    patient_response = client.post(
        "/api/patients",
        json={"name": "Bob", "gender": "男", "age": 60, "patient_id": "P100"},
    )
    patient_id = patient_response.get_json()["patient"]["id"]

    create_response = client.post(
        "/api/diagnoses",
        json={
            "patient_id": patient_id,
            "image_path": "uploads/originals/test.jpg",
            "contour_path": "uploads/contours/test.png",
            "lesion_areas": {"HE": 1.2, "EX": 0.3, "MA": 0.1, "SE": 0.0},
            "lesion_counts": {"HE": 4, "EX": 1, "MA": 8, "SE": 0},
            "lesion_positions": {
                "HE": [{"x": 0.45, "y": 0.4, "area": 42, "area_ratio": 0.01, "bbox": [40, 35, 8, 9]}],
                "EX": [],
                "MA": [],
                "SE": [],
            },
            "severity": "中度 NPDR",
        },
    )
    assert create_response.status_code == 201
    created_diagnosis = create_response.get_json()["diagnosis"]
    diagnosis_id = created_diagnosis["id"]
    assert created_diagnosis["lesion_positions"]["HE"][0]["x"] == 0.45

    list_response = client.get(f"/api/diagnoses?patient_id={patient_id}")
    assert list_response.status_code == 200
    assert list_response.get_json()["total"] == 1

    detail_response = client.get(f"/api/diagnoses/{diagnosis_id}")
    assert detail_response.status_code == 200
    assert detail_response.get_json()["diagnosis"]["severity"] == "中度 NPDR"
    assert detail_response.get_json()["diagnosis"]["lesion_positions"]["HE"][0]["bbox"] == [40, 35, 8, 9]

    update_response = client.put(f"/api/diagnoses/{diagnosis_id}", json={"notes": "复查"})
    assert update_response.status_code == 200
    assert update_response.get_json()["diagnosis"]["notes"] == "复查"

    delete_response = client.delete(f"/api/diagnoses/{diagnosis_id}")
    assert delete_response.status_code == 200
    assert delete_response.get_json()["success"] is True

    missing_response = client.get(f"/api/diagnoses/{diagnosis_id}")
    assert missing_response.status_code == 404
