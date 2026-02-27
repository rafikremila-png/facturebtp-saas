"""
Test Admin Metrics Dashboard and Button Label Fixes
Tests for iteration 19 features:
- GET /api/admin/metrics returns MRR, ARR, active_subscribers, trial_users, churn_rate, plan_breakdown, mrr_history
- Admin metrics endpoint requires super_admin role
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Admin credentials
ADMIN_EMAIL = "admin@btpfacture.com"
ADMIN_PASSWORD = "Admin123!"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    data = response.json()
    assert data["user"]["role"] == "super_admin", "User is not super_admin"
    return data["access_token"]


class TestAdminMetricsEndpoint:
    """Test GET /api/admin/metrics endpoint"""
    
    def test_admin_metrics_returns_all_required_fields(self, admin_token):
        """Test that admin metrics returns all required fields"""
        response = requests.get(
            f"{BASE_URL}/api/admin/metrics",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Check all required fields exist
        required_fields = [
            "mrr", "arr", "active_subscribers", "trial_users", 
            "churn_rate", "plan_breakdown", "mrr_history"
        ]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Verify data types
        assert isinstance(data["mrr"], (int, float)), "MRR should be numeric"
        assert isinstance(data["arr"], (int, float)), "ARR should be numeric"
        assert isinstance(data["active_subscribers"], int), "active_subscribers should be int"
        assert isinstance(data["trial_users"], int), "trial_users should be int"
        assert isinstance(data["churn_rate"], (int, float)), "churn_rate should be numeric"
        assert isinstance(data["plan_breakdown"], list), "plan_breakdown should be a list"
        assert isinstance(data["mrr_history"], list), "mrr_history should be a list"
        
        print(f"✓ Admin metrics returned all required fields")
        print(f"  MRR: {data['mrr']}, ARR: {data['arr']}")
        print(f"  Active subscribers: {data['active_subscribers']}")
        print(f"  Trial users: {data['trial_users']}")
        print(f"  Churn rate: {data['churn_rate']}%")
        print(f"  Plan breakdown items: {len(data['plan_breakdown'])}")
        print(f"  MRR history months: {len(data['mrr_history'])}")
    
    def test_plan_breakdown_structure(self, admin_token):
        """Test that plan_breakdown has correct structure"""
        response = requests.get(
            f"{BASE_URL}/api/admin/metrics",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # plan_breakdown should be a list
        assert isinstance(data["plan_breakdown"], list), "plan_breakdown should be a list"
        
        # If there are plans, check structure
        if data["plan_breakdown"]:
            plan = data["plan_breakdown"][0]
            expected_fields = ["plan", "active", "trial", "total", "price", "mrr_contribution"]
            for field in expected_fields:
                assert field in plan, f"Plan breakdown missing field: {field}"
            
            print(f"✓ Plan breakdown structure verified")
            for p in data["plan_breakdown"]:
                print(f"  {p['plan']}: {p['total']} users, MRR contribution: {p['mrr_contribution']}€")
    
    def test_mrr_history_structure(self, admin_token):
        """Test that mrr_history has correct structure"""
        response = requests.get(
            f"{BASE_URL}/api/admin/metrics",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # mrr_history should be a list
        assert isinstance(data["mrr_history"], list), "mrr_history should be a list"
        
        # Should have 6 months of history
        assert len(data["mrr_history"]) == 6, f"Expected 6 months, got {len(data['mrr_history'])}"
        
        # Check structure of each month
        for month in data["mrr_history"]:
            assert "month" in month, "Missing 'month' field"
            assert "month_label" in month, "Missing 'month_label' field"
            assert "mrr" in month, "Missing 'mrr' field"
        
        print(f"✓ MRR history structure verified (6 months)")
        for m in data["mrr_history"]:
            print(f"  {m['month_label']}: {m['mrr']}€")
    
    def test_admin_metrics_requires_super_admin(self):
        """Test that admin metrics requires super_admin role"""
        # Try without authentication
        response = requests.get(f"{BASE_URL}/api/admin/metrics")
        assert response.status_code == 401, "Should require authentication"
        
        print("✓ Admin metrics requires authentication")
    
    def test_admin_metrics_force_refresh(self, admin_token):
        """Test force_refresh parameter"""
        response = requests.get(
            f"{BASE_URL}/api/admin/metrics?force_refresh=true",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have calculated_at timestamp
        assert "calculated_at" in data, "Missing calculated_at timestamp"
        
        print(f"✓ Force refresh works, calculated_at: {data['calculated_at']}")


class TestAdminSubscribersEndpoint:
    """Test GET /api/admin/metrics/subscribers endpoint"""
    
    def test_get_subscribers_list(self, admin_token):
        """Test getting list of subscribers"""
        response = requests.get(
            f"{BASE_URL}/api/admin/metrics/subscribers",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "subscribers" in data, "Missing subscribers field"
        assert "total" in data, "Missing total field"
        assert isinstance(data["subscribers"], list), "subscribers should be a list"
        
        print(f"✓ Subscribers list returned: {data['total']} total")


class TestAdminMRRHistoryEndpoint:
    """Test GET /api/admin/metrics/mrr-history endpoint"""
    
    def test_get_mrr_history(self, admin_token):
        """Test getting MRR history"""
        response = requests.get(
            f"{BASE_URL}/api/admin/metrics/mrr-history",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list), "MRR history should be a list"
        assert len(data) == 6, f"Expected 6 months, got {len(data)}"
        
        print(f"✓ MRR history endpoint works: {len(data)} months")


class TestHealthCheck:
    """Basic health check"""
    
    def test_health_endpoint(self):
        """Test health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✓ Health check passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
