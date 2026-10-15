from fastapi.testclient import TestClient
from src.main import app, messages_db

client = TestClient(app)

def setup_function():
    """Reset the database before each test to ensure isolation."""
    messages_db.clear()
    import src.main
    src.main.current_id = 1

def test_create_valid_message():
    """1. Create a valid message."""
    response = client.post("/api/v1/messages", json={"role": "user", "content": "Hello API!"})
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["role"] == "user"
    assert data["content"] == "Hello API!"
    assert "created_at" in data

def test_reject_empty_message():
    """2. Reject an empty message (or whitespace only)."""
    response = client.post("/api/v1/messages", json={"role": "user", "content": "   "})
    assert response.status_code == 422

def test_list_messages_with_params():
    """3. List messages using limit, offset, and role."""
    client.post("/api/v1/messages", json={"role": "user", "content": "Msg 1"})
    client.post("/api/v1/messages", json={"role": "assistant", "content": "Msg 2"})
    client.post("/api/v1/messages", json={"role": "user", "content": "Msg 3"})
    
    response = client.get("/api/v1/messages?role=user&limit=1&offset=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["content"] == "Msg 3"

def test_retrieve_existing_message():
    """4. Retrieve an existing message."""
    post_res = client.post("/api/v1/messages", json={"role": "user", "content": "Test GET"})
    msg_id = post_res.json()["id"]
    
    get_res = client.get(f"/api/v1/messages/{msg_id}")
    assert get_res.status_code == 200
    assert get_res.json()["content"] == "Test GET"

def test_return_404_for_missing_message():
    """5. Return 404 for a missing message."""
    response = client.get("/api/v1/messages/999")
    assert response.status_code == 404
    assert response.json()["detail"]["error"] == "Message not found"

def test_update_message():
    """6. Update a message."""
    post_res = client.post("/api/v1/messages", json={"role": "user", "content": "Initial"})
    msg_id = post_res.json()["id"]
    
    patch_res = client.patch(f"/api/v1/messages/{msg_id}", json={"content": "Updated"})
    assert patch_res.status_code == 200
    assert patch_res.json()["content"] == "Updated"

def test_delete_message():
    """7. Delete a message and confirm it can no longer be retrieved."""
    post_res = client.post("/api/v1/messages", json={"role": "user", "content": "To delete"})
    msg_id = post_res.json()["id"]
    
    del_res = client.delete(f"/api/v1/messages/{msg_id}")
    assert del_res.status_code == 204
    
    get_res = client.get(f"/api/v1/messages/{msg_id}")
    assert get_res.status_code == 404