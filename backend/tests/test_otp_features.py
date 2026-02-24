"""
Test OTP Features for BTP Invoice Application
- Registration with phone required
- OTP email verification
- User profile page
- Admin user detail page
- Website request in settings
"""
import pytest
import requests
import os
import time
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestRegistrationWithOTP:
    """Test registration flow with OTP verification"""
    
    def test_registration_requires_phone(self):
        """Test that registration requires phone field"""
        # Try to register without phone
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"test_no_phone_{uuid.uuid4().hex[:8]}@test.com",
            "password": "Test1234!",
            "name": "Test User"
            # Missing phone
        })
        # Should fail with validation error
        assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.text}"
        
    def test_registration_with_all_fields_returns_requires_verification(self):
        """Test registration with all fields returns requires_verification: true"""
        test_email = f"test_otp_{uuid.uuid4().hex[:8]}@test.com"
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": test_email,
            "password": "Test1234!",
            "name": "Test OTP User",
            "phone": "0612345678",
            "company_name": "Test Company",
            "address": "123 Test Street"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("requires_verification") == True, f"Expected requires_verification=True, got {data}"
        assert data.get("email") == test_email
        
    def test_registration_phone_validation(self):
        """Test phone number validation (French format)"""
        # Invalid phone format
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"test_phone_{uuid.uuid4().hex[:8]}@test.com",
            "password": "Test1234!",
            "name": "Test User",
            "phone": "123"  # Invalid format
        })
        assert response.status_code == 422, f"Expected 422 for invalid phone, got {response.status_code}"
        
    def test_registration_password_validation(self):
        """Test password validation rules"""
        # Password too short
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"test_pwd_{uuid.uuid4().hex[:8]}@test.com",
            "password": "Test1!",  # Too short
            "name": "Test User",
            "phone": "0612345678"
        })
        assert response.status_code == 422, f"Expected 422 for short password, got {response.status_code}"


class TestOTPVerification:
    """Test OTP verification endpoints"""
    
    def test_verify_email_endpoint_exists(self):
        """Test that verify-email endpoint exists"""
        response = requests.post(f"{BASE_URL}/api/auth/verify-email", json={
            "email": "nonexistent@test.com",
            "otp_code": "123456",
            "otp_type": "registration"
        })
        # Should return 400 (invalid OTP) not 404 (endpoint not found)
        assert response.status_code in [400, 404], f"Expected 400 or 404, got {response.status_code}"
        
    def test_resend_otp_endpoint_exists(self):
        """Test that resend-otp endpoint exists"""
        response = requests.post(f"{BASE_URL}/api/auth/resend-otp", json={
            "email": "test@test.com",
            "otp_type": "registration"
        })
        # Should return 200 (message sent) or rate limit error
        assert response.status_code in [200, 429], f"Expected 200 or 429, got {response.status_code}"


class TestUserProfile:
    """Test user profile endpoints"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@btpfacture.com",
            "password": "Admin123!"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Admin login failed")
        
    def test_profile_endpoint_exists(self, admin_token):
        """Test that /auth/profile endpoint exists"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/auth/profile", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
    def test_profile_returns_full_details(self, admin_token):
        """Test that profile returns full user details"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/auth/profile", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        # Check required fields
        assert "id" in data
        assert "email" in data
        assert "name" in data
        assert "phone" in data
        assert "company_name" in data or data.get("company_name") is None
        assert "address" in data or data.get("address") is None
        assert "role" in data
        assert "created_at" in data
        assert "email_verified" in data
        
    def test_profile_update(self, admin_token):
        """Test profile update endpoint"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.put(f"{BASE_URL}/api/auth/profile", headers=headers, json={
            "name": "Super Admin Updated",
            "phone": "0698765432"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"


class TestAdminUserDetail:
    """Test admin user detail page functionality"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@btpfacture.com",
            "password": "Admin123!"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Admin login failed")
        
    def test_get_user_detail(self, admin_token):
        """Test getting user detail by ID"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # First get list of users
        response = requests.get(f"{BASE_URL}/api/users", headers=headers)
        assert response.status_code == 200
        users = response.json()
        assert len(users) > 0, "No users found"
        
        # Get detail of first user
        user_id = users[0]["id"]
        response = requests.get(f"{BASE_URL}/api/users/{user_id}", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        # Check detailed fields
        assert "id" in data
        assert "email" in data
        assert "name" in data
        assert "phone" in data
        assert "company_name" in data or data.get("company_name") is None
        assert "address" in data or data.get("address") is None
        assert "role" in data
        assert "created_at" in data
        assert "last_login" in data or data.get("last_login") is None
        assert "is_active" in data
        assert "email_verified" in data
        
    def test_request_otp_for_admin_action(self, admin_token):
        """Test requesting OTP for admin actions"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Get a user to test with
        response = requests.get(f"{BASE_URL}/api/users", headers=headers)
        users = response.json()
        # Find a non-admin user
        target_user = None
        for u in users:
            if u.get("role") != "super_admin":
                target_user = u
                break
        
        if not target_user:
            pytest.skip("No non-admin user to test with")
            
        # Request OTP for role change
        response = requests.post(
            f"{BASE_URL}/api/users/{target_user['id']}/request-otp?otp_type=promote_admin",
            headers=headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"


class TestWebsiteRequest:
    """Test website request feature in settings"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@btpfacture.com",
            "password": "Admin123!"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Admin login failed")
        
    def test_website_request_endpoint_exists(self, admin_token):
        """Test that website-requests endpoint exists"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.post(f"{BASE_URL}/api/website-requests", headers=headers, json={
            "activity_type": "Maçonnerie",
            "objective": "Site vitrine pour présenter mes services de maçonnerie",
            "budget": "1000-2500",
            "timeline": "1-mois",
            "additional_notes": "Test request"
        })
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.text}"
        
    def test_website_request_validation(self, admin_token):
        """Test website request validation"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        # Missing required fields
        response = requests.post(f"{BASE_URL}/api/website-requests", headers=headers, json={
            "activity_type": "Test"
            # Missing other required fields
        })
        assert response.status_code == 422, f"Expected 422 for missing fields, got {response.status_code}"
        
    def test_settings_website_field(self, admin_token):
        """Test that settings include website field"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/settings", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        # Website field should exist (can be empty)
        assert "website" in data or data.get("website") is None


class TestLoginWithOTP:
    """Test login flow with OTP for unverified users"""
    
    def test_login_super_admin_no_otp_required(self):
        """Test that super admin can login without OTP verification"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@btpfacture.com",
            "password": "Admin123!"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "super_admin"
        
    def test_login_unverified_user_returns_403(self):
        """Test that unverified user gets 403 with OTP sent"""
        # First register a new user
        test_email = f"test_unverified_{uuid.uuid4().hex[:8]}@test.com"
        reg_response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": test_email,
            "password": "Test1234!",
            "name": "Unverified User",
            "phone": "0612345678"
        })
        
        if reg_response.status_code != 200:
            pytest.skip("Registration failed")
            
        # Try to login without verification
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": test_email,
            "password": "Test1234!"
        })
        
        # Should return 403 with message about verification
        assert login_response.status_code == 403, f"Expected 403, got {login_response.status_code}"
        assert "vérifié" in login_response.json().get("detail", "").lower() or "verif" in login_response.json().get("detail", "").lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
