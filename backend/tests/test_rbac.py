"""
RBAC (Role-Based Access Control) Tests for BTP Invoice Application
Tests the 3-role system: super_admin, admin, user
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
SUPER_ADMIN_EMAIL = "admin@btpfacture.com"
SUPER_ADMIN_PASSWORD = "Admin123!"
REGULAR_USER_EMAIL = f"test_user_{uuid.uuid4().hex[:8]}@test.com"
REGULAR_USER_PASSWORD = "Test1234!"
REGULAR_USER_NAME = "Test User RBAC"


class TestRBACBackend:
    """Test RBAC backend API access control"""
    
    @pytest.fixture(scope="class")
    def super_admin_token(self):
        """Get super admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Super admin login failed: {response.text}"
        data = response.json()
        assert data.get("user", {}).get("role") == "super_admin", "Super admin should have super_admin role"
        return data["access_token"]
    
    @pytest.fixture(scope="class")
    def regular_user_token(self, super_admin_token):
        """Create and get regular user token"""
        # First, register a new user
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": REGULAR_USER_EMAIL,
            "password": REGULAR_USER_PASSWORD,
            "name": REGULAR_USER_NAME
        })
        
        if response.status_code == 400 and "déjà utilisé" in response.text:
            # User already exists, try to login
            response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": REGULAR_USER_EMAIL,
                "password": REGULAR_USER_PASSWORD
            })
        
        assert response.status_code == 200, f"Regular user creation/login failed: {response.text}"
        data = response.json()
        assert data.get("user", {}).get("role") == "user", "New user should have 'user' role by default"
        return data["access_token"], data["user"]["id"]
    
    # ============== LOGIN ROLE TESTS ==============
    
    def test_login_returns_role_super_admin(self):
        """Test: Login returns role in response for super_admin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        
        # Verify role is returned
        assert "user" in data, "Response should contain user object"
        assert "role" in data["user"], "User object should contain role"
        assert data["user"]["role"] == "super_admin", "Super admin should have super_admin role"
        print(f"✓ Super admin login returns role: {data['user']['role']}")
    
    def test_login_returns_role_regular_user(self, regular_user_token):
        """Test: Login returns role in response for regular user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": REGULAR_USER_EMAIL,
            "password": REGULAR_USER_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        
        # Verify role is returned
        assert "user" in data, "Response should contain user object"
        assert "role" in data["user"], "User object should contain role"
        assert data["user"]["role"] == "user", "Regular user should have 'user' role"
        print(f"✓ Regular user login returns role: {data['user']['role']}")
    
    # ============== RBAC ACCESS CONTROL TESTS ==============
    
    def test_regular_user_cannot_access_users_list(self, regular_user_token):
        """Test: Regular user CANNOT access GET /api/users (should return 403)"""
        token, user_id = regular_user_token
        response = requests.get(
            f"{BASE_URL}/api/users",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403, f"Expected 403 Forbidden, got {response.status_code}: {response.text}"
        print("✓ Regular user correctly denied access to GET /api/users (403)")
    
    def test_regular_user_cannot_modify_settings(self, regular_user_token):
        """Test: Regular user CANNOT modify settings PUT /api/settings (should return 403)"""
        token, user_id = regular_user_token
        response = requests.put(
            f"{BASE_URL}/api/settings",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "company_name": "Test Company",
                "address": "123 Test Street"
            }
        )
        
        assert response.status_code == 403, f"Expected 403 Forbidden, got {response.status_code}: {response.text}"
        print("✓ Regular user correctly denied access to PUT /api/settings (403)")
    
    def test_super_admin_can_list_users(self, super_admin_token):
        """Test: Super admin CAN list users GET /api/users"""
        response = requests.get(
            f"{BASE_URL}/api/users",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list of users"
        assert len(data) > 0, "Should have at least one user (super admin)"
        
        # Verify user structure
        for user in data:
            assert "id" in user, "User should have id"
            assert "email" in user, "User should have email"
            assert "role" in user, "User should have role"
        
        print(f"✓ Super admin can list users - found {len(data)} users")
    
    def test_super_admin_can_update_user_role(self, super_admin_token, regular_user_token):
        """Test: Super admin CAN update user role PATCH /api/users/{id}/role"""
        token, user_id = regular_user_token
        
        # Change role to admin
        response = requests.patch(
            f"{BASE_URL}/api/users/{user_id}/role",
            headers={"Authorization": f"Bearer {super_admin_token}"},
            json={"role": "admin"}
        )
        
        assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("new_role") == "admin", "Role should be updated to admin"
        print(f"✓ Super admin can update user role to admin")
        
        # Change role back to user
        response = requests.patch(
            f"{BASE_URL}/api/users/{user_id}/role",
            headers={"Authorization": f"Bearer {super_admin_token}"},
            json={"role": "user"}
        )
        
        assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
        print(f"✓ Super admin can update user role back to user")
    
    def test_regular_user_cannot_update_roles(self, regular_user_token, super_admin_token):
        """Test: Regular user CANNOT update roles"""
        token, user_id = regular_user_token
        
        # Get another user to try to modify
        users_response = requests.get(
            f"{BASE_URL}/api/users",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        users = users_response.json()
        
        # Find a user that is not the current user
        target_user = None
        for u in users:
            if u["id"] != user_id:
                target_user = u
                break
        
        if target_user:
            response = requests.patch(
                f"{BASE_URL}/api/users/{target_user['id']}/role",
                headers={"Authorization": f"Bearer {token}"},
                json={"role": "admin"}
            )
            
            assert response.status_code == 403, f"Expected 403 Forbidden, got {response.status_code}: {response.text}"
            print("✓ Regular user correctly denied access to PATCH /api/users/{id}/role (403)")
        else:
            print("⚠ No other user found to test role update denial")
    
    def test_super_admin_cannot_be_modified_by_admin(self, super_admin_token, regular_user_token):
        """Test: Super admin role cannot be modified by regular admin"""
        token, user_id = regular_user_token
        
        # First, make the regular user an admin
        requests.patch(
            f"{BASE_URL}/api/users/{user_id}/role",
            headers={"Authorization": f"Bearer {super_admin_token}"},
            json={"role": "admin"}
        )
        
        # Re-login to get new token with admin role
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": REGULAR_USER_EMAIL,
            "password": REGULAR_USER_PASSWORD
        })
        admin_token = login_response.json()["access_token"]
        
        # Get super admin user id
        users_response = requests.get(
            f"{BASE_URL}/api/users",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        users = users_response.json()
        super_admin_user = next((u for u in users if u["role"] == "super_admin"), None)
        
        if super_admin_user:
            # Try to modify super admin role
            response = requests.patch(
                f"{BASE_URL}/api/users/{super_admin_user['id']}/role",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={"role": "user"}
            )
            
            assert response.status_code == 403, f"Expected 403 Forbidden, got {response.status_code}: {response.text}"
            print("✓ Admin correctly denied from modifying super_admin role (403)")
        
        # Reset user back to regular user
        requests.patch(
            f"{BASE_URL}/api/users/{user_id}/role",
            headers={"Authorization": f"Bearer {super_admin_token}"},
            json={"role": "user"}
        )
    
    def test_invalid_role_rejected(self, super_admin_token, regular_user_token):
        """Test: Invalid role values are rejected"""
        token, user_id = regular_user_token
        
        response = requests.patch(
            f"{BASE_URL}/api/users/{user_id}/role",
            headers={"Authorization": f"Bearer {super_admin_token}"},
            json={"role": "invalid_role"}
        )
        
        assert response.status_code == 422, f"Expected 422 Validation Error, got {response.status_code}: {response.text}"
        print("✓ Invalid role value correctly rejected (422)")
    
    # ============== USER MANAGEMENT TESTS ==============
    
    def test_super_admin_can_get_single_user(self, super_admin_token, regular_user_token):
        """Test: Super admin can get single user details"""
        token, user_id = regular_user_token
        
        response = requests.get(
            f"{BASE_URL}/api/users/{user_id}",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["id"] == user_id, "User ID should match"
        assert "role" in data, "User should have role field"
        print(f"✓ Super admin can get single user details")
    
    def test_super_admin_can_activate_deactivate_user(self, super_admin_token, regular_user_token):
        """Test: Super admin can activate/deactivate users"""
        token, user_id = regular_user_token
        
        # Deactivate user
        response = requests.patch(
            f"{BASE_URL}/api/users/{user_id}/deactivate",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200 OK for deactivate, got {response.status_code}: {response.text}"
        print("✓ Super admin can deactivate user")
        
        # Activate user
        response = requests.patch(
            f"{BASE_URL}/api/users/{user_id}/activate",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200 OK for activate, got {response.status_code}: {response.text}"
        print("✓ Super admin can activate user")
    
    def test_cannot_deactivate_super_admin(self, super_admin_token):
        """Test: Cannot deactivate super admin account"""
        # Get super admin user id
        users_response = requests.get(
            f"{BASE_URL}/api/users",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        users = users_response.json()
        super_admin_user = next((u for u in users if u["role"] == "super_admin"), None)
        
        if super_admin_user:
            response = requests.patch(
                f"{BASE_URL}/api/users/{super_admin_user['id']}/deactivate",
                headers={"Authorization": f"Bearer {super_admin_token}"}
            )
            
            assert response.status_code in [400, 403], f"Expected 400 or 403, got {response.status_code}: {response.text}"
            print("✓ Super admin account cannot be deactivated")


class TestRBACCleanup:
    """Cleanup test data"""
    
    def test_cleanup_test_user(self):
        """Clean up test user created during tests"""
        # Login as super admin
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        
        if response.status_code == 200:
            token = response.json()["access_token"]
            
            # Get all users
            users_response = requests.get(
                f"{BASE_URL}/api/users",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if users_response.status_code == 200:
                users = users_response.json()
                # Find and delete test users
                for user in users:
                    if user["email"].startswith("test_user_") and user["email"].endswith("@test.com"):
                        delete_response = requests.delete(
                            f"{BASE_URL}/api/users/{user['id']}",
                            headers={"Authorization": f"Bearer {token}"}
                        )
                        if delete_response.status_code == 200:
                            print(f"✓ Cleaned up test user: {user['email']}")
        
        print("✓ Cleanup completed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
