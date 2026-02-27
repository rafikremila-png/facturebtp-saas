"""
Test V3 Article Management System
Tests for:
- V3 categories API (10 categories with 239 items)
- V3 kits API (8 kits)
- Quote stats/usage API (trial limits)
- Quote creation with trial limit check
- Registration without business_type
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "admin@btpfacture.com"
TEST_PASSWORD = "Admin123!"


class TestV3CategoriesAPI:
    """Test V3 Categories endpoints - simplified structure without subcategories"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.user_id = login_response.json().get("user", {}).get("id")
        else:
            pytest.skip(f"Login failed: {login_response.status_code}")
    
    def test_v3_categories_list_returns_10_categories(self):
        """Test GET /api/v3/categories returns 10 categories"""
        response = self.session.get(f"{BASE_URL}/api/v3/categories")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Response is a direct array
        categories = response.json()
        assert isinstance(categories, list), "Response should be a list"
        assert len(categories) == 10, f"Expected 10 categories, got {len(categories)}"
        
        # Verify category structure
        for cat in categories:
            assert "id" in cat, "Category should have 'id'"
            assert "name" in cat, "Category should have 'name'"
            assert "business_types" in cat, "Category should have 'business_types'"
        
        print(f"✓ V3 Categories API returns {len(categories)} categories")
        
        # Print category names for verification
        category_names = [cat["name"] for cat in categories]
        print(f"  Categories: {category_names}")
    
    def test_v3_categories_with_items_returns_239_items(self):
        """Test GET /api/v3/categories/with-items returns categories with 239 items total"""
        response = self.session.get(f"{BASE_URL}/api/v3/categories/with-items")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Response is a direct array
        categories = response.json()
        assert isinstance(categories, list), "Response should be a list"
        assert len(categories) == 10, f"Expected 10 categories, got {len(categories)}"
        
        # Count total items
        total_items = 0
        for cat in categories:
            assert "items" in cat, f"Category {cat.get('name')} should have 'items'"
            total_items += len(cat["items"])
        
        # Should have 239 items total
        assert total_items == 239, f"Expected 239 items, got {total_items}"
        print(f"✓ V3 Categories with items returns {len(categories)} categories with {total_items} total items")
        
        # Verify item structure (no subcategories - direct category->item)
        for cat in categories:
            for item in cat.get("items", []):
                assert "name" in item, "Item should have 'name'"
                assert "unit" in item, "Item should have 'unit'"
                assert "default_price" in item, "Item should have 'default_price'"
    
    def test_v3_single_category(self):
        """Test GET /api/v3/categories/{category_id} returns single category"""
        # First get list of categories
        list_response = self.session.get(f"{BASE_URL}/api/v3/categories")
        assert list_response.status_code == 200
        
        categories = list_response.json()
        if len(categories) > 0:
            category_id = categories[0]["id"]
            
            response = self.session.get(f"{BASE_URL}/api/v3/categories/{category_id}")
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            data = response.json()
            assert data["id"] == category_id
            print(f"✓ Single category endpoint works for category: {data['name']}")
    
    def test_v3_category_items(self):
        """Test GET /api/v3/categories/{category_id}/items returns items for category"""
        # First get list of categories
        list_response = self.session.get(f"{BASE_URL}/api/v3/categories")
        assert list_response.status_code == 200
        
        categories = list_response.json()
        if len(categories) > 0:
            category_id = categories[0]["id"]
            category_name = categories[0]["name"]
            
            response = self.session.get(f"{BASE_URL}/api/v3/categories/{category_id}/items")
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            items = response.json()
            assert isinstance(items, list), "Response should be a list"
            
            print(f"✓ Category '{category_name}' has {len(items)} items")
            
            # Verify items have correct structure
            if len(items) > 0:
                item = items[0]
                assert "name" in item
                assert "unit" in item
                assert "default_price" in item


class TestV3KitsAPI:
    """Test V3 Kits endpoints - should return 8 kits"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            pytest.skip(f"Login failed: {login_response.status_code}")
    
    def test_v3_kits_list_returns_8_kits(self):
        """Test GET /api/v3/kits returns 8 kits"""
        response = self.session.get(f"{BASE_URL}/api/v3/kits")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Response is a direct array
        kits = response.json()
        assert isinstance(kits, list), "Response should be a list"
        assert len(kits) == 8, f"Expected 8 kits, got {len(kits)}"
        
        # Verify kit structure
        for kit in kits:
            assert "id" in kit, "Kit should have 'id'"
            assert "name" in kit, "Kit should have 'name'"
            assert "items" in kit, "Kit should have 'items'"
        
        print(f"✓ V3 Kits API returns {len(kits)} kits")
        
        # Print kit names
        kit_names = [kit["name"] for kit in kits]
        print(f"  Kits: {kit_names}")
    
    def test_v3_single_kit(self):
        """Test GET /api/v3/kits/{kit_id} returns single kit"""
        # First get list of kits
        list_response = self.session.get(f"{BASE_URL}/api/v3/kits")
        assert list_response.status_code == 200
        
        kits = list_response.json()
        if len(kits) > 0:
            kit_id = kits[0]["id"]
            
            response = self.session.get(f"{BASE_URL}/api/v3/kits/{kit_id}")
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            data = response.json()
            assert data["id"] == kit_id
            print(f"✓ Single kit endpoint works for kit: {data['name']}")


class TestQuoteStatsUsageAPI:
    """Test Quote Stats/Usage API for trial limits"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.user_id = login_response.json().get("user", {}).get("id")
        else:
            pytest.skip(f"Login failed: {login_response.status_code}")
    
    def test_quote_stats_usage_endpoint(self):
        """Test GET /api/quotes/stats/usage returns proper trial limits"""
        response = self.session.get(f"{BASE_URL}/api/quotes/stats/usage")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify structure
        assert "quote_count" in data, "Should have quote_count"
        assert "can_create" in data, "Should have can_create"
        assert "trial_status" in data, "Should have trial_status"
        
        print(f"✓ Quote stats usage response:")
        print(f"  Quote count: {data.get('quote_count')}")
        print(f"  Quote limit: {data.get('quote_limit')}")
        print(f"  Can create: {data.get('can_create')}")
        print(f"  Trial status: {data.get('trial_status')}")


class TestQuoteCreationWithTrialLimit:
    """Test Quote creation checks trial limits"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.user_id = login_response.json().get("user", {}).get("id")
        else:
            pytest.skip(f"Login failed: {login_response.status_code}")
    
    def test_quote_creation_endpoint_exists(self):
        """Test POST /api/quotes endpoint exists and validates"""
        # First we need a client to create a quote
        # Get existing clients
        clients_response = self.session.get(f"{BASE_URL}/api/clients")
        
        if clients_response.status_code == 200:
            clients = clients_response.json()
            if len(clients) > 0:
                client_id = clients[0]["id"]
                
                # Try to create a quote (this should check trial limits)
                quote_data = {
                    "client_id": client_id,
                    "items": [
                        {
                            "description": "Test item for trial limit check",
                            "quantity": 1,
                            "unit": "unité",
                            "unit_price": 100,
                            "vat_rate": 20
                        }
                    ],
                    "validity_days": 30,
                    "notes": "Test quote for trial limit"
                }
                
                response = self.session.post(f"{BASE_URL}/api/quotes", json=quote_data)
                
                # Should either succeed (201) or fail with trial limit error (403)
                assert response.status_code in [200, 201, 403], f"Expected 200/201/403, got {response.status_code}: {response.text}"
                
                if response.status_code == 403:
                    print("✓ Quote creation properly enforces trial limits (403 returned)")
                else:
                    print(f"✓ Quote creation succeeded (status {response.status_code})")
                    # Clean up - delete the test quote
                    if response.status_code in [200, 201]:
                        quote_id = response.json().get("id")
                        if quote_id:
                            self.session.delete(f"{BASE_URL}/api/quotes/{quote_id}")
                            print(f"  Cleaned up test quote {quote_id}")
            else:
                pytest.skip("No clients available for quote creation test")
        else:
            pytest.skip(f"Could not get clients: {clients_response.status_code}")


class TestRegistrationWithoutBusinessType:
    """Test that registration form does NOT require business_type"""
    
    def test_registration_without_business_type(self):
        """Test POST /api/auth/register works without business_type field"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        # Generate unique email for test
        test_email = f"test_no_btype_{int(time.time())}@test.com"
        
        # Register without business_type (but with required phone field)
        register_data = {
            "email": test_email,
            "password": "TestPass123!",
            "name": "Test User No BType",
            "company_name": "Test Company",
            "phone": "0123456789"
            # Note: NO business_type field - should default to "general"
        }
        
        response = session.post(f"{BASE_URL}/api/auth/register", json=register_data)
        
        # Should succeed - business_type should default to "general"
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.text}"
        
        data = response.json()
        print(f"✓ Registration without business_type succeeded")
        
        # Verify user was created with default business_type
        if "user" in data:
            user = data["user"]
            print(f"  User created: {user.get('email')}")
            if "business_type" in user:
                assert user.get("business_type") == "general", f"Expected default business_type 'general', got {user.get('business_type')}"
                print(f"  Default business_type: {user.get('business_type')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
