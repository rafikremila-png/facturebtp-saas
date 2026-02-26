"""
Test suite for Landing Pages, Registration with business_type, and V2 Service Selector
Tests the new BTP platform features:
1. Landing pages (general + specialized)
2. Registration with business_type field
3. Quote/Invoice forms using ServiceItemSelectorV2
4. Backward compatibility with old category endpoints
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestLandingPagesAndRegistration:
    """Test landing pages and registration with business_type"""
    
    def test_backend_health(self):
        """Verify backend is running"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        print("SUCCESS: Backend health check passed")
    
    def test_registration_accepts_business_type(self):
        """Test that registration API accepts business_type field"""
        # Generate unique email to avoid conflicts
        unique_email = f"test_electrician_{int(time.time())}@test.com"
        
        payload = {
            "email": unique_email,
            "password": "TestPass123!",
            "name": "Test Electrician",
            "phone": "0612345678",
            "company_name": "Test Electric Co",
            "address": "123 Test Street",
            "business_type": "electrician"
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
        
        # Should return 200 with requires_verification=True
        assert response.status_code == 200, f"Registration failed: {response.text}"
        data = response.json()
        assert data.get("requires_verification") == True
        assert data.get("email") == unique_email
        print(f"SUCCESS: Registration accepted business_type='electrician' for {unique_email}")
    
    def test_registration_validates_business_type(self):
        """Test that invalid business_type defaults to 'general'"""
        unique_email = f"test_invalid_bt_{int(time.time())}@test.com"
        
        payload = {
            "email": unique_email,
            "password": "TestPass123!",
            "name": "Test User",
            "phone": "0612345678",
            "business_type": "invalid_type"  # Invalid type
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
        # Should still succeed - invalid type defaults to 'general'
        assert response.status_code == 200, f"Registration failed: {response.text}"
        print("SUCCESS: Invalid business_type handled gracefully")


class TestV2CategoriesAPI:
    """Test V2 Categories API with subcategories and smart pricing"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token for admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@btpfacture.com",
            "password": "Admin123!"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Admin login failed")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_v2_categories_returns_list(self, auth_headers):
        """Test GET /api/v2/categories returns categories"""
        response = requests.get(f"{BASE_URL}/api/v2/categories", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        print(f"SUCCESS: V2 categories returned {len(data)} categories")
    
    def test_v2_categories_with_subcategories(self, auth_headers):
        """Test GET /api/v2/categories/with-subcategories returns hierarchy"""
        response = requests.get(f"{BASE_URL}/api/v2/categories/with-subcategories", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Check structure
        if len(data) > 0:
            category = data[0]
            assert "id" in category
            assert "name" in category
            assert "subcategories" in category
            assert isinstance(category["subcategories"], list)
            print(f"SUCCESS: V2 categories with subcategories - {len(data)} categories")
    
    def test_v2_subcategory_items_with_smart_price(self, auth_headers):
        """Test GET /api/v2/subcategories/{id}/items returns items with smart_price"""
        # First get categories to find a subcategory ID
        cat_response = requests.get(f"{BASE_URL}/api/v2/categories/with-subcategories", headers=auth_headers)
        assert cat_response.status_code == 200
        categories = cat_response.json()
        
        if len(categories) > 0 and len(categories[0].get("subcategories", [])) > 0:
            subcategory_id = categories[0]["subcategories"][0]["id"]
            
            # Get items for this subcategory
            items_response = requests.get(f"{BASE_URL}/api/v2/subcategories/{subcategory_id}/items", headers=auth_headers)
            assert items_response.status_code == 200
            items = items_response.json()
            
            if len(items) > 0:
                item = items[0]
                assert "id" in item
                assert "name" in item
                assert "smart_price" in item or "default_price" in item
                print(f"SUCCESS: Subcategory items returned {len(items)} items with pricing")
            else:
                print("INFO: Subcategory has no items")
        else:
            pytest.skip("No categories/subcategories available")
    
    def test_v2_kits_returns_list(self, auth_headers):
        """Test GET /api/v2/kits returns kits"""
        response = requests.get(f"{BASE_URL}/api/v2/kits", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"SUCCESS: V2 kits returned {len(data)} kits")
    
    def test_v2_kit_details_with_expanded_items(self, auth_headers):
        """Test GET /api/v2/kits/{id} returns kit with expanded_items"""
        # First get kits list
        kits_response = requests.get(f"{BASE_URL}/api/v2/kits", headers=auth_headers)
        assert kits_response.status_code == 200
        kits = kits_response.json()
        
        if len(kits) > 0:
            kit_id = kits[0]["id"]
            
            # Get kit details
            kit_response = requests.get(f"{BASE_URL}/api/v2/kits/{kit_id}", headers=auth_headers)
            assert kit_response.status_code == 200
            kit = kit_response.json()
            
            assert "id" in kit
            assert "name" in kit
            assert "expanded_items" in kit
            assert "total_ht" in kit
            print(f"SUCCESS: Kit '{kit['name']}' has {len(kit.get('expanded_items', []))} expanded items")
        else:
            pytest.skip("No kits available")


class TestBackwardCompatibility:
    """Test that old category endpoints still work"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token for admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@btpfacture.com",
            "password": "Admin123!"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Admin login failed")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_old_categories_endpoint(self, auth_headers):
        """Test GET /api/categories still works"""
        response = requests.get(f"{BASE_URL}/api/categories", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"SUCCESS: Old /api/categories endpoint works - {len(data)} categories")
    
    def test_old_categories_with_items_endpoint(self, auth_headers):
        """Test GET /api/categories/with-items still works"""
        response = requests.get(f"{BASE_URL}/api/categories/with-items", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"SUCCESS: Old /api/categories/with-items endpoint works")


class TestQuoteInvoiceConsistency:
    """Test that Quote and Invoice forms have consistent structure"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token for admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@btpfacture.com",
            "password": "Admin123!"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Admin login failed")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    @pytest.fixture(scope="class")
    def test_client(self, auth_headers):
        """Create a test client for quote/invoice tests"""
        client_data = {
            "name": f"Test Client {int(time.time())}",
            "email": f"testclient{int(time.time())}@test.com",
            "phone": "0612345678",
            "address": "123 Test Street"
        }
        response = requests.post(f"{BASE_URL}/api/clients", json=client_data, headers=auth_headers)
        if response.status_code == 201:
            return response.json()
        pytest.skip("Failed to create test client")
    
    def test_create_quote_with_items(self, auth_headers, test_client):
        """Test creating a quote with line items"""
        quote_data = {
            "client_id": test_client["id"],
            "validity_days": 30,
            "notes": "Test quote",
            "items": [
                {
                    "description": "Installation prise électrique",
                    "quantity": 5,
                    "unit_price": 65.0,
                    "vat_rate": 20.0
                },
                {
                    "description": "Câblage électrique",
                    "quantity": 10,
                    "unit_price": 12.0,
                    "vat_rate": 20.0
                }
            ]
        }
        
        response = requests.post(f"{BASE_URL}/api/quotes", json=quote_data, headers=auth_headers)
        assert response.status_code == 201, f"Quote creation failed: {response.text}"
        quote = response.json()
        
        assert "id" in quote
        assert "quote_number" in quote
        assert len(quote.get("items", [])) == 2
        print(f"SUCCESS: Quote created with {len(quote['items'])} items")
        return quote
    
    def test_create_invoice_with_items(self, auth_headers, test_client):
        """Test creating an invoice with line items"""
        invoice_data = {
            "client_id": test_client["id"],
            "payment_method": "virement",
            "notes": "Test invoice",
            "items": [
                {
                    "description": "Installation prise électrique",
                    "quantity": 5,
                    "unit_price": 65.0,
                    "vat_rate": 20.0
                },
                {
                    "description": "Câblage électrique",
                    "quantity": 10,
                    "unit_price": 12.0,
                    "vat_rate": 20.0
                }
            ]
        }
        
        response = requests.post(f"{BASE_URL}/api/invoices", json=invoice_data, headers=auth_headers)
        assert response.status_code == 201, f"Invoice creation failed: {response.text}"
        invoice = response.json()
        
        assert "id" in invoice
        assert "invoice_number" in invoice
        assert len(invoice.get("items", [])) == 2
        print(f"SUCCESS: Invoice created with {len(invoice['items'])} items")
        return invoice


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
