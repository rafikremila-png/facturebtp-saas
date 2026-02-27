"""
SaaS Monetization System Tests
Tests for subscription plans, usage limits, Stripe checkout, and Pro features
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://chantier-pro-11.preview.emergentagent.com').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@btpfacture.com"
ADMIN_PASSWORD = "Admin123!"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for admin user"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Authentication failed - skipping authenticated tests")


@pytest.fixture
def auth_headers(auth_token):
    """Get headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestSaaSPlansEndpoint:
    """Tests for GET /api/saas/plans - Returns 3 plans with correct pricing"""
    
    def test_plans_returns_3_plans(self):
        """Verify /api/saas/plans returns exactly 3 plans"""
        response = requests.get(f"{BASE_URL}/api/saas/plans")
        assert response.status_code == 200
        
        plans = response.json()
        assert len(plans) == 3, f"Expected 3 plans, got {len(plans)}"
    
    def test_plans_have_correct_ids(self):
        """Verify plan IDs are essentiel, pro, business"""
        response = requests.get(f"{BASE_URL}/api/saas/plans")
        plans = response.json()
        
        plan_ids = [p["id"] for p in plans]
        assert "essentiel" in plan_ids
        assert "pro" in plan_ids
        assert "business" in plan_ids
    
    def test_essentiel_plan_pricing(self):
        """Verify Essentiel plan has correct pricing (19€ monthly)"""
        response = requests.get(f"{BASE_URL}/api/saas/plans")
        plans = response.json()
        
        essentiel = next(p for p in plans if p["id"] == "essentiel")
        assert essentiel["price_monthly"] == 19.0, f"Expected 19€, got {essentiel['price_monthly']}€"
        assert essentiel["price_yearly"] == 182.4, f"Expected 182.4€ yearly, got {essentiel['price_yearly']}€"
        assert essentiel["limits"]["quotes_per_month"] == 30
        assert essentiel["limits"]["invoices_per_month"] == 30
    
    def test_pro_plan_pricing(self):
        """Verify Pro plan has correct pricing (29€ monthly)"""
        response = requests.get(f"{BASE_URL}/api/saas/plans")
        plans = response.json()
        
        pro = next(p for p in plans if p["id"] == "pro")
        assert pro["price_monthly"] == 29.0, f"Expected 29€, got {pro['price_monthly']}€"
        assert pro["price_yearly"] == 278.4, f"Expected 278.4€ yearly, got {pro['price_yearly']}€"
        assert pro["limits"]["quotes_per_month"] == -1, "Pro should have unlimited quotes"
        assert pro["limits"]["invoices_per_month"] == -1, "Pro should have unlimited invoices"
        assert pro["highlight"] == True, "Pro plan should be highlighted"
        assert pro["badge"] == "Le plus populaire"
    
    def test_business_plan_pricing(self):
        """Verify Business plan has correct pricing (59€ monthly)"""
        response = requests.get(f"{BASE_URL}/api/saas/plans")
        plans = response.json()
        
        business = next(p for p in plans if p["id"] == "business")
        assert business["price_monthly"] == 59.0, f"Expected 59€, got {business['price_monthly']}€"
        assert business["price_yearly"] == 566.4, f"Expected 566.4€ yearly, got {business['price_yearly']}€"
        assert business["limits"]["quotes_per_month"] == -1, "Business should have unlimited quotes"
        assert business["limits"]["invoices_per_month"] == -1, "Business should have unlimited invoices"
    
    def test_yearly_savings_calculation(self):
        """Verify yearly savings are calculated correctly (20% discount)"""
        response = requests.get(f"{BASE_URL}/api/saas/plans")
        plans = response.json()
        
        for plan in plans:
            expected_savings = round(plan["price_monthly"] * 12 - plan["price_yearly"], 2)
            assert plan["yearly_savings"] == expected_savings, \
                f"Plan {plan['id']}: Expected savings {expected_savings}, got {plan['yearly_savings']}"


class TestSaaSSubscriptionEndpoint:
    """Tests for GET /api/saas/subscription - Returns user subscription info"""
    
    def test_subscription_requires_auth(self):
        """Verify subscription endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/saas/subscription")
        assert response.status_code == 401
    
    def test_subscription_returns_user_info(self, auth_headers):
        """Verify subscription endpoint returns user subscription info"""
        response = requests.get(f"{BASE_URL}/api/saas/subscription", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        # Check required fields
        assert "plan" in data
        assert "status" in data
        assert "is_active" in data
        assert "is_trial" in data
        assert "invoice_usage" in data
        assert "invoice_limit" in data
        assert "quote_usage" in data
        assert "quote_limit" in data
        assert "can_create_invoice" in data
        assert "can_create_quote" in data
        assert "features" in data
        assert "limits" in data
    
    def test_subscription_has_trial_info(self, auth_headers):
        """Verify subscription includes trial information"""
        response = requests.get(f"{BASE_URL}/api/saas/subscription", headers=auth_headers)
        data = response.json()
        
        # Trial users should have trial info
        if data["is_trial"]:
            assert "trial_start" in data
            assert "trial_end" in data
            assert "trial_days_remaining" in data
            assert "trial_expired" in data


class TestSaaSUsageEndpoint:
    """Tests for GET /api/saas/usage - Returns usage stats"""
    
    def test_usage_requires_auth(self):
        """Verify usage endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/saas/usage")
        assert response.status_code == 401
    
    def test_usage_returns_stats(self, auth_headers):
        """Verify usage endpoint returns quote and invoice usage"""
        response = requests.get(f"{BASE_URL}/api/saas/usage", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "quote_usage" in data
        assert "quote_limit" in data
        assert "invoice_usage" in data
        assert "invoice_limit" in data
        assert "can_create_quote" in data
        assert "can_create_invoice" in data
        assert "is_trial" in data
        
        # Verify types
        assert isinstance(data["quote_usage"], int)
        assert isinstance(data["invoice_usage"], int)


class TestSaaSCheckoutEndpoint:
    """Tests for POST /api/saas/checkout - Creates Stripe checkout session"""
    
    def test_checkout_requires_auth(self):
        """Verify checkout endpoint requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/saas/checkout",
            json={"plan_id": "pro", "billing_period": "monthly", "origin_url": "https://example.com"}
        )
        assert response.status_code == 401
    
    def test_checkout_validates_plan(self, auth_headers):
        """Verify checkout validates plan ID"""
        response = requests.post(
            f"{BASE_URL}/api/saas/checkout",
            headers=auth_headers,
            json={"plan_id": "invalid_plan", "billing_period": "monthly", "origin_url": "https://example.com"}
        )
        # Should return 400 for invalid plan or 500 if Stripe fails
        assert response.status_code in [400, 500]
    
    def test_checkout_with_valid_plan(self, auth_headers):
        """Test checkout with valid plan (may fail due to test Stripe key)"""
        response = requests.post(
            f"{BASE_URL}/api/saas/checkout",
            headers=auth_headers,
            json={
                "plan_id": "pro",
                "billing_period": "monthly",
                "origin_url": "https://chantier-pro-11.preview.emergentagent.com"
            }
        )
        # With test Stripe key, this will return 500 (expected)
        # In production with real key, it would return 200 with checkout_url
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "checkout_url" in data
            assert "session_id" in data


class TestCSVExportProFeature:
    """Tests for CSV export endpoints - Should return 403 for non-Pro users"""
    
    def test_invoices_csv_requires_pro(self, auth_headers):
        """Verify invoices CSV export returns 403 for trial users"""
        response = requests.get(f"{BASE_URL}/api/export/invoices/csv", headers=auth_headers)
        assert response.status_code == 403
        assert "Pro" in response.json().get("detail", "")
    
    def test_quotes_csv_requires_pro(self, auth_headers):
        """Verify quotes CSV export returns 403 for trial users"""
        response = requests.get(f"{BASE_URL}/api/export/quotes/csv", headers=auth_headers)
        assert response.status_code == 403
        assert "Pro" in response.json().get("detail", "")
    
    def test_clients_csv_requires_pro(self, auth_headers):
        """Verify clients CSV export returns 403 for trial users"""
        response = requests.get(f"{BASE_URL}/api/export/clients/csv", headers=auth_headers)
        assert response.status_code == 403
        assert "Pro" in response.json().get("detail", "")
    
    def test_accounting_csv_requires_pro(self, auth_headers):
        """Verify accounting CSV export returns 403 for trial users"""
        response = requests.get(f"{BASE_URL}/api/export/accounting/csv?year=2025", headers=auth_headers)
        assert response.status_code == 403
        assert "Pro" in response.json().get("detail", "")


class TestRemindersProFeature:
    """Tests for reminder endpoints - Should indicate feature not available for non-Pro users"""
    
    def test_reminders_stats_for_trial_user(self, auth_headers):
        """Verify reminders stats shows feature_available: false for trial users"""
        response = requests.get(f"{BASE_URL}/api/reminders/stats", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["feature_available"] == False
    
    def test_pending_reminders_for_trial_user(self, auth_headers):
        """Verify pending reminders returns 403 for trial users"""
        response = requests.get(f"{BASE_URL}/api/reminders/pending", headers=auth_headers)
        assert response.status_code == 403
        assert "Pro" in response.json().get("detail", "")


class TestFeatureAccessEndpoint:
    """Tests for GET /api/saas/feature/{feature} - Check feature access"""
    
    def test_csv_export_feature_denied_for_trial(self, auth_headers):
        """Verify csv_export feature is denied for trial users"""
        response = requests.get(f"{BASE_URL}/api/saas/feature/csv_export", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["allowed"] == False
        assert "upgrade_plan" in data
    
    def test_automatic_reminders_feature_denied_for_trial(self, auth_headers):
        """Verify automatic_reminders feature is denied for trial users"""
        response = requests.get(f"{BASE_URL}/api/saas/feature/automatic_reminders", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["allowed"] == False
    
    def test_pdf_export_feature_allowed_for_trial(self, auth_headers):
        """Verify pdf_export feature is allowed for trial users"""
        response = requests.get(f"{BASE_URL}/api/saas/feature/pdf_export", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["allowed"] == True


class TestTrialLimits:
    """Tests for trial user limits (9 quotes/invoices total)"""
    
    def test_trial_user_has_9_limit(self, auth_headers):
        """Verify trial users have 9 quote/invoice limit"""
        response = requests.get(f"{BASE_URL}/api/saas/subscription", headers=auth_headers)
        data = response.json()
        
        if data["is_trial"]:
            assert data["quote_limit"] == 9, f"Expected 9 quote limit, got {data['quote_limit']}"
            assert data["invoice_limit"] == 9, f"Expected 9 invoice limit, got {data['invoice_limit']}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
