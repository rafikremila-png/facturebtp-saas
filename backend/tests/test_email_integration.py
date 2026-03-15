"""
Test Email Integration for BTP Facture
Tests: Email status endpoint, email API endpoints structure
Note: RESEND_API_KEY is a test key - actual email sending will fail but API structure should work
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestEmailStatus:
    """Test email configuration status endpoints"""
    
    def test_health_endpoint_email_configured(self):
        """GET /api/health should return email_configured: true"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert "email_configured" in data
        assert data["email_configured"] == True
        assert data["status"] == "ok"
        print(f"Health check passed: {data}")
    
    def test_email_status_endpoint(self):
        """GET /api/email/status should return configured: true, provider: resend"""
        response = requests.get(f"{BASE_URL}/api/email/status")
        assert response.status_code == 200
        data = response.json()
        assert data["configured"] == True
        assert data["provider"] == "resend"
        assert data["sender"] == "facturation@facturebtp.fr"
        print(f"Email status passed: {data}")


class TestEmailEndpointsStructure:
    """Test email API endpoints exist and respond appropriately"""
    
    def test_invoice_email_requires_auth(self):
        """POST /api/email/invoice should require authentication"""
        response = requests.post(f"{BASE_URL}/api/email/invoice", json={
            "invoice_id": "test-id",
            "client_email": "test@test.com"
        })
        # Should return 401 without auth token
        assert response.status_code == 401
        print(f"Invoice email auth check passed: {response.status_code}")
    
    def test_reminder_endpoint_requires_auth(self):
        """POST /api/email/reminder should require authentication"""
        response = requests.post(f"{BASE_URL}/api/email/reminder", json={
            "invoice_id": "test-id"
        })
        assert response.status_code == 401
        print(f"Reminder endpoint auth check passed: {response.status_code}")
    
    def test_payment_confirmation_requires_auth(self):
        """POST /api/email/payment-confirmation should require authentication"""
        response = requests.post(f"{BASE_URL}/api/email/payment-confirmation", json={
            "invoice_id": "test-id"
        })
        assert response.status_code == 401
        print(f"Payment confirmation auth check passed: {response.status_code}")
    
    def test_check_reminders_requires_auth(self):
        """POST /api/email/check-reminders should require authentication"""
        response = requests.post(f"{BASE_URL}/api/email/check-reminders")
        assert response.status_code == 401
        print(f"Check reminders auth check passed: {response.status_code}")
    
    def test_welcome_email_endpoint_structure(self):
        """POST /api/email/welcome should accept email parameter"""
        response = requests.post(f"{BASE_URL}/api/email/welcome", json={
            "email": "test@test.com"
        })
        # With test key, it should return 500 (Resend API error) but not 401 (no auth required)
        assert response.status_code in [200, 500]
        print(f"Welcome email endpoint structure passed: {response.status_code}")
    
    def test_otp_email_endpoint_structure(self):
        """POST /api/email/otp should accept email and code parameters"""
        response = requests.post(f"{BASE_URL}/api/email/otp", json={
            "email": "test@test.com",
            "code": "123456"
        })
        # With test key, it should return 500 (Resend API error) but not 422 (validation error)
        assert response.status_code in [200, 500]
        print(f"OTP email endpoint structure passed: {response.status_code}")


class TestEmailEndpointValidation:
    """Test email endpoint validation"""
    
    def test_invoice_email_validation(self):
        """POST /api/email/invoice should validate required fields"""
        # Missing client_email
        response = requests.post(f"{BASE_URL}/api/email/invoice", json={
            "invoice_id": "test-id"
        })
        # Should return 422 (validation error) or 401 (auth required first)
        assert response.status_code in [401, 422]
        print(f"Invoice email validation passed: {response.status_code}")
    
    def test_otp_email_validation(self):
        """POST /api/email/otp should validate required fields"""
        # Missing code
        response = requests.post(f"{BASE_URL}/api/email/otp", json={
            "email": "test@test.com"
        })
        # Should return 422 (validation error)
        assert response.status_code == 422
        print(f"OTP email validation passed: {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
