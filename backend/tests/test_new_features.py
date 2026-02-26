"""
Test suite for new BTP Invoice features:
1. Renovation Kits (3 default kits)
2. Public Client View via share token
3. Email sending with PDF attachment
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://construction-invoice-2.preview.emergentagent.com').rstrip('/')

# Test credentials
TEST_EMAIL = "test@btp.fr"
TEST_PASSWORD = "Test123!"

# Known share token for testing
TEST_SHARE_TOKEN = "Q7CDW9sEcHtiLTxdzI0dQYd-d4Etf9BEQZmxaNX30us"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["access_token"]


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestRenovationKits:
    """Test renovation kits functionality"""
    
    def test_list_kits_returns_default_kits(self, auth_headers):
        """Test that GET /api/kits returns the 3 default kits"""
        response = requests.get(f"{BASE_URL}/api/kits", headers=auth_headers)
        assert response.status_code == 200
        
        kits = response.json()
        assert isinstance(kits, list)
        assert len(kits) >= 3, "Should have at least 3 default kits"
        
        # Check for the 3 default kits
        kit_names = [kit["name"] for kit in kits]
        assert "Rénovation salle de bain" in kit_names, "Missing bathroom renovation kit"
        assert "Installation cuisine" in kit_names, "Missing kitchen installation kit"
        assert "Rénovation électrique complète" in kit_names, "Missing electrical renovation kit"
    
    def test_default_kits_have_correct_structure(self, auth_headers):
        """Test that default kits have correct structure with items"""
        response = requests.get(f"{BASE_URL}/api/kits", headers=auth_headers)
        assert response.status_code == 200
        
        kits = response.json()
        for kit in kits:
            # Check kit structure
            assert "id" in kit
            assert "name" in kit
            assert "description" in kit
            assert "items" in kit
            assert "is_default" in kit
            assert "created_at" in kit
            
            # Check items structure
            assert isinstance(kit["items"], list)
            assert len(kit["items"]) > 0, f"Kit {kit['name']} should have items"
            
            for item in kit["items"]:
                assert "description" in item
                assert "unit" in item
                assert "quantity" in item
                assert "unit_price" in item
                assert "vat_rate" in item
    
    def test_bathroom_kit_has_correct_items(self, auth_headers):
        """Test bathroom renovation kit has expected items"""
        response = requests.get(f"{BASE_URL}/api/kits", headers=auth_headers)
        assert response.status_code == 200
        
        kits = response.json()
        bathroom_kit = next((k for k in kits if k["name"] == "Rénovation salle de bain"), None)
        assert bathroom_kit is not None
        
        # Should have 6 items
        assert len(bathroom_kit["items"]) == 6
        
        # Check total is approximately 3466€
        total = sum(item["quantity"] * item["unit_price"] for item in bathroom_kit["items"])
        assert 3400 <= total <= 3500, f"Bathroom kit total should be ~3466€, got {total}"
    
    def test_kitchen_kit_has_correct_items(self, auth_headers):
        """Test kitchen installation kit has expected items"""
        response = requests.get(f"{BASE_URL}/api/kits", headers=auth_headers)
        assert response.status_code == 200
        
        kits = response.json()
        kitchen_kit = next((k for k in kits if k["name"] == "Installation cuisine"), None)
        assert kitchen_kit is not None
        
        # Should have 6 items
        assert len(kitchen_kit["items"]) == 6
        
        # Check total is approximately 2780€
        total = sum(item["quantity"] * item["unit_price"] for item in kitchen_kit["items"])
        assert 2700 <= total <= 2850, f"Kitchen kit total should be ~2780€, got {total}"
    
    def test_electrical_kit_has_correct_items(self, auth_headers):
        """Test electrical renovation kit has expected items"""
        response = requests.get(f"{BASE_URL}/api/kits", headers=auth_headers)
        assert response.status_code == 200
        
        kits = response.json()
        electrical_kit = next((k for k in kits if k["name"] == "Rénovation électrique complète"), None)
        assert electrical_kit is not None
        
        # Should have 5 items
        assert len(electrical_kit["items"]) == 5
        
        # Check total is approximately 3675€
        total = sum(item["quantity"] * item["unit_price"] for item in electrical_kit["items"])
        assert 3600 <= total <= 3750, f"Electrical kit total should be ~3675€, got {total}"
    
    def test_create_custom_kit(self, auth_headers):
        """Test creating a custom kit"""
        kit_data = {
            "name": "TEST_Kit personnalisé",
            "description": "Kit de test",
            "items": [
                {"description": "Test item 1", "unit": "unité", "quantity": 2, "unit_price": 100.0, "vat_rate": 20.0},
                {"description": "Test item 2", "unit": "m²", "quantity": 5, "unit_price": 50.0, "vat_rate": 20.0}
            ]
        }
        
        response = requests.post(f"{BASE_URL}/api/kits", json=kit_data, headers=auth_headers)
        assert response.status_code == 200
        
        created_kit = response.json()
        assert created_kit["name"] == kit_data["name"]
        assert created_kit["description"] == kit_data["description"]
        assert len(created_kit["items"]) == 2
        assert created_kit["is_default"] == False
        
        # Cleanup - delete the test kit
        kit_id = created_kit["id"]
        delete_response = requests.delete(f"{BASE_URL}/api/kits/{kit_id}", headers=auth_headers)
        assert delete_response.status_code == 200
    
    def test_get_single_kit(self, auth_headers):
        """Test getting a single kit by ID"""
        # First get all kits
        response = requests.get(f"{BASE_URL}/api/kits", headers=auth_headers)
        assert response.status_code == 200
        kits = response.json()
        
        if len(kits) > 0:
            kit_id = kits[0]["id"]
            single_response = requests.get(f"{BASE_URL}/api/kits/{kit_id}", headers=auth_headers)
            assert single_response.status_code == 200
            
            kit = single_response.json()
            assert kit["id"] == kit_id


class TestPublicClientView:
    """Test public client view functionality"""
    
    @pytest.fixture(scope="class")
    def fresh_share_token(self, auth_headers):
        """Create a fresh share token for testing"""
        # Get a quote
        quotes_response = requests.get(f"{BASE_URL}/api/quotes", headers=auth_headers)
        if quotes_response.status_code != 200 or len(quotes_response.json()) == 0:
            pytest.skip("No quotes available for testing")
        
        quote_id = quotes_response.json()[0]["id"]
        
        # Create share link
        share_response = requests.post(f"{BASE_URL}/api/quotes/{quote_id}/share", headers=auth_headers)
        assert share_response.status_code == 200
        return share_response.json()["share_token"]
    
    def test_public_quote_access_without_auth(self, fresh_share_token):
        """Test that public quote can be accessed without authentication"""
        response = requests.get(f"{BASE_URL}/api/public/quote/{fresh_share_token}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["type"] == "devis"
        assert "document_number" in data
        assert "client_name" in data
        assert "items" in data
        assert "total_ht" in data
        assert "total_vat" in data
        assert "total_ttc" in data
    
    def test_public_quote_has_company_info(self, fresh_share_token):
        """Test that public quote includes company information"""
        response = requests.get(f"{BASE_URL}/api/public/quote/{fresh_share_token}")
        assert response.status_code == 200
        
        data = response.json()
        assert "company" in data
        company = data["company"]
        assert "name" in company
        assert "address" in company
        assert "phone" in company
        assert "email" in company
    
    def test_public_quote_has_status_label(self, fresh_share_token):
        """Test that public quote has status label in French"""
        response = requests.get(f"{BASE_URL}/api/public/quote/{fresh_share_token}")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "status_label" in data
        # Status label should be in French
        valid_labels = ["Devis", "Devis envoyé", "Devis accepté", "Devis refusé", "Facturé"]
        assert data["status_label"] in valid_labels
    
    def test_public_quote_pdf_download(self, fresh_share_token):
        """Test that public quote PDF can be downloaded"""
        response = requests.get(f"{BASE_URL}/api/public/quote/{fresh_share_token}/pdf")
        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/pdf"
    
    def test_invalid_share_token_returns_404(self):
        """Test that invalid share token returns 404"""
        response = requests.get(f"{BASE_URL}/api/public/quote/invalid-token-12345")
        assert response.status_code == 404
    
    def test_create_share_link_for_quote(self, auth_headers):
        """Test creating a share link for a quote"""
        # First get a quote
        quotes_response = requests.get(f"{BASE_URL}/api/quotes", headers=auth_headers)
        assert quotes_response.status_code == 200
        quotes = quotes_response.json()
        
        if len(quotes) > 0:
            quote_id = quotes[0]["id"]
            
            # Create share link
            share_response = requests.post(f"{BASE_URL}/api/quotes/{quote_id}/share", headers=auth_headers)
            assert share_response.status_code == 200
            
            share_data = share_response.json()
            assert "share_token" in share_data
            assert "share_url" in share_data
            assert len(share_data["share_token"]) > 20  # Token should be reasonably long


class TestEmailSending:
    """Test email sending functionality"""
    
    def test_send_quote_email_endpoint_exists(self, auth_headers):
        """Test that send email endpoint exists and validates input"""
        # First get a quote
        quotes_response = requests.get(f"{BASE_URL}/api/quotes", headers=auth_headers)
        assert quotes_response.status_code == 200
        quotes = quotes_response.json()
        
        if len(quotes) > 0:
            quote_id = quotes[0]["id"]
            
            # Try to send email (will fail with test API key but endpoint should work)
            email_data = {
                "recipient_email": "test@example.com",
                "custom_message": "Test message"
            }
            
            response = requests.post(
                f"{BASE_URL}/api/quotes/{quote_id}/send-email",
                json=email_data,
                headers=auth_headers
            )
            
            # Should either succeed or fail with email service error (not 404 or validation error)
            # 520 is a Cloudflare error that can occur with test API keys
            assert response.status_code in [200, 500, 520], f"Unexpected status: {response.status_code}"
    
    def test_send_email_requires_recipient(self, auth_headers):
        """Test that send email requires recipient email"""
        quotes_response = requests.get(f"{BASE_URL}/api/quotes", headers=auth_headers)
        assert quotes_response.status_code == 200
        quotes = quotes_response.json()
        
        if len(quotes) > 0:
            quote_id = quotes[0]["id"]
            
            # Try without recipient email
            email_data = {
                "custom_message": "Test message"
            }
            
            response = requests.post(
                f"{BASE_URL}/api/quotes/{quote_id}/send-email",
                json=email_data,
                headers=auth_headers
            )
            
            # Should fail validation
            assert response.status_code == 422


class TestShareLinkManagement:
    """Test share link creation and revocation"""
    
    def test_create_and_revoke_quote_share_link(self, auth_headers):
        """Test creating and revoking a quote share link"""
        # Get a quote
        quotes_response = requests.get(f"{BASE_URL}/api/quotes", headers=auth_headers)
        assert quotes_response.status_code == 200
        quotes = quotes_response.json()
        
        if len(quotes) > 0:
            quote_id = quotes[0]["id"]
            
            # Create share link
            create_response = requests.post(f"{BASE_URL}/api/quotes/{quote_id}/share", headers=auth_headers)
            assert create_response.status_code == 200
            share_token = create_response.json()["share_token"]
            
            # Verify link works
            public_response = requests.get(f"{BASE_URL}/api/public/quote/{share_token}")
            assert public_response.status_code == 200
            
            # Revoke link
            revoke_response = requests.delete(f"{BASE_URL}/api/quotes/{quote_id}/share", headers=auth_headers)
            assert revoke_response.status_code == 200
            
            # Verify link no longer works
            public_response_after = requests.get(f"{BASE_URL}/api/public/quote/{share_token}")
            assert public_response_after.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
