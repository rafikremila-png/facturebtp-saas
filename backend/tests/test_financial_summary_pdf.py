"""
Test suite for Financial Summary PDF Export feature
Tests the PDF download endpoint for project financial summary
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials - will create new user if needed
TEST_EMAIL = "test_pdf@btp.fr"
TEST_PASSWORD = "Test1234"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token - register if user doesn't exist"""
    # Try login first
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    
    if response.status_code == 200:
        return response.json().get("access_token")
    
    # If login fails, try to register
    register_response = requests.post(f"{BASE_URL}/api/auth/register", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "name": "Test PDF User"
    })
    
    if register_response.status_code == 200:
        return register_response.json().get("access_token")
    
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture(scope="module")
def test_quote_with_data(auth_headers):
    """Create a test quote with situations for testing financial summary PDF"""
    # Create a client
    client_response = requests.post(
        f"{BASE_URL}/api/clients",
        headers=auth_headers,
        json={
            "name": "TEST_PDF_Client",
            "email": "test_pdf_client@example.com",
            "address": "123 Test Street",
            "phone": "0123456789"
        }
    )
    
    if client_response.status_code != 200:
        pytest.skip(f"Could not create test client: {client_response.text}")
    
    client_id = client_response.json()["id"]
    
    # Create a quote
    quote_response = requests.post(
        f"{BASE_URL}/api/quotes",
        headers=auth_headers,
        json={
            "client_id": client_id,
            "items": [
                {"description": "Travaux de rénovation", "quantity": 1, "unit_price": 5000, "vat_rate": 20},
                {"description": "Matériaux", "quantity": 10, "unit_price": 100, "vat_rate": 20}
            ],
            "notes": "Test quote for PDF export"
        }
    )
    
    if quote_response.status_code != 200:
        pytest.skip(f"Could not create test quote: {quote_response.text}")
    
    quote_data = quote_response.json()
    quote_id = quote_data["id"]
    quote_number = quote_data["quote_number"]
    
    # Update quote status to "accepte" to allow creating situations
    update_response = requests.put(
        f"{BASE_URL}/api/quotes/{quote_id}",
        headers=auth_headers,
        json={"status": "accepte"}
    )
    
    # Create a situation (30% progress)
    situation_response = requests.post(
        f"{BASE_URL}/api/quotes/{quote_id}/situation",
        headers=auth_headers,
        json={
            "quote_id": quote_id,
            "situation_type": "global",
            "global_percentage": 30,
            "notes": "First situation for PDF test"
        }
    )
    
    yield {
        "quote_id": quote_id,
        "quote_number": quote_number,
        "client_id": client_id
    }
    
    # Cleanup after tests
    # Delete invoices/situations first
    invoices_response = requests.get(f"{BASE_URL}/api/invoices", headers=auth_headers)
    if invoices_response.status_code == 200:
        for inv in invoices_response.json():
            if inv.get("quote_id") == quote_id or inv.get("parent_quote_id") == quote_id:
                requests.delete(f"{BASE_URL}/api/invoices/{inv['id']}", headers=auth_headers)
    
    requests.delete(f"{BASE_URL}/api/quotes/{quote_id}", headers=auth_headers)
    requests.delete(f"{BASE_URL}/api/clients/{client_id}", headers=auth_headers)


class TestFinancialSummaryPDFEndpoint:
    """Tests for financial summary PDF download endpoint"""
    
    def test_financial_summary_endpoint_returns_data(self, auth_headers, test_quote_with_data):
        """Test GET /api/quotes/{id}/financial-summary returns data"""
        quote_id = test_quote_with_data["quote_id"]
        
        response = requests.get(
            f"{BASE_URL}/api/quotes/{quote_id}/financial-summary",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "quote_id" in data
        assert "quote_number" in data
        assert "project_total_ttc" in data
        assert "totals" in data
        
        print(f"✓ Financial summary endpoint works for quote {data['quote_number']}")
        print(f"  - Project total TTC: {data['project_total_ttc']}€")
        print(f"  - Situations count: {data['situations']['count']}")
    
    def test_download_financial_summary_pdf_success(self, auth_headers, test_quote_with_data):
        """Test GET /api/quotes/{id}/financial-summary/pdf returns valid PDF"""
        quote_id = test_quote_with_data["quote_id"]
        quote_number = test_quote_with_data["quote_number"]
        
        response = requests.get(
            f"{BASE_URL}/api/quotes/{quote_id}/financial-summary/pdf",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Verify content type is PDF
        content_type = response.headers.get('Content-Type', '')
        assert 'application/pdf' in content_type, f"Expected PDF content type, got: {content_type}"
        
        # Verify content disposition header for download
        content_disposition = response.headers.get('Content-Disposition', '')
        assert 'attachment' in content_disposition, f"Expected attachment disposition, got: {content_disposition}"
        assert 'Recapitulatif_financier' in content_disposition, f"Expected filename in disposition, got: {content_disposition}"
        
        # Verify PDF content starts with PDF magic bytes
        pdf_content = response.content
        assert len(pdf_content) > 0, "PDF content is empty"
        assert pdf_content[:4] == b'%PDF', f"Content does not start with PDF magic bytes: {pdf_content[:10]}"
        
        print(f"✓ Financial summary PDF downloaded successfully")
        print(f"  - Content-Type: {content_type}")
        print(f"  - Content-Disposition: {content_disposition}")
        print(f"  - PDF size: {len(pdf_content)} bytes")
    
    def test_download_financial_summary_pdf_not_found(self, auth_headers):
        """Test 404 for non-existent quote PDF"""
        response = requests.get(
            f"{BASE_URL}/api/quotes/non-existent-id-12345/financial-summary/pdf",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        print("✓ 404 returned for non-existent quote PDF")
    
    def test_download_financial_summary_pdf_unauthorized(self, test_quote_with_data):
        """Test 401/403 without authentication for PDF"""
        quote_id = test_quote_with_data["quote_id"]
        
        response = requests.get(
            f"{BASE_URL}/api/quotes/{quote_id}/financial-summary/pdf"
        )
        
        assert response.status_code in [401, 403]
        print(f"✓ {response.status_code} returned without authentication for PDF")


class TestFinancialSummaryPDFContent:
    """Tests for PDF content validation"""
    
    def test_pdf_contains_valid_structure(self, auth_headers, test_quote_with_data):
        """Test that PDF has valid structure and reasonable size"""
        quote_id = test_quote_with_data["quote_id"]
        
        response = requests.get(
            f"{BASE_URL}/api/quotes/{quote_id}/financial-summary/pdf",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        pdf_content = response.content
        
        # PDF should have reasonable size (at least 1KB, less than 10MB)
        assert len(pdf_content) > 1000, f"PDF too small: {len(pdf_content)} bytes"
        assert len(pdf_content) < 10 * 1024 * 1024, f"PDF too large: {len(pdf_content)} bytes"
        
        # Check PDF ends with %%EOF marker (standard PDF ending)
        assert b'%%EOF' in pdf_content[-100:], "PDF does not end with %%EOF marker"
        
        print(f"✓ PDF has valid structure")
        print(f"  - Size: {len(pdf_content)} bytes")
        print(f"  - Contains %%EOF marker: Yes")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
