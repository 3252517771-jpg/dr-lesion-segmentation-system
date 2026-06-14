from __future__ import annotations

from io import BytesIO

from PIL import Image


def make_image_bytes() -> BytesIO:
    image = Image.new("RGB", (96, 96), color=(80, 60, 50))
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    buffer.seek(0)
    return buffer


def create_patient(client) -> int:
    response = client.post(
        "/api/patients",
        json={"name": "Test", "gender": "女", "age": 50, "patient_id": "PX001"},
    )
    return response.get_json()["patient"]["id"]


def test_placeholder_diagnose_flow(client, app):
    app.config["MODEL_BACKEND"] = "placeholder"
    patient_id = create_patient(client)

    response = client.post(
        "/api/diagnose",
        data={"patient_id": str(patient_id), "image": (make_image_bytes(), "fundus.jpg")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 201
    payload = response.get_json()
    assert payload["mode"] == "placeholder"
    diagnosis = payload["diagnosis"]
    assert diagnosis["id"] > 0
    assert diagnosis["contour_url"].startswith("/api/images/uploads/contours/")
    assert diagnosis["image_url"].startswith("/api/images/uploads/originals/")

    image_response = client.get(diagnosis["contour_url"])
    assert image_response.status_code == 200
    assert image_response.content_type.startswith("image/")

    detail_response = client.get(f"/api/diagnoses/{diagnosis['id']}")
    assert detail_response.status_code == 200
    assert detail_response.get_json()["diagnosis"]["severity"] == "中度 NPDR"


def test_diagnose_validation_errors(client, app):
    app.config["MODEL_BACKEND"] = "placeholder"

    response = client.post("/api/diagnose", data={}, content_type="multipart/form-data")
    assert response.status_code == 400


def test_stats_endpoints(client, app):
    app.config["MODEL_BACKEND"] = "placeholder"
    patient_id = create_patient(client)
    client.post(
        "/api/diagnose",
        data={"patient_id": str(patient_id), "image": (make_image_bytes(), "fundus.jpg")},
        content_type="multipart/form-data",
    )

    overview = client.get("/api/stats/overview")
    assert overview.status_code == 200
    assert overview.get_json()["total_diagnoses"] == 1

    lesions = client.get("/api/stats/lesions")
    assert lesions.status_code == 200
    assert len(lesions.get_json()["lesion_frequencies"]) == 4

    trend = client.get("/api/stats/trend?days=7")
    assert trend.status_code == 200
    assert len(trend.get_json()["trend"]) == 7


def test_real_mode_missing_model_returns_error(client, app, tmp_path):
    app.config["MODEL_BACKEND"] = "real"
    app.config["MODEL_PATH"] = str(tmp_path / "missing.pth")
    patient_id = create_patient(client)

    response = client.post(
        "/api/diagnose",
        data={"patient_id": str(patient_id), "image": (make_image_bytes(), "fundus.jpg")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 500
    assert response.get_json()["error"]["code"] == "MODEL_LOAD_FAILED"
