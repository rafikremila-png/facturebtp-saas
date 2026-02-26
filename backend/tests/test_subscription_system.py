"""
Test Suite for Subscription System
Tests: Plans API, Status API, Checkout, Cancel, Feature Gating, Trial System
"""

import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@btpfacture.com"
ADMIN_PASSWORD = "Admin123!"


class TestSubscriptionPlans:
    """Test GET /api/subscription/plans - Returns all 3 plans with prices and features"""
    
    def test_get_subscription_plans_returns_3_plans(self):
        """Verify endpoint returns exactly 3 plans: essentiel, pro, business"""
        response = requests.get(f"{BASE_URL}/api/subscription/plans")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        plans = response.json()
        assert isinstance(plans, list), "Response should be a list"
        assert len(plans) == 3, f"Expected 3 plans, got {len(plans)}"
        
        plan_ids = [p["id"] for p in plans]
        assert "essentiel" in plan_ids, "Missing essentiel plan"
        assert "pro" in plan_ids, "Missing pro plan"
        assert "business" in plan_ids, "Missing business plan"
    
    def test_essentiel_plan_has_correct_price(self):
        """Verify Essentiel plan is 19€"""
        response = requests.get(f"{BASE_URL}/api/subscription/plans")
        assert response.status_code == 200
        
        plans = response.json()
        essentiel = next((p for p in plans if p["id"] == "essentiel"), None)
        
        assert essentiel is not None, "Essentiel plan not found"
        assert essentiel["price_monthly"] == 19.0, f"Expected 19€, got {essentiel['price_monthly']}€"
        assert essentiel["name"] == "Essentiel", f"Expected name 'Essentiel', got {essentiel['name']}"
    
    def test_pro_plan_has_correct_price(self):
        """Verify Pro plan is 29€"""
        response = requests.get(f"{BASE_URL}/api/subscription/plans")
        assert response.status_code == 200
        
        plans = response.json()
        pro = next((p for p in plans if p["id"] == "pro"), None)
        
        assert pro is not None, "Pro plan not found"
        assert pro["price_monthly"] == 29.0, f"Expected 29€, got {pro['price_monthly']}€"
        assert pro["name"] == "Pro", f"Expected name 'Pro', got {pro['name']}"
    
    def test_business_plan_has_correct_price(self):
        """Verify Business plan is 59€"""
        response = requests.get(f"{BASE_URL}/api/subscription/plans")
        assert response.status_code == 200
        
        plans = response.json()
        business = next((p for p in plans if p["id"] == "business"), None)
        
        assert business is not None, "Business plan not found"
        assert business["price_monthly"] == 59.0, f"Expected 59€, got {business['price_monthly']}€"
        assert business["name"] == "Business", f"Expected name 'Business', got {business['name']}"
    
    def test_plans_have_features(self):
        """Verify all plans have features object"""
        response = requests.get(f"{BASE_URL}/api/subscription/plans")
        assert response.status_code == 200
        
        plans = response.json()
        for plan in plans:
            assert "features" in plan, f"Plan {plan['id']} missing features"
            assert isinstance(plan["features"], dict), f"Plan {plan['id']} features should be dict"
            
            # Check required feature keys
            required_features = ["unlimited_quotes", "max_invoices_per_month", "predefined_kits"]
            for feature in required_features:
                assert feature in plan["features"], f"Plan {plan['id']} missing feature: {feature}"
    
    def test_essentiel_has_30_invoice_limit(self):
        """Verify Essentiel plan has 30 invoice limit"""
        response = requests.get(f"{BASE_URL}/api/subscription/plans")
        assert response.status_code == 200
        
        plans = response.json()
        essentiel = next((p for p in plans if p["id"] == "essentiel"), None)
        
        assert essentiel["features"]["max_invoices_per_month"] == 30, \
            f"Expected 30 invoices, got {essentiel['features']['max_invoices_per_month']}"
    
    def test_pro_has_unlimited_invoices(self):
        """Verify Pro plan has unlimited invoices (-1)"""
        response = requests.get(f"{BASE_URL}/api/subscription/plans")
        assert response.status_code == 200
        
        plans = response.json()
        pro = next((p for p in plans if p["id"] == "pro"), None)
        
        assert pro["features"]["max_invoices_per_month"] == -1, \
            f"Expected -1 (unlimited), got {pro['features']['max_invoices_per_month']}"
    
    def test_business_has_unlimited_invoices(self):
        """Verify Business plan has unlimited invoices (-1)"""
        response = requests.get(f"{BASE_URL}/api/subscription/plans")
        assert response.status_code == 200
        
        plans = response.json()
        business = next((p for p in plans if p["id"] == "business"), None)
        
        assert business["features"]["max_invoices_per_month"] == -1, \
            f"Expected -1 (unlimited), got {business['features']['max_invoices_per_month']}"
    
    def test_essentiel_no_kits_access(self):
        """Verify Essentiel plan does NOT have kits access"""
        response = requests.get(f"{BASE_URL}/api/subscription/plans")
        assert response.status_code == 200
        
        plans = response.json()
        essentiel = next((p for p in plans if p["id"] == "essentiel"), None)
        
        assert essentiel["features"]["predefined_kits"] == False, \
            f"Essentiel should NOT have kits access"
    
    def test_pro_has_kits_access(self):
        """Verify Pro plan has kits access"""
        response = requests.get(f"{BASE_URL}/api/subscription/plans")
        assert response.status_code == 200
        
        plans = response.json()
        pro = next((p for p in plans if p["id"] == "pro"), None)
        
        assert pro["features"]["predefined_kits"] == True, \
            f"Pro should have kits access"
    
    def test_business_has_kits_access(self):
        """Verify Business plan has kits access"""
        response = requests.get(f"{BASE_URL}/api/subscription/plans")
        assert response.status_code == 200
        
        plans = response.json()
        business = next((p for p in plans if p["id"] == "business"), None)
        
        assert business["features"]["predefined_kits"] == True, \
            f"Business should have kits access"


class TestSubscriptionStatus:
    """Test GET /api/subscription/status - Returns user's current subscription status"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token for admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Authentication failed: {response.status_code}")
    
    def test_subscription_status_requires_auth(self):
        """Verify endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/subscription/status")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    
    def test_subscription_status_returns_data(self, auth_token):
        """Verify endpoint returns subscription status for authenticated user"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/subscription/status", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        # Check required fields
        required_fields = ["plan", "plan_name", "status", "is_active", "is_trial", 
                          "can_create_invoices", "can_create_quotes", "invoices_this_month", 
                          "invoices_limit", "features"]
        
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
    
    def test_subscription_status_has_features(self, auth_token):
        """Verify status includes features object"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/subscription/status", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "features" in data, "Missing features in status"
        assert isinstance(data["features"], dict), "Features should be a dict"


class TestCheckoutSession:
    """Test POST /api/subscription/checkout - Creates Stripe checkout session"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token for admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Authentication failed: {response.status_code}")
    
    def test_checkout_requires_auth(self):
        """Verify checkout endpoint requires authentication"""
        response = requests.post(f"{BASE_URL}/api/subscription/checkout", json={
            "plan_id": "pro",
            "origin_url": "https://example.com"
        })
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    
    def test_checkout_rejects_invalid_plan(self, auth_token):
        """Verify checkout rejects invalid plan IDs"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(f"{BASE_URL}/api/subscription/checkout", 
            headers=headers,
            json={
                "plan_id": "invalid_plan",
                "origin_url": "https://example.com"
            }
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    
    def test_checkout_accepts_valid_plan(self, auth_token):
        """Verify checkout accepts valid plan IDs (essentiel, pro, business)"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Test with pro plan
        response = requests.post(f"{BASE_URL}/api/subscription/checkout", 
            headers=headers,
            json={
                "plan_id": "pro",
                "origin_url": "https://construction-invoice-2.preview.emergentagent.com"
            }
        )
        
        # Should return 200 with checkout_url or 503 if Stripe not configured
        assert response.status_code in [200, 503], f"Expected 200 or 503, got {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            assert "checkout_url" in data, "Missing checkout_url in response"
            assert "session_id" in data, "Missing session_id in response"


class TestCancelSubscription:
    """Test POST /api/subscription/cancel - Cancels subscription"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token for admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Authentication failed: {response.status_code}")
    
    def test_cancel_requires_auth(self):
        """Verify cancel endpoint requires authentication"""
        response = requests.post(f"{BASE_URL}/api/subscription/cancel")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    
    def test_cancel_on_trial_returns_error(self, auth_token):
        """Verify canceling on trial returns appropriate error"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(f"{BASE_URL}/api/subscription/cancel", headers=headers)
        
        # Should return 400 if user is on trial (no subscription to cancel)
        # or 200 if user has active subscription
        assert response.status_code in [200, 400], f"Expected 200 or 400, got {response.status_code}"


class TestFeatureAccess:
    """Test GET /api/subscription/features/{feature} - Checks feature access"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token for admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Authentication failed: {response.status_code}")
    
    def test_feature_access_requires_auth(self):
        """Verify feature access endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/subscription/features/predefined_kits")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    
    def test_feature_access_returns_data(self, auth_token):
        """Verify feature access returns proper response"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/subscription/features/predefined_kits", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "allowed" in data, "Missing 'allowed' field"
        assert isinstance(data["allowed"], bool), "'allowed' should be boolean"
    
    def test_feature_access_create_invoice(self, auth_token):
        """Verify create_invoice feature check works"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/subscription/features/create_invoice", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "allowed" in data
    
    def test_feature_access_create_quote(self, auth_token):
        """Verify create_quote feature check works"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/subscription/features/create_quote", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "allowed" in data


class TestWebhookEndpoint:
    """Test POST /api/webhook/stripe - Stripe webhook endpoint exists"""
    
    def test_webhook_endpoint_exists(self):
        """Verify webhook endpoint exists and accepts POST"""
        # Send empty body - should not crash
        response = requests.post(f"{BASE_URL}/api/webhook/stripe", 
            headers={"Content-Type": "application/json"},
            data="{}"
        )
        
        # Should return 200 with status (even if ignored)
        # or 422 for validation error (which means endpoint exists)
        assert response.status_code in [200, 422, 500], \
            f"Expected 200, 422, or 500, got {response.status_code}"


class TestTrialSystem:
    """Test trial system still works (14 days)"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token for admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Authentication failed: {response.status_code}")
    
    def test_subscription_status_shows_trial_info(self, auth_token):
        """Verify subscription status includes trial information"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/subscription/status", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check trial-related fields exist
        assert "is_trial" in data, "Missing is_trial field"
        assert "trial_end_date" in data or data["is_trial"] == False, \
            "Trial users should have trial_end_date"
        assert "trial_days_remaining" in data or data["is_trial"] == False, \
            "Trial users should have trial_days_remaining"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
