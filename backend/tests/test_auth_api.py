import pytest
from app.models.user import UserRole

def test_register_always_creates_patient(client):
    # Try sending role: admin in the body
    payload = {
        "email": "infiltrator@test.com",
        "password": "Password123!",
        "full_name": "Wannabe Admin",
        "role": "admin"  # PublicRegister should ignore or reject this field
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["role"] == "patient", "Public registration must ALWAYS produce a patient account"
    assert data["email"] == "infiltrator@test.com"

def test_login_flow(client, create_user):
    user = create_user("doctor_login@test.com", "DoctorPass123!", "Dr. Test", UserRole.DOCTOR)
    
    # Successful login
    login_res = client.post("/api/v1/auth/token", data={
        "username": "doctor_login@test.com",
        "password": "DoctorPass123!"
    })
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

    # Failed login with incorrect password
    bad_res = client.post("/api/v1/auth/token", data={
        "username": "doctor_login@test.com",
        "password": "WrongPassword!"
    })
    assert bad_res.status_code == 401
    assert "incorrect" in bad_res.json()["detail"].lower()

def test_role_based_access_controls(client, create_user):
    patient = create_user("patient_rbac@test.com", "Pass123!", "John Patient", UserRole.PATIENT)
    doctor = create_user("doctor_rbac@test.com", "Pass123!", "Dr. Smith", UserRole.DOCTOR)
    admin = create_user("admin_rbac@test.com", "Pass123!", "Admin Boss", UserRole.ADMIN)

    # Get tokens
    def get_token(email):
        res = client.post("/api/v1/auth/token", data={"username": email, "password": "Pass123!"})
        return res.json()["access_token"]

    patient_token = get_token("patient_rbac@test.com")
    doctor_token = get_token("doctor_rbac@test.com")
    admin_token = get_token("admin_rbac@test.com")

    # Patient accessing doctor endpoint -> 403
    p_to_doc = client.get("/api/v1/doctor/patients/triage-queue", headers={"Authorization": f"Bearer {patient_token}"})
    assert p_to_doc.status_code == 403

    # Patient accessing admin endpoint -> 403
    p_to_adm = client.get("/api/v1/admin/stats", headers={"Authorization": f"Bearer {patient_token}"})
    assert p_to_adm.status_code == 403

    # Doctor accessing admin endpoint -> 403
    d_to_adm = client.get("/api/v1/admin/stats", headers={"Authorization": f"Bearer {doctor_token}"})
    assert d_to_adm.status_code == 403

    # Admin accessing admin endpoint -> 200
    a_to_adm = client.get("/api/v1/admin/stats", headers={"Authorization": f"Bearer {admin_token}"})
    assert a_to_adm.status_code == 200

def test_admin_can_create_doctor_and_admin_cannot_demote_self(client, create_user):
    admin = create_user("superadmin@test.com", "AdminPass123!", "Super Admin", UserRole.ADMIN)
    token = client.post("/api/v1/auth/token", data={"username": "superadmin@test.com", "password": "AdminPass123!"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Admin creates a new doctor
    new_doc_res = client.post("/api/v1/admin/users", json={
        "email": "created_doc@test.com",
        "password": "DocPass123!",
        "full_name": "Created Physician",
        "role": "doctor",
        "is_active": True
    }, headers=headers)
    assert new_doc_res.status_code in [200, 201]
    assert new_doc_res.json()["role"] == "doctor"

    # Admin cannot demote self
    demote_self_res = client.patch(f"/api/v1/admin/users/{admin.id}/role?new_role=patient", headers=headers)
    assert demote_self_res.status_code == 400
    assert "demote" in demote_self_res.json()["detail"].lower()

    # Admin cannot deactivate self
    deact_self_res = client.patch(f"/api/v1/admin/users/{admin.id}/toggle-status", headers=headers)
    assert deact_self_res.status_code == 400
    assert "deactivate" in deact_self_res.json()["detail"].lower()
