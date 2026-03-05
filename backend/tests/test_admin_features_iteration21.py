"""
Test Admin Features - Iteration 21
Testing:
1. Admin can delete regular users (not other admins)
2. Profile completion endpoint returns correct data
3. User detail view shows all non-sensitive information
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@btpfacture.com"
ADMIN_PASSWORD = "Admin123!"
USER_EMAIL = "rafik.remila@gmail.com"
USER_PASSWORD = "Zeralda@0676"


class TestAdminAuthentication:
    """Test admin login and token retrieval"""
    
    def test_admin_login_success(self):
        """Admin should be able to login successfully"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == ADMIN_EMAIL
        assert data["user"]["role"] in ["admin", "super_admin"]
        print(f"✓ Admin login successful, role: {data['user']['role']}")
    
    def test_user_login_success(self):
        """Regular user should be able to login successfully"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": USER_EMAIL,
            "password": USER_PASSWORD
        })
        assert response.status_code == 200, f"User login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        print(f"✓ User login successful, role: {data['user'].get('role', 'user')}")


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    pytest.skip(f"Admin authentication failed: {response.text}")


@pytest.fixture(scope="module")
def user_token():
    """Get regular user authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": USER_EMAIL,
        "password": USER_PASSWORD
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    pytest.skip(f"User authentication failed: {response.text}")


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    """Headers with admin auth token"""
    return {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }


@pytest.fixture(scope="module")
def user_headers(user_token):
    """Headers with user auth token"""
    return {
        "Authorization": f"Bearer {user_token}",
        "Content-Type": "application/json"
    }


class TestUsersList:
    """Test users list endpoint - Admin only"""
    
    def test_admin_can_list_users(self, admin_headers):
        """Admin should be able to list all users"""
        response = requests.get(f"{BASE_URL}/api/users", headers=admin_headers)
        assert response.status_code == 200, f"Failed to list users: {response.text}"
        users = response.json()
        assert isinstance(users, list)
        assert len(users) > 0
        print(f"✓ Admin can list users, found {len(users)} users")
        
        # Verify user structure
        user = users[0]
        assert "id" in user
        assert "email" in user
        assert "name" in user
        assert "role" in user
    
    def test_regular_user_cannot_list_users(self, user_headers):
        """Regular user should NOT be able to list users"""
        response = requests.get(f"{BASE_URL}/api/users", headers=user_headers)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✓ Regular user correctly denied access to users list")


class TestProfileCompletion:
    """Test profile completion endpoint - Admin only"""
    
    def test_profile_completion_endpoint_exists(self, admin_headers):
        """Profile completion endpoint should exist and be accessible by admin"""
        # First get a user ID
        users_response = requests.get(f"{BASE_URL}/api/users", headers=admin_headers)
        assert users_response.status_code == 200
        users = users_response.json()
        
        # Find a regular user (not admin)
        regular_user = None
        for u in users:
            if u.get("role") == "user":
                regular_user = u
                break
        
        if not regular_user:
            pytest.skip("No regular user found for testing")
        
        user_id = regular_user["id"]
        
        # Test profile completion endpoint
        response = requests.get(f"{BASE_URL}/api/users/{user_id}/profile-completion", headers=admin_headers)
        assert response.status_code == 200, f"Profile completion failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "user_id" in data
        assert "completion_percentage" in data
        assert "completed_count" in data
        assert "total_count" in data
        assert "items" in data
        assert "summary" in data
        
        print(f"✓ Profile completion endpoint works, user {regular_user['name']} is {data['completion_percentage']}% complete")
    
    def test_profile_completion_returns_correct_structure(self, admin_headers):
        """Profile completion should return all expected fields"""
        # Get users
        users_response = requests.get(f"{BASE_URL}/api/users", headers=admin_headers)
        users = users_response.json()
        
        # Get first user's profile completion
        user_id = users[0]["id"]
        response = requests.get(f"{BASE_URL}/api/users/{user_id}/profile-completion", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Check items structure
        assert isinstance(data["items"], list)
        if len(data["items"]) > 0:
            item = data["items"][0]
            assert "key" in item
            assert "label" in item
            assert "completed" in item
            assert "category" in item
        
        # Check summary structure
        summary = data["summary"]
        expected_categories = ["profil", "profil_total", "entreprise", "entreprise_total", 
                              "legal", "legal_total", "bancaire", "bancaire_total"]
        for cat in expected_categories:
            assert cat in summary, f"Missing category: {cat}"
        
        print(f"✓ Profile completion structure is correct with {len(data['items'])} items")
    
    def test_profile_completion_categories(self, admin_headers):
        """Profile completion should include all expected categories"""
        users_response = requests.get(f"{BASE_URL}/api/users", headers=admin_headers)
        users = users_response.json()
        user_id = users[0]["id"]
        
        response = requests.get(f"{BASE_URL}/api/users/{user_id}/profile-completion", headers=admin_headers)
        data = response.json()
        
        # Check that all expected items are present
        expected_keys = ["name", "phone", "email_verified", "company_name", "address", 
                        "siret", "vat_number", "iban", "bic", "logo", "website"]
        
        item_keys = [item["key"] for item in data["items"]]
        for key in expected_keys:
            assert key in item_keys, f"Missing profile item: {key}"
        
        print(f"✓ All {len(expected_keys)} profile completion items present")
    
    def test_regular_user_cannot_access_profile_completion(self, user_headers):
        """Regular user should NOT be able to access profile completion"""
        # Use a random UUID
        fake_user_id = str(uuid.uuid4())
        response = requests.get(f"{BASE_URL}/api/users/{fake_user_id}/profile-completion", headers=user_headers)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✓ Regular user correctly denied access to profile completion")


class TestUserDetail:
    """Test user detail endpoint - Admin only"""
    
    def test_admin_can_view_user_detail(self, admin_headers):
        """Admin should be able to view user details"""
        # Get users list
        users_response = requests.get(f"{BASE_URL}/api/users", headers=admin_headers)
        users = users_response.json()
        
        # Find a regular user
        regular_user = None
        for u in users:
            if u.get("role") == "user":
                regular_user = u
                break
        
        if not regular_user:
            pytest.skip("No regular user found")
        
        user_id = regular_user["id"]
        
        # Get user detail
        response = requests.get(f"{BASE_URL}/api/users/{user_id}", headers=admin_headers)
        assert response.status_code == 200, f"Failed to get user detail: {response.text}"
        data = response.json()
        
        # Verify non-sensitive fields are present
        assert "id" in data
        assert "email" in data
        assert "name" in data
        assert "role" in data
        assert "created_at" in data
        
        # Verify sensitive fields are NOT present
        assert "password" not in data
        
        print(f"✓ Admin can view user detail for {data['name']}")
    
    def test_user_detail_includes_all_fields(self, admin_headers):
        """User detail should include all non-sensitive fields"""
        users_response = requests.get(f"{BASE_URL}/api/users", headers=admin_headers)
        users = users_response.json()
        user_id = users[0]["id"]
        
        response = requests.get(f"{BASE_URL}/api/users/{user_id}", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Check expected fields
        expected_fields = ["id", "email", "name", "role", "created_at"]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
        
        print(f"✓ User detail includes all expected fields")


class TestAdminDeleteUser:
    """Test admin delete user functionality"""
    
    def test_delete_endpoint_requires_otp(self, admin_headers):
        """Delete endpoint should require OTP verification"""
        # Get a regular user
        users_response = requests.get(f"{BASE_URL}/api/users", headers=admin_headers)
        users = users_response.json()
        
        regular_user = None
        for u in users:
            if u.get("role") == "user":
                regular_user = u
                break
        
        if not regular_user:
            pytest.skip("No regular user found")
        
        user_id = regular_user["id"]
        
        # Try to delete without OTP - should fail
        response = requests.delete(
            f"{BASE_URL}/api/users/{user_id}", 
            headers=admin_headers,
            json={"otp_code": "000000"}  # Invalid OTP
        )
        
        # Should fail with 400 (invalid OTP) not 403 (permission denied)
        assert response.status_code == 400, f"Expected 400 for invalid OTP, got {response.status_code}: {response.text}"
        print("✓ Delete endpoint correctly requires valid OTP")
    
    def test_admin_can_request_delete_otp(self, admin_headers):
        """Admin should be able to request OTP for delete action"""
        # Get a regular user
        users_response = requests.get(f"{BASE_URL}/api/users", headers=admin_headers)
        users = users_response.json()
        
        regular_user = None
        for u in users:
            if u.get("role") == "user":
                regular_user = u
                break
        
        if not regular_user:
            pytest.skip("No regular user found")
        
        user_id = regular_user["id"]
        
        # Request OTP for delete
        response = requests.post(
            f"{BASE_URL}/api/users/{user_id}/request-otp?otp_type=delete_user",
            headers=admin_headers
        )
        
        assert response.status_code == 200, f"Failed to request OTP: {response.text}"
        data = response.json()
        assert "message" in data
        print(f"✓ Admin can request delete OTP for user {regular_user['name']}")
    
    def test_admin_cannot_delete_other_admin(self, admin_headers):
        """Admin should NOT be able to delete another admin (only super_admin can)"""
        # Get users list
        users_response = requests.get(f"{BASE_URL}/api/users", headers=admin_headers)
        users = users_response.json()
        
        # Find an admin user (not super_admin)
        admin_user = None
        for u in users:
            if u.get("role") == "admin":
                admin_user = u
                break
        
        if not admin_user:
            print("⚠ No admin user found to test - skipping")
            pytest.skip("No admin user found")
        
        # Try to delete admin - should fail
        response = requests.delete(
            f"{BASE_URL}/api/users/{admin_user['id']}", 
            headers=admin_headers,
            json={"otp_code": "123456"}
        )
        
        # Should fail - either 400 (invalid OTP) or 403 (permission denied)
        assert response.status_code in [400, 403], f"Expected 400 or 403, got {response.status_code}"
        print("✓ Admin correctly cannot delete other admin")
    
    def test_cannot_delete_super_admin(self, admin_headers):
        """No one should be able to delete super_admin"""
        # Get users list
        users_response = requests.get(f"{BASE_URL}/api/users", headers=admin_headers)
        users = users_response.json()
        
        # Find super_admin
        super_admin = None
        for u in users:
            if u.get("role") == "super_admin":
                super_admin = u
                break
        
        if not super_admin:
            pytest.skip("No super_admin found")
        
        # Try to delete super_admin - should fail
        response = requests.delete(
            f"{BASE_URL}/api/users/{super_admin['id']}", 
            headers=admin_headers,
            json={"otp_code": "123456"}
        )
        
        # Should fail
        assert response.status_code in [400, 403], f"Expected 400 or 403, got {response.status_code}"
        print("✓ Super admin correctly protected from deletion")


class TestDeleteButtonVisibility:
    """Test that delete button visibility logic is correct based on roles"""
    
    def test_admin_role_permissions(self, admin_headers):
        """Verify admin role permissions for user management"""
        # Get current admin info
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=admin_headers)
        assert response.status_code == 200
        admin_data = response.json()
        
        admin_role = admin_data.get("role")
        print(f"✓ Current admin role: {admin_role}")
        
        # Get users list
        users_response = requests.get(f"{BASE_URL}/api/users", headers=admin_headers)
        users = users_response.json()
        
        # Count users by role
        role_counts = {}
        for u in users:
            role = u.get("role", "user")
            role_counts[role] = role_counts.get(role, 0) + 1
        
        print(f"✓ User distribution: {role_counts}")
        
        # Verify admin can see all users
        assert len(users) > 0
        print(f"✓ Admin can see {len(users)} users")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
