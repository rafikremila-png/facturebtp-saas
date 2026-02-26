"""
Test Suite for V2 Categories API - Enhanced system with subcategories, smart pricing, and kits
Tests: V2 API endpoints, smart pricing, kits, and backward compatibility with V1
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@btpfacture.com"
ADMIN_PASSWORD = "Admin123!"


class TestV2CategoriesAPI:
    """Test V2 Categories API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Login and get auth token"""
        # Wait a bit to avoid rate limiting
        time.sleep(0.5)
        
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        
        if login_response.status_code == 429:
            pytest.skip("Rate limited - skipping test")
        
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.user = login_response.json()["user"]
    
    def test_seed_v2_categories(self):
        """Test POST /api/v2/categories/seed - Seeds V2 data (super_admin only)"""
        response = requests.post(
            f"{BASE_URL}/api/v2/categories/seed?force=true",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Seed failed: {response.text}"
        data = response.json()
        
        assert "stats" in data
        stats = data["stats"]
        
        # Verify expected counts from seed data
        assert stats["categories"] == 7, f"Expected 7 categories, got {stats['categories']}"
        assert stats["subcategories"] == 28, f"Expected 28 subcategories, got {stats['subcategories']}"
        assert stats["items"] == 140, f"Expected 140 items, got {stats['items']}"
        assert stats["kits"] == 8, f"Expected 8 kits, got {stats['kits']}"
        
        print(f"✓ V2 data seeded: {stats}")
    
    def test_get_categories_v2(self):
        """Test GET /api/v2/categories - Returns categories filtered by user business_type"""
        response = requests.get(
            f"{BASE_URL}/api/v2/categories",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        categories = response.json()
        
        # Admin user has business_type='general' so should see all 7 categories
        assert isinstance(categories, list)
        assert len(categories) == 7, f"Expected 7 categories for general user, got {len(categories)}"
        
        # Verify category structure
        for cat in categories:
            assert "id" in cat
            assert "name" in cat
            assert "business_types" in cat
            assert isinstance(cat["business_types"], list)
        
        # Verify expected category names
        category_names = [c["name"] for c in categories]
        expected_names = ["Électricité", "Réseaux & Courants Faibles", "Plomberie", 
                        "Maçonnerie", "Peinture", "Menuiserie", "Rénovation générale"]
        for name in expected_names:
            assert name in category_names, f"Missing category: {name}"
        
        print(f"✓ GET /api/v2/categories returned {len(categories)} categories")
    
    def test_get_categories_with_subcategories_v2(self):
        """Test GET /api/v2/categories/with-subcategories - Returns categories with their subcategories"""
        response = requests.get(
            f"{BASE_URL}/api/v2/categories/with-subcategories",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        categories = response.json()
        
        assert isinstance(categories, list)
        assert len(categories) == 7
        
        # Verify each category has subcategories
        for cat in categories:
            assert "subcategories" in cat, f"Category {cat['name']} missing subcategories"
            assert isinstance(cat["subcategories"], list)
            assert len(cat["subcategories"]) == 4, f"Expected 4 subcategories for {cat['name']}, got {len(cat['subcategories'])}"
            
            # Verify subcategory structure
            for subcat in cat["subcategories"]:
                assert "id" in subcat
                assert "name" in subcat
                assert "category_id" in subcat
                assert subcat["category_id"] == cat["id"]
        
        print(f"✓ GET /api/v2/categories/with-subcategories returned {len(categories)} categories with subcategories")
    
    def test_get_category_subcategories_v2(self):
        """Test GET /api/v2/categories/{id}/subcategories - Returns subcategories for a category"""
        # First get categories to get a valid ID
        categories_response = requests.get(
            f"{BASE_URL}/api/v2/categories",
            headers=self.headers
        )
        categories = categories_response.json()
        
        # Test with Électricité category
        electricite = next((c for c in categories if c["name"] == "Électricité"), None)
        assert electricite is not None, "Électricité category not found"
        
        response = requests.get(
            f"{BASE_URL}/api/v2/categories/{electricite['id']}/subcategories",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        subcategories = response.json()
        
        assert isinstance(subcategories, list)
        assert len(subcategories) == 4
        
        # Verify expected subcategory names for Électricité
        subcat_names = [s["name"] for s in subcategories]
        expected_subcats = ["Installation", "Rénovation", "Dépannage", "Mise aux normes"]
        for name in expected_subcats:
            assert name in subcat_names, f"Missing subcategory: {name}"
        
        print(f"✓ GET /api/v2/categories/{electricite['id']}/subcategories returned {len(subcategories)} subcategories")
        return subcategories
    
    def test_get_subcategory_items_v2(self):
        """Test GET /api/v2/subcategories/{id}/items - Returns items with smart_price"""
        # Get categories with subcategories
        categories_response = requests.get(
            f"{BASE_URL}/api/v2/categories/with-subcategories",
            headers=self.headers
        )
        categories = categories_response.json()
        
        # Find Électricité > Installation subcategory
        electricite = next((c for c in categories if c["name"] == "Électricité"), None)
        assert electricite is not None
        
        installation = next((s for s in electricite["subcategories"] if s["name"] == "Installation"), None)
        assert installation is not None, "Installation subcategory not found"
        
        response = requests.get(
            f"{BASE_URL}/api/v2/subcategories/{installation['id']}/items",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        items = response.json()
        
        assert isinstance(items, list)
        assert len(items) == 5, f"Expected 5 items in Installation, got {len(items)}"
        
        # Verify item structure with smart_price
        for item in items:
            assert "id" in item
            assert "name" in item
            assert "description" in item
            assert "unit" in item
            assert "default_price" in item
            assert "suggested_prices" in item
            assert "smart_price" in item, "Missing smart_price field"
            
            # For general user, smart_price should be from suggested_prices['general'] or default_price
            assert isinstance(item["smart_price"], (int, float))
        
        # Verify specific item
        prise = next((i for i in items if "prise électrique" in i["name"].lower()), None)
        assert prise is not None, "Installation prise électrique not found"
        assert prise["default_price"] == 65
        assert prise["suggested_prices"].get("electrician") == 55
        assert prise["suggested_prices"].get("general") == 70
        # Admin has business_type='general', so smart_price should be 70
        assert prise["smart_price"] == 70, f"Expected smart_price=70 for general, got {prise['smart_price']}"
        
        print(f"✓ GET /api/v2/subcategories/{installation['id']}/items returned {len(items)} items with smart_price")
        return items
    
    def test_get_kits_v2(self):
        """Test GET /api/v2/kits - Returns kits filtered by user business_type"""
        response = requests.get(
            f"{BASE_URL}/api/v2/kits",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        kits = response.json()
        
        assert isinstance(kits, list)
        # General user should see all 8 kits (all business types + general)
        assert len(kits) == 8, f"Expected 8 kits for general user, got {len(kits)}"
        
        # Verify kit structure
        for kit in kits:
            assert "id" in kit
            assert "name" in kit
            assert "business_type" in kit
            assert "description" in kit
            assert "items" in kit
            assert isinstance(kit["items"], list)
        
        # Verify expected kit names
        kit_names = [k["name"] for k in kits]
        expected_kits = [
            "Installation électrique appartement T3",
            "Rénovation tableau électrique",
            "Rénovation salle de bain complète",
            "Installation chauffe-eau",
            "Installation réseau bureau complet",
            "Rénovation appartement clé en main",
            "Peinture appartement T3",
            "Création salle de bain maçonnerie"
        ]
        for name in expected_kits:
            assert name in kit_names, f"Missing kit: {name}"
        
        print(f"✓ GET /api/v2/kits returned {len(kits)} kits")
        return kits
    
    def test_get_kit_with_expanded_items_v2(self):
        """Test GET /api/v2/kits/{id} - Returns kit with expanded_items and total_ht"""
        # First get kits
        kits_response = requests.get(
            f"{BASE_URL}/api/v2/kits",
            headers=self.headers
        )
        kits = kits_response.json()
        
        # Test with "Installation électrique appartement T3" kit
        elec_kit = next((k for k in kits if "électrique appartement" in k["name"].lower()), None)
        assert elec_kit is not None, "Installation électrique appartement T3 kit not found"
        
        response = requests.get(
            f"{BASE_URL}/api/v2/kits/{elec_kit['id']}",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        kit = response.json()
        
        # Verify expanded_items
        assert "expanded_items" in kit, "Missing expanded_items"
        assert isinstance(kit["expanded_items"], list)
        assert len(kit["expanded_items"]) == 7, f"Expected 7 expanded items, got {len(kit['expanded_items'])}"
        
        # Verify expanded item structure
        for item in kit["expanded_items"]:
            assert "id" in item
            assert "name" in item
            assert "description" in item
            assert "unit" in item
            assert "quantity" in item
            assert "unit_price" in item
            assert "total" in item
            
            # Verify total calculation
            expected_total = item["quantity"] * item["unit_price"]
            assert abs(item["total"] - expected_total) < 0.01, f"Total mismatch for {item['name']}"
        
        # Verify total_ht
        assert "total_ht" in kit, "Missing total_ht"
        calculated_total = sum(i["total"] for i in kit["expanded_items"])
        assert abs(kit["total_ht"] - calculated_total) < 0.01, f"total_ht mismatch: {kit['total_ht']} vs {calculated_total}"
        
        print(f"✓ GET /api/v2/kits/{elec_kit['id']} returned kit with {len(kit['expanded_items'])} expanded items, total_ht={kit['total_ht']}")
    
    def test_smart_pricing_by_business_type(self):
        """Test that smart_price varies based on business_type"""
        # Get items from Électricité > Installation
        categories_response = requests.get(
            f"{BASE_URL}/api/v2/categories/with-subcategories",
            headers=self.headers
        )
        categories = categories_response.json()
        
        electricite = next((c for c in categories if c["name"] == "Électricité"), None)
        installation = next((s for s in electricite["subcategories"] if s["name"] == "Installation"), None)
        
        response = requests.get(
            f"{BASE_URL}/api/v2/subcategories/{installation['id']}/items",
            headers=self.headers
        )
        items = response.json()
        
        # Find "Installation prise électrique" item
        prise = next((i for i in items if "prise électrique" in i["name"].lower()), None)
        assert prise is not None
        
        # Verify suggested_prices structure
        assert "suggested_prices" in prise
        assert prise["suggested_prices"].get("electrician") == 55
        assert prise["suggested_prices"].get("general") == 70
        
        # For admin (general business_type), smart_price should be 70
        assert prise["smart_price"] == 70
        
        print(f"✓ Smart pricing verified: electrician=55€, general=70€, current smart_price={prise['smart_price']}€")


class TestV1BackwardCompatibility:
    """Test that V1 endpoints still work for backward compatibility"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Login and get auth token"""
        time.sleep(0.5)
        
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        
        if login_response.status_code == 429:
            pytest.skip("Rate limited - skipping test")
        
        assert login_response.status_code == 200
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_v1_get_categories(self):
        """Test GET /api/categories - V1 endpoint still works"""
        response = requests.get(
            f"{BASE_URL}/api/categories",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"V1 /api/categories failed: {response.text}"
        categories = response.json()
        
        assert isinstance(categories, list)
        print(f"✓ V1 GET /api/categories returned {len(categories)} categories")
    
    def test_v1_get_categories_with_items(self):
        """Test GET /api/categories/with-items - V1 endpoint still works"""
        response = requests.get(
            f"{BASE_URL}/api/categories/with-items",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"V1 /api/categories/with-items failed: {response.text}"
        categories = response.json()
        
        assert isinstance(categories, list)
        
        # Verify structure
        for cat in categories:
            assert "id" in cat
            assert "name" in cat
            assert "items" in cat
        
        print(f"✓ V1 GET /api/categories/with-items returned {len(categories)} categories with items")


class TestFrontendIntegration:
    """Test that frontend API calls work correctly"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Login and get auth token"""
        time.sleep(0.5)
        
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        
        if login_response.status_code == 429:
            pytest.skip("Rate limited - skipping test")
        
        assert login_response.status_code == 200
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_frontend_category_flow(self):
        """Test the flow used by ServiceItemSelectorV2 component"""
        # Step 1: Load categories with subcategories (on component mount)
        categories_response = requests.get(
            f"{BASE_URL}/api/v2/categories/with-subcategories",
            headers=self.headers
        )
        assert categories_response.status_code == 200
        categories = categories_response.json()
        assert len(categories) == 7
        
        # Step 2: User selects a category (Électricité)
        electricite = next((c for c in categories if c["name"] == "Électricité"), None)
        assert electricite is not None
        subcategories = electricite["subcategories"]
        assert len(subcategories) == 4
        
        # Step 3: User selects a subcategory (Installation)
        installation = next((s for s in subcategories if s["name"] == "Installation"), None)
        assert installation is not None
        
        # Step 4: Load items for subcategory
        items_response = requests.get(
            f"{BASE_URL}/api/v2/subcategories/{installation['id']}/items",
            headers=self.headers
        )
        assert items_response.status_code == 200
        items = items_response.json()
        assert len(items) == 5
        
        # Step 5: User selects an item - verify it has smart_price
        item = items[0]
        assert "smart_price" in item
        assert "name" in item
        assert "unit" in item
        
        print(f"✓ Frontend category flow works: {len(categories)} categories → {len(subcategories)} subcategories → {len(items)} items")
    
    def test_frontend_kit_flow(self):
        """Test the flow used by kit selection in ServiceItemSelectorV2"""
        # Step 1: Load kits (on dialog open)
        kits_response = requests.get(
            f"{BASE_URL}/api/v2/kits",
            headers=self.headers
        )
        assert kits_response.status_code == 200
        kits = kits_response.json()
        assert len(kits) == 8
        
        # Step 2: User selects a kit
        kit = kits[0]
        assert "id" in kit
        assert "name" in kit
        
        # Step 3: Load kit details with expanded items
        kit_details_response = requests.get(
            f"{BASE_URL}/api/v2/kits/{kit['id']}",
            headers=self.headers
        )
        assert kit_details_response.status_code == 200
        kit_details = kit_details_response.json()
        
        # Step 4: Verify expanded_items for adding to invoice
        assert "expanded_items" in kit_details
        assert "total_ht" in kit_details
        
        for item in kit_details["expanded_items"]:
            assert "name" in item
            assert "quantity" in item
            assert "unit_price" in item
            assert "unit" in item
        
        print(f"✓ Frontend kit flow works: {len(kits)} kits → kit '{kit_details['name']}' with {len(kit_details['expanded_items'])} items, total_ht={kit_details['total_ht']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
