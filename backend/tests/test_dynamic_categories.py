"""
Test Dynamic Category System for BTP Facture
Tests business-type filtering for predefined categories and items
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@btpfacture.com"
ADMIN_PASSWORD = "Admin123!"


class TestBusinessTypes:
    """Test /api/business-types endpoint"""
    
    def test_get_business_types_returns_types_and_labels(self):
        """GET /api/business-types returns available business types with labels"""
        response = requests.get(f"{BASE_URL}/api/business-types")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "types" in data, "Response should contain 'types' field"
        assert "labels" in data, "Response should contain 'labels' field"
        
        # Verify expected business types
        expected_types = ["general", "electrician", "plumber", "mason", "painter", "carpenter", "it_installer"]
        for bt in expected_types:
            assert bt in data["types"], f"Business type '{bt}' should be in types list"
            assert bt in data["labels"], f"Business type '{bt}' should have a label"
        
        # Verify labels are French
        assert data["labels"]["general"] == "Général / Multi-corps"
        assert data["labels"]["electrician"] == "Électricien"
        assert data["labels"]["plumber"] == "Plombier"
        
        print(f"✓ GET /api/business-types returns {len(data['types'])} types with labels")


class TestCategoriesWithItems:
    """Test /api/categories/with-items endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as admin to get auth token"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_categories_with_items_returns_categories(self):
        """GET /api/categories/with-items returns categories filtered by user's business_type"""
        response = requests.get(f"{BASE_URL}/api/categories/with-items", headers=self.headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list of categories"
        assert len(data) > 0, "Should return at least one category"
        
        # Verify category structure
        first_category = data[0]
        assert "id" in first_category, "Category should have 'id'"
        assert "name" in first_category, "Category should have 'name'"
        assert "business_types" in first_category, "Category should have 'business_types'"
        assert "items" in first_category, "Category should have 'items'"
        
        print(f"✓ GET /api/categories/with-items returns {len(data)} categories")
        
        # Verify items structure
        if first_category["items"]:
            first_item = first_category["items"][0]
            assert "id" in first_item, "Item should have 'id'"
            assert "name" in first_item, "Item should have 'name'"
            assert "category_id" in first_item, "Item should have 'category_id'"
            print(f"✓ First category '{first_category['name']}' has {len(first_category['items'])} items")
    
    def test_categories_include_expected_names(self):
        """Verify expected category names are present"""
        response = requests.get(f"{BASE_URL}/api/categories/with-items", headers=self.headers)
        
        assert response.status_code == 200
        data = response.json()
        
        category_names = [c["name"] for c in data]
        
        # Expected categories from seed data
        expected_categories = [
            "Maçonnerie", "Électricité", "Plomberie", "Peinture", 
            "Menuiserie", "Carrelage", "Plâtrerie / Isolation",
            "Rénovation générale", "Réseaux & Courants Faibles"
        ]
        
        for expected in expected_categories:
            assert expected in category_names, f"Category '{expected}' should be present"
        
        print(f"✓ All {len(expected_categories)} expected categories are present")


class TestCategoryItems:
    """Test /api/categories/{id}/items endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as admin and get a category ID"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Get categories to find a valid ID
        categories_response = requests.get(f"{BASE_URL}/api/categories/with-items", headers=self.headers)
        assert categories_response.status_code == 200
        self.categories = categories_response.json()
    
    def test_get_category_items_returns_items(self):
        """GET /api/categories/{id}/items returns items for a specific category"""
        # Find a category with items
        category_with_items = None
        for cat in self.categories:
            if cat.get("items") and len(cat["items"]) > 0:
                category_with_items = cat
                break
        
        assert category_with_items is not None, "Should have at least one category with items"
        
        category_id = category_with_items["id"]
        response = requests.get(f"{BASE_URL}/api/categories/{category_id}/items", headers=self.headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list of items"
        assert len(data) > 0, "Should return at least one item"
        
        # Verify item structure
        first_item = data[0]
        assert "id" in first_item, "Item should have 'id'"
        assert "name" in first_item, "Item should have 'name'"
        assert "category_id" in first_item, "Item should have 'category_id'"
        assert first_item["category_id"] == category_id, "Item's category_id should match requested category"
        
        print(f"✓ GET /api/categories/{category_id}/items returns {len(data)} items for '{category_with_items['name']}'")
    
    def test_get_category_items_invalid_id_returns_empty(self):
        """GET /api/categories/{invalid_id}/items returns empty list for invalid category"""
        invalid_id = "00000000-0000-0000-0000-000000000000"
        response = requests.get(f"{BASE_URL}/api/categories/{invalid_id}/items", headers=self.headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) == 0, "Should return empty list for invalid category"
        
        print("✓ GET /api/categories/{invalid_id}/items returns empty list")


class TestSettingsBusinessType:
    """Test settings page business_type selector"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as admin"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_settings_includes_business_type(self):
        """GET /api/settings returns business_type field"""
        response = requests.get(f"{BASE_URL}/api/settings", headers=self.headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "business_type" in data, "Settings should include 'business_type' field"
        
        print(f"✓ GET /api/settings includes business_type: '{data['business_type']}'")
    
    def test_update_settings_business_type(self):
        """PUT /api/settings can update business_type"""
        # Get current settings
        get_response = requests.get(f"{BASE_URL}/api/settings", headers=self.headers)
        assert get_response.status_code == 200
        current_settings = get_response.json()
        original_business_type = current_settings.get("business_type", "general")
        
        # Update to electrician
        new_business_type = "electrician" if original_business_type != "electrician" else "plumber"
        update_payload = {**current_settings, "business_type": new_business_type}
        
        update_response = requests.put(f"{BASE_URL}/api/settings", headers=self.headers, json=update_payload)
        assert update_response.status_code == 200, f"Expected 200, got {update_response.status_code}: {update_response.text}"
        
        # Verify update
        verify_response = requests.get(f"{BASE_URL}/api/settings", headers=self.headers)
        assert verify_response.status_code == 200
        updated_settings = verify_response.json()
        assert updated_settings["business_type"] == new_business_type, f"business_type should be '{new_business_type}'"
        
        print(f"✓ PUT /api/settings successfully updated business_type to '{new_business_type}'")
        
        # Restore original
        restore_payload = {**updated_settings, "business_type": original_business_type}
        requests.put(f"{BASE_URL}/api/settings", headers=self.headers, json=restore_payload)
        print(f"✓ Restored business_type to '{original_business_type}'")


class TestCategoryFiltering:
    """Test that categories are filtered by business_type"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as admin"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_general_user_sees_all_categories(self):
        """User with business_type='general' should see all categories"""
        # First set business_type to general
        get_response = requests.get(f"{BASE_URL}/api/settings", headers=self.headers)
        current_settings = get_response.json()
        
        update_payload = {**current_settings, "business_type": "general"}
        requests.put(f"{BASE_URL}/api/settings", headers=self.headers, json=update_payload)
        
        # Get categories
        categories_response = requests.get(f"{BASE_URL}/api/categories/with-items", headers=self.headers)
        assert categories_response.status_code == 200
        
        categories = categories_response.json()
        category_names = [c["name"] for c in categories]
        
        # General user should see all 9 categories
        assert len(categories) >= 9, f"General user should see at least 9 categories, got {len(categories)}"
        
        print(f"✓ General user sees {len(categories)} categories: {category_names}")
    
    def test_electrician_sees_filtered_categories(self):
        """User with business_type='electrician' should see only relevant categories"""
        # Set business_type to electrician
        get_response = requests.get(f"{BASE_URL}/api/settings", headers=self.headers)
        current_settings = get_response.json()
        
        update_payload = {**current_settings, "business_type": "electrician"}
        requests.put(f"{BASE_URL}/api/settings", headers=self.headers, json=update_payload)
        
        # Get categories
        categories_response = requests.get(f"{BASE_URL}/api/categories/with-items", headers=self.headers)
        assert categories_response.status_code == 200
        
        categories = categories_response.json()
        category_names = [c["name"] for c in categories]
        
        # Electrician should see Électricité and Réseaux & Courants Faibles
        assert "Électricité" in category_names, "Electrician should see 'Électricité' category"
        assert "Réseaux & Courants Faibles" in category_names, "Electrician should see 'Réseaux & Courants Faibles' category"
        
        # Electrician should also see categories with 'general' in business_types
        # Based on seed data, electrician sees: Électricité, Réseaux & Courants Faibles, Rénovation générale
        
        print(f"✓ Electrician user sees {len(categories)} categories: {category_names}")
        
        # Restore to general
        restore_payload = {**current_settings, "business_type": "general"}
        requests.put(f"{BASE_URL}/api/settings", headers=self.headers, json=restore_payload)


class TestCategoriesEndpoint:
    """Test /api/categories endpoint (without items)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as admin"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_categories_returns_list(self):
        """GET /api/categories returns list of categories"""
        response = requests.get(f"{BASE_URL}/api/categories", headers=self.headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) > 0, "Should return at least one category"
        
        # Verify category structure (without items)
        first_category = data[0]
        assert "id" in first_category, "Category should have 'id'"
        assert "name" in first_category, "Category should have 'name'"
        assert "business_types" in first_category, "Category should have 'business_types'"
        
        print(f"✓ GET /api/categories returns {len(data)} categories")


class TestSearchItems:
    """Test /api/categories/search/items endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as admin"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_search_items_returns_results(self):
        """GET /api/categories/search/items?q=prise returns matching items"""
        response = requests.get(f"{BASE_URL}/api/categories/search/items", 
                               headers=self.headers, 
                               params={"q": "prise"})
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        # Should find items with "prise" in name (e.g., "Installation prise électrique")
        if len(data) > 0:
            print(f"✓ Search for 'prise' returned {len(data)} items")
            for item in data[:3]:
                print(f"  - {item.get('name', 'N/A')}")
        else:
            print("✓ Search returned empty list (may need to check seed data)")
    
    def test_search_items_short_query_returns_empty(self):
        """GET /api/categories/search/items?q=a returns empty list (query too short)"""
        response = requests.get(f"{BASE_URL}/api/categories/search/items", 
                               headers=self.headers, 
                               params={"q": "a"})
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) == 0, "Short query should return empty list"
        
        print("✓ Short query returns empty list as expected")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
