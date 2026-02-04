"""
Test suite for Project Financial Summary feature
Tests both authenticated and public endpoints for financial dashboard
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test_sit@btp.fr"
TEST_PASSWORD = "test123"

# Test data from main agent
TEST_QUOTE_ID = "71a8cca3-dd2a-4e2d-9dc0-d72622b3b1a1"
TEST_SHARE_TOKEN = "_wR86pskq_gMUy_sM00Xuw1garuGVs3bxdoJvGkOIrA"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestAuthenticatedFinancialSummary:
    """Tests for authenticated financial summary endpoint"""
    
    def test_get_financial_summary_success(self, auth_headers):
        """Test GET /api/quotes/{id}/financial-summary returns complete summary"""
        response = requests.get(
            f"{BASE_URL}/api/quotes/{TEST_QUOTE_ID}/financial-summary",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify required fields exist
        assert "quote_id" in data
        assert "quote_number" in data
        assert "client_name" in data
        assert "status" in data
        
        # Verify project totals
        assert "project_total_ht" in data
        assert "project_total_vat" in data
        assert "project_total_ttc" in data
        assert isinstance(data["project_total_ttc"], (int, float))
        
        # Verify acomptes section
        assert "acomptes" in data
        acomptes = data["acomptes"]
        assert "count" in acomptes
        assert "total_invoiced" in acomptes
        assert "total_paid" in acomptes
        assert "pending" in acomptes
        
        # Verify situations section
        assert "situations" in data
        situations = data["situations"]
        assert "count" in situations
        assert "total_invoiced" in situations
        assert "total_paid" in situations
        assert "pending" in situations
        assert "progress_percentage" in situations
        
        # Verify retenue de garantie section
        assert "retenue_garantie" in data
        retenue = data["retenue_garantie"]
        assert "total_retained" in retenue
        assert "total_released" in retenue
        assert "pending_release" in retenue
        
        # Verify totals section
        assert "totals" in data
        totals = data["totals"]
        assert "total_invoiced" in totals
        assert "total_paid" in totals
        assert "remaining_to_invoice" in totals
        assert "remaining_to_pay" in totals
        assert "percentage_paid" in totals
        
        # Verify invoices list
        assert "invoices" in data
        assert isinstance(data["invoices"], list)
        
        print(f"✓ Financial summary returned successfully for quote {data['quote_number']}")
        print(f"  - Project total TTC: {data['project_total_ttc']}€")
        print(f"  - Acomptes: {acomptes['count']} ({acomptes['total_invoiced']}€)")
        print(f"  - Situations: {situations['count']} ({situations['total_invoiced']}€)")
        print(f"  - Retenue pending: {retenue['pending_release']}€")
        print(f"  - Total paid: {totals['total_paid']}€ ({totals['percentage_paid']}%)")
    
    def test_financial_summary_invoices_list(self, auth_headers):
        """Test that invoices list contains correct fields"""
        response = requests.get(
            f"{BASE_URL}/api/quotes/{TEST_QUOTE_ID}/financial-summary",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        invoices = data.get("invoices", [])
        if len(invoices) > 0:
            invoice = invoices[0]
            # Verify invoice fields
            assert "id" in invoice
            assert "invoice_number" in invoice
            assert "type" in invoice
            assert "date" in invoice
            assert "total_ttc" in invoice
            assert "payment_status" in invoice
            assert "has_retenue" in invoice
            
            print(f"✓ Invoices list contains {len(invoices)} invoices with correct structure")
            for inv in invoices:
                print(f"  - {inv['invoice_number']}: {inv['type']} - {inv['total_ttc']}€ ({inv['payment_status']})")
        else:
            print("✓ No invoices found for this quote (empty list returned)")
    
    def test_financial_summary_calculations(self, auth_headers):
        """Test that financial calculations are correct"""
        response = requests.get(
            f"{BASE_URL}/api/quotes/{TEST_QUOTE_ID}/financial-summary",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        totals = data["totals"]
        acomptes = data["acomptes"]
        situations = data["situations"]
        
        # Total invoiced should equal acomptes + situations
        expected_invoiced = acomptes["total_invoiced"] + situations["total_invoiced"]
        assert abs(totals["total_invoiced"] - expected_invoiced) < 0.01, \
            f"Total invoiced mismatch: {totals['total_invoiced']} != {expected_invoiced}"
        
        # Remaining to invoice should be project total - total invoiced
        expected_remaining = data["project_total_ttc"] - totals["total_invoiced"]
        assert abs(totals["remaining_to_invoice"] - max(0, expected_remaining)) < 0.01, \
            f"Remaining to invoice mismatch: {totals['remaining_to_invoice']} != {max(0, expected_remaining)}"
        
        print(f"✓ Financial calculations are correct")
        print(f"  - Total invoiced: {totals['total_invoiced']}€ = Acomptes({acomptes['total_invoiced']}€) + Situations({situations['total_invoiced']}€)")
        print(f"  - Remaining to invoice: {totals['remaining_to_invoice']}€")
    
    def test_financial_summary_not_found(self, auth_headers):
        """Test 404 for non-existent quote"""
        response = requests.get(
            f"{BASE_URL}/api/quotes/non-existent-id/financial-summary",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        print("✓ 404 returned for non-existent quote")
    
    def test_financial_summary_unauthorized(self):
        """Test 401/403 without authentication"""
        response = requests.get(
            f"{BASE_URL}/api/quotes/{TEST_QUOTE_ID}/financial-summary"
        )
        
        assert response.status_code in [401, 403]
        print(f"✓ {response.status_code} returned without authentication")


class TestPublicFinancialSummary:
    """Tests for public financial summary endpoint"""
    
    def test_public_financial_summary_success(self):
        """Test GET /api/public/quote/{token}/financial-summary returns summary"""
        response = requests.get(
            f"{BASE_URL}/api/public/quote/{TEST_SHARE_TOKEN}/financial-summary"
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify same structure as authenticated endpoint
        assert "quote_id" in data
        assert "quote_number" in data
        assert "client_name" in data
        assert "project_total_ttc" in data
        assert "acomptes" in data
        assert "situations" in data
        assert "retenue_garantie" in data
        assert "totals" in data
        assert "invoices" in data
        
        print(f"✓ Public financial summary returned successfully")
        print(f"  - Quote: {data['quote_number']}")
        print(f"  - Client: {data['client_name']}")
        print(f"  - Total TTC: {data['project_total_ttc']}€")
    
    def test_public_financial_summary_invalid_token(self):
        """Test 404 for invalid share token"""
        response = requests.get(
            f"{BASE_URL}/api/public/quote/invalid-token-12345/financial-summary"
        )
        
        assert response.status_code == 404
        print("✓ 404 returned for invalid share token")
    
    def test_public_financial_summary_data_matches_authenticated(self, auth_headers):
        """Test that public and authenticated endpoints return same data"""
        # Get authenticated response
        auth_response = requests.get(
            f"{BASE_URL}/api/quotes/{TEST_QUOTE_ID}/financial-summary",
            headers=auth_headers
        )
        
        # Get public response
        public_response = requests.get(
            f"{BASE_URL}/api/public/quote/{TEST_SHARE_TOKEN}/financial-summary"
        )
        
        if auth_response.status_code == 200 and public_response.status_code == 200:
            auth_data = auth_response.json()
            public_data = public_response.json()
            
            # Compare key fields
            assert auth_data["quote_number"] == public_data["quote_number"]
            assert auth_data["project_total_ttc"] == public_data["project_total_ttc"]
            assert auth_data["totals"]["total_invoiced"] == public_data["totals"]["total_invoiced"]
            assert auth_data["totals"]["total_paid"] == public_data["totals"]["total_paid"]
            
            print("✓ Public and authenticated endpoints return matching data")
        else:
            pytest.skip("Could not compare - one endpoint failed")


class TestFinancialSummaryEdgeCases:
    """Test edge cases for financial summary"""
    
    def test_financial_summary_with_new_quote(self, auth_headers):
        """Test financial summary for a quote with no invoices"""
        # First, create a new client
        client_response = requests.post(
            f"{BASE_URL}/api/clients",
            headers=auth_headers,
            json={
                "name": "TEST_Financial_Summary_Client",
                "email": "test_fs@example.com"
            }
        )
        
        if client_response.status_code != 200:
            pytest.skip("Could not create test client")
        
        client_id = client_response.json()["id"]
        
        # Create a new quote
        quote_response = requests.post(
            f"{BASE_URL}/api/quotes",
            headers=auth_headers,
            json={
                "client_id": client_id,
                "items": [
                    {"description": "Test item", "quantity": 1, "unit_price": 1000, "vat_rate": 20}
                ]
            }
        )
        
        if quote_response.status_code != 200:
            pytest.skip("Could not create test quote")
        
        quote_id = quote_response.json()["id"]
        
        # Get financial summary for new quote
        summary_response = requests.get(
            f"{BASE_URL}/api/quotes/{quote_id}/financial-summary",
            headers=auth_headers
        )
        
        assert summary_response.status_code == 200
        data = summary_response.json()
        
        # Verify empty state
        assert data["acomptes"]["count"] == 0
        assert data["situations"]["count"] == 0
        assert data["totals"]["total_invoiced"] == 0
        assert data["totals"]["total_paid"] == 0
        assert len(data["invoices"]) == 0
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/quotes/{quote_id}", headers=auth_headers)
        requests.delete(f"{BASE_URL}/api/clients/{client_id}", headers=auth_headers)
        
        print("✓ Financial summary works correctly for quote with no invoices")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
