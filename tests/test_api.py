from app import service

def recipient(name="Ada Lovelace", email="ada@example.com", course="Python"):
    return {"name": name, "email": email, "course": course}

def submit(client, recipients):
    return client.post("/api/jobs", json={"event_name": "AI Workshop", "issuer": "Example Org",
                                         "recipients": recipients})

def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_job_creation_pdf_generation_and_download(client):
    response = submit(client, [recipient()])
    assert response.status_code == 202
    job = client.get(response.json()["status_url"]).json()
    assert job["status"] == "completed"
    assert (job["total"], job["succeeded"], job["failed"]) == (1, 1, 0)
    download = client.get(job["recipients"][0]["certificate_url"])
    assert download.status_code == 200
    assert download.headers["content-type"] == "application/pdf"
    assert download.content.startswith(b"%PDF")

def test_invalid_recipient_does_not_block_valid_one(client):
    response = submit(client, [recipient(name="", email="bad"), recipient(name="Grace Hopper")])
    job = client.get(response.json()["status_url"]).json()
    assert job["status"] == "completed_with_errors"
    assert (job["total"], job["succeeded"], job["failed"]) == (2, 1, 1)
    assert job["recipients"][0]["status"] == "failed"
    assert job["recipients"][0]["error"]
    assert job["recipients"][1]["status"] == "succeeded"

def test_generation_exception_is_isolated(client, monkeypatch):
    original = service.generate_certificate
    def flaky(path, name, course, event_name, issuer):
        if name == "Fails":
            raise RuntimeError("simulated failure")
        original(path, name, course, event_name, issuer)
    monkeypatch.setattr(service, "generate_certificate", flaky)
    response = submit(client, [recipient("Fails", "fail@example.com"), recipient("Works", "works@example.com")])
    job = client.get(response.json()["status_url"]).json()
    assert job["failed"] == 1 and job["succeeded"] == 1
    assert job["recipients"][0]["error"] == "Certificate generation failed."
    assert job["recipients"][1]["status"] == "succeeded"

def test_empty_batch_rejected(client):
    response = client.post("/api/jobs", json={"event_name": "Course", "recipients": []})
    assert response.status_code == 422

def test_unknown_job_and_certificate_return_404(client):
    assert client.get("/api/jobs/no-such-job").status_code == 404
    assert client.get("/api/certificates/999999").status_code == 404
