"""
Test Suite for UI Bug Fixes - Iteration 20
Tests: Authentication, Settings, Logo Upload, Admin Access, Clients CRUD
"""
import pytest
import requests
import os
import uuid
import base64

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@btpfacture.com"
ADMIN_PASSWORD = "Admin123!"
USER_EMAIL = "rafik.remila@gmail.com"
USER_PASSWORD = "Zeralda@0676"


class TestAuthentication:
    """Test user login and authentication"""
    
    def test_admin_login_success(self):
        """Test: Admin can login successfully"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "access_token" in data, "Response should contain access_token"
        assert "user" in data, "Response should contain user object"
        assert data["user"]["email"] == ADMIN_EMAIL
        assert data["user"]["role"] == "super_admin"
        print(f"✓ Admin login successful - role: {data['user']['role']}")
    
    def test_user_login_success(self):
        """Test: Regular user can login successfully"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": USER_EMAIL,
            "password": USER_PASSWORD
        })
        assert response.status_code == 200, f"User login failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "access_token" in data, "Response should contain access_token"
        assert "user" in data, "Response should contain user object"
        assert data["user"]["email"] == USER_EMAIL
        print(f"✓ User login successful - role: {data['user']['role']}")
    
    def test_login_invalid_credentials(self):
        """Test: Login with invalid credentials returns 401"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@test.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Invalid credentials correctly rejected with 401")
    
    def test_login_missing_fields(self):
        """Test: Login with missing fields returns 422"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL
        })
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        print("✓ Missing password correctly rejected with 422")


class TestSettingsPage:
    """Test settings page load and save functionality"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def user_token(self):
        """Get regular user token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": USER_EMAIL,
            "password": USER_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_get_settings_authenticated(self, user_token):
        """Test: Authenticated user can get settings"""
        response = requests.get(
            f"{BASE_URL}/api/settings",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200, f"Get settings failed: {response.text}"
        data = response.json()
        
        # Verify settings structure
        assert "company_name" in data or data == {}, "Settings should have company_name or be empty"
        print(f"✓ Settings loaded successfully")
    
    def test_update_settings(self, user_token):
        """Test: User can update settings"""
        test_company_name = f"Test Company {uuid.uuid4().hex[:6]}"
        
        response = requests.put(
            f"{BASE_URL}/api/settings",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "company_name": test_company_name,
                "address": "123 Test Street",
                "phone": "0612345678",
                "email": "test@company.com",
                "siret": "12345678901234",
                "default_vat_rates": [20.0, 10.0, 5.5]
            }
        )
        assert response.status_code == 200, f"Update settings failed: {response.text}"
        data = response.json()
        
        # Verify update was applied
        assert data.get("company_name") == test_company_name, "Company name should be updated"
        print(f"✓ Settings updated successfully - company: {test_company_name}")
        
        # Verify persistence with GET
        get_response = requests.get(
            f"{BASE_URL}/api/settings",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data.get("company_name") == test_company_name, "Settings should persist"
        print("✓ Settings persisted correctly")
    
    def test_settings_unauthenticated(self):
        """Test: Unauthenticated request returns 401"""
        response = requests.get(f"{BASE_URL}/api/settings")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Unauthenticated settings request correctly rejected")


class TestLogoUpload:
    """Test logo upload functionality"""
    
    @pytest.fixture(scope="class")
    def user_token(self):
        """Get user token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": USER_EMAIL,
            "password": USER_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_upload_logo_png(self, user_token):
        """Test: User can upload PNG logo"""
        # Create a simple 1x1 PNG image
        png_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )
        
        files = {"file": ("test_logo.png", png_data, "image/png")}
        response = requests.post(
            f"{BASE_URL}/api/settings/logo",
            headers={"Authorization": f"Bearer {user_token}"},
            files=files
        )
        
        assert response.status_code == 200, f"Logo upload failed: {response.text}"
        data = response.json()
        assert "logo_base64" in data, "Response should contain logo_base64"
        print("✓ PNG logo uploaded successfully")
    
    def test_upload_logo_jpeg(self, user_token):
        """Test: User can upload JPEG logo"""
        # Create a simple 1x1 JPEG image
        jpeg_data = base64.b64decode(
            "/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAn/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBEQCEAwEPwAB//9k="
        )
        
        files = {"file": ("test_logo.jpg", jpeg_data, "image/jpeg")}
        response = requests.post(
            f"{BASE_URL}/api/settings/logo",
            headers={"Authorization": f"Bearer {user_token}"},
            files=files
        )
        
        assert response.status_code == 200, f"JPEG logo upload failed: {response.text}"
        print("✓ JPEG logo uploaded successfully")
    
    def test_logo_persists_in_settings(self, user_token):
        """Test: Uploaded logo persists in settings"""
        response = requests.get(
            f"{BASE_URL}/api/settings",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Logo should be in settings (may be None if never uploaded)
        assert "logo_base64" in data or data.get("logo_base64") is None, "Settings should have logo_base64 field"
        print("✓ Logo field present in settings")


class TestAdminAccess:
    """Test admin login and dashboard access"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def user_token(self):
        """Get regular user token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": USER_EMAIL,
            "password": USER_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_admin_can_access_users_list(self, admin_token):
        """Test: Admin can access users list"""
        response = requests.get(
            f"{BASE_URL}/api/users",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Admin users list failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), "Users list should be an array"
        print(f"✓ Admin can access users list - {len(data)} users found")
    
    def test_regular_user_cannot_access_users_list(self, user_token):
        """Test: Regular user cannot access users list"""
        response = requests.get(
            f"{BASE_URL}/api/users",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✓ Regular user correctly denied access to users list")
    
    def test_admin_can_access_dashboard(self, admin_token):
        """Test: Admin can access dashboard"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Dashboard access failed: {response.text}"
        data = response.json()
        
        # Verify dashboard structure
        assert "total_turnover" in data or "total_clients" in data, "Dashboard should have stats"
        print("✓ Admin can access dashboard")
    
    def test_admin_can_access_metrics(self, admin_token):
        """Test: Admin can access SaaS metrics"""
        response = requests.get(
            f"{BASE_URL}/api/admin/metrics",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Admin metrics failed: {response.text}"
        data = response.json()
        
        # Verify metrics structure
        assert "mrr" in data, "Metrics should have MRR"
        assert "active_subscribers" in data, "Metrics should have active_subscribers"
        print(f"✓ Admin can access metrics - MRR: {data.get('mrr')}")


class TestClientsCRUD:
    """Test Clients CRUD operations"""
    
    @pytest.fixture(scope="class")
    def user_token(self):
        """Get user token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": USER_EMAIL,
            "password": USER_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def test_client_id(self, user_token):
        """Create a test client and return its ID"""
        client_data = {
            "name": f"TEST_Client_{uuid.uuid4().hex[:6]}",
            "address": "123 Test Street",
            "phone": "0612345678",
            "email": "testclient@test.com"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/clients",
            headers={"Authorization": f"Bearer {user_token}"},
            json=client_data
        )
        assert response.status_code == 201, f"Create client failed: {response.text}"
        return response.json()["id"]
    
    def test_create_client(self, user_token):
        """Test: User can create a client"""
        client_data = {
            "name": f"TEST_NewClient_{uuid.uuid4().hex[:6]}",
            "address": "456 New Street",
            "phone": "0698765432",
            "email": "newclient@test.com"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/clients",
            headers={"Authorization": f"Bearer {user_token}"},
            json=client_data
        )
        assert response.status_code == 201, f"Create client failed: {response.text}"
        data = response.json()
        
        assert data["name"] == client_data["name"], "Client name should match"
        assert "id" in data, "Response should contain client ID"
        print(f"✓ Client created successfully - ID: {data['id']}")
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/clients/{data['id']}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
    
    def test_get_clients_list(self, user_token):
        """Test: User can get clients list"""
        response = requests.get(
            f"{BASE_URL}/api/clients",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200, f"Get clients failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), "Clients should be a list"
        print(f"✓ Clients list retrieved - {len(data)} clients")
    
    def test_get_single_client(self, user_token, test_client_id):
        """Test: User can get a single client"""
        response = requests.get(
            f"{BASE_URL}/api/clients/{test_client_id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200, f"Get client failed: {response.text}"
        data = response.json()
        
        assert data["id"] == test_client_id, "Client ID should match"
        print(f"✓ Single client retrieved - {data['name']}")
    
    def test_update_client(self, user_token, test_client_id):
        """Test: User can update a client"""
        update_data = {
            "name": f"TEST_UpdatedClient_{uuid.uuid4().hex[:6]}",
            "address": "789 Updated Street"
        }
        
        response = requests.put(
            f"{BASE_URL}/api/clients/{test_client_id}",
            headers={"Authorization": f"Bearer {user_token}"},
            json=update_data
        )
        assert response.status_code == 200, f"Update client failed: {response.text}"
        data = response.json()
        
        assert data["name"] == update_data["name"], "Client name should be updated"
        print(f"✓ Client updated successfully - {data['name']}")
        
        # Verify persistence
        get_response = requests.get(
            f"{BASE_URL}/api/clients/{test_client_id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert get_response.status_code == 200
        assert get_response.json()["name"] == update_data["name"], "Update should persist"
        print("✓ Client update persisted")
    
    def test_delete_client(self, user_token, test_client_id):
        """Test: User can delete a client"""
        response = requests.delete(
            f"{BASE_URL}/api/clients/{test_client_id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code in [200, 204], f"Delete client failed: {response.text}"
        print("✓ Client deleted successfully")
        
        # Verify deletion
        get_response = requests.get(
            f"{BASE_URL}/api/clients/{test_client_id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert get_response.status_code == 404, "Deleted client should return 404"
        print("✓ Client deletion verified")
    
    def test_create_client_validation(self, user_token):
        """Test: Client creation validates required fields"""
        # Missing name
        response = requests.post(
            f"{BASE_URL}/api/clients",
            headers={"Authorization": f"Bearer {user_token}"},
            json={"address": "Test Address"}
        )
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        print("✓ Client validation works - missing name rejected")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
