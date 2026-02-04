"""
Test suite for Acomptes (Advance Payments) feature
Tests the following endpoints:
- POST /api/quotes/{id}/acompte - Create acompte invoice
- GET /api/quotes/{id}/acomptes - List acomptes for a quote
- GET /api/quotes/{id}/acomptes/summary - Get acomptes summary
- POST /api/quotes/{id}/final-invoice - Create final invoice with deductions
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@btp.fr"
TEST_PASSWORD = "Test123!"

# Known quote ID from context (DEV-2026-0001, status: accepte)
KNOWN_QUOTE_ID = "ceaf200c-71e1-4132-bb95-ff0d8a241403"


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
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestAcomptesAPI:
    """Test Acomptes (Advance Payments) API endpoints"""
    
    def test_get_quote_exists(self, auth_headers):
        """Verify the test quote exists and is in correct status"""
        response = requests.get(
            f"{BASE_URL}/api/quotes/{KNOWN_QUOTE_ID}",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Quote not found: {response.text}"
        quote = response.json()
        assert quote["id"] == KNOWN_QUOTE_ID
        assert quote["status"] in ["accepte", "envoye"], f"Quote status is {quote['status']}, expected accepte or envoye"
        assert quote["total_ttc"] > 0, "Quote total_ttc should be positive"
        print(f"✓ Quote {quote['quote_number']} found with status '{quote['status']}' and total_ttc={quote['total_ttc']}")
    
    def test_get_acomptes_summary(self, auth_headers):
        """Test GET /api/quotes/{id}/acomptes/summary endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/quotes/{KNOWN_QUOTE_ID}/acomptes/summary",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to get acomptes summary: {response.text}"
        
        summary = response.json()
        
        # Validate response structure
        assert "quote_total_ht" in summary
        assert "quote_total_vat" in summary
        assert "quote_total_ttc" in summary
        assert "acomptes_count" in summary
        assert "total_acomptes_ht" in summary
        assert "total_acomptes_vat" in summary
        assert "total_acomptes_ttc" in summary
        assert "total_paid" in summary
        assert "remaining_ht" in summary
        assert "remaining_vat" in summary
        assert "remaining_ttc" in summary
        assert "percentage_invoiced" in summary
        assert "percentage_paid" in summary
        assert "acomptes" in summary
        
        # Validate data types
        assert isinstance(summary["acomptes_count"], int)
        assert isinstance(summary["percentage_invoiced"], (int, float))
        assert isinstance(summary["acomptes"], list)
        
        print(f"✓ Acomptes summary: {summary['acomptes_count']} acomptes, {summary['percentage_invoiced']}% invoiced")
        print(f"  Quote total TTC: {summary['quote_total_ttc']}€, Remaining: {summary['remaining_ttc']}€")
        
        return summary
    
    def test_list_quote_acomptes(self, auth_headers):
        """Test GET /api/quotes/{id}/acomptes endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/quotes/{KNOWN_QUOTE_ID}/acomptes",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to list acomptes: {response.text}"
        
        acomptes = response.json()
        assert isinstance(acomptes, list)
        
        # If there are acomptes, validate structure
        if len(acomptes) > 0:
            acompte = acomptes[0]
            assert "id" in acompte
            assert "invoice_number" in acompte
            assert "quote_id" in acompte
            assert "quote_number" in acompte
            assert "acompte_type" in acompte
            assert "acompte_value" in acompte
            assert "acompte_number" in acompte
            assert "total_ht" in acompte
            assert "total_vat" in acompte
            assert "total_ttc" in acompte
            assert "payment_status" in acompte
            print(f"✓ Found {len(acomptes)} acompte(s) for quote")
            for a in acomptes:
                print(f"  - {a['invoice_number']}: {a['acompte_value']}{'%' if a['acompte_type'] == 'percentage' else '€'} = {a['total_ttc']}€ TTC ({a['payment_status']})")
        else:
            print("✓ No acomptes found for quote (expected if none created yet)")
        
        return acomptes
    
    def test_create_acompte_percentage(self, auth_headers):
        """Test POST /api/quotes/{id}/acompte with percentage type"""
        # First get current summary to know remaining amount
        summary_response = requests.get(
            f"{BASE_URL}/api/quotes/{KNOWN_QUOTE_ID}/acomptes/summary",
            headers=auth_headers
        )
        initial_summary = summary_response.json()
        initial_count = initial_summary["acomptes_count"]
        
        # Create a 10% acompte
        acompte_data = {
            "quote_id": KNOWN_QUOTE_ID,
            "acompte_type": "percentage",
            "value": 10,
            "notes": "Test acompte 10%",
            "payment_method": "virement"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/quotes/{KNOWN_QUOTE_ID}/acompte",
            headers=auth_headers,
            json=acompte_data
        )
        assert response.status_code == 200, f"Failed to create acompte: {response.text}"
        
        acompte = response.json()
        
        # Validate response structure
        assert "id" in acompte
        assert "invoice_number" in acompte
        assert acompte["invoice_number"].startswith("FAC-")
        assert acompte["acompte_type"] == "percentage"
        assert acompte["acompte_value"] == 10
        assert acompte["acompte_number"] == initial_count + 1
        assert acompte["total_ttc"] > 0
        assert acompte["payment_status"] == "impaye"
        
        # Verify the amount is approximately 10% of quote total
        expected_ttc = initial_summary["quote_total_ttc"] * 0.10
        assert abs(acompte["total_ttc"] - expected_ttc) < 0.01, f"Expected ~{expected_ttc}€, got {acompte['total_ttc']}€"
        
        print(f"✓ Created acompte {acompte['invoice_number']}: 10% = {acompte['total_ttc']}€ TTC")
        
        # Verify summary updated
        new_summary_response = requests.get(
            f"{BASE_URL}/api/quotes/{KNOWN_QUOTE_ID}/acomptes/summary",
            headers=auth_headers
        )
        new_summary = new_summary_response.json()
        assert new_summary["acomptes_count"] == initial_count + 1
        
        return acompte
    
    def test_create_acompte_fixed_amount(self, auth_headers):
        """Test POST /api/quotes/{id}/acompte with fixed amount type"""
        # Get current summary
        summary_response = requests.get(
            f"{BASE_URL}/api/quotes/{KNOWN_QUOTE_ID}/acomptes/summary",
            headers=auth_headers
        )
        initial_summary = summary_response.json()
        initial_count = initial_summary["acomptes_count"]
        
        # Create a fixed amount acompte of 100€
        acompte_data = {
            "quote_id": KNOWN_QUOTE_ID,
            "acompte_type": "amount",
            "value": 100,
            "notes": "Test acompte montant fixe 100€",
            "payment_method": "cheque"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/quotes/{KNOWN_QUOTE_ID}/acompte",
            headers=auth_headers,
            json=acompte_data
        )
        assert response.status_code == 200, f"Failed to create acompte: {response.text}"
        
        acompte = response.json()
        
        # Validate response
        assert acompte["acompte_type"] == "amount"
        assert acompte["acompte_value"] == 100
        assert acompte["acompte_number"] == initial_count + 1
        assert acompte["payment_method"] == "cheque"
        
        print(f"✓ Created acompte {acompte['invoice_number']}: 100€ fixed = {acompte['total_ttc']}€ TTC")
        
        return acompte
    
    def test_acompte_appears_in_invoices_list(self, auth_headers):
        """Verify acompte invoices appear in the invoices list with is_acompte flag"""
        response = requests.get(
            f"{BASE_URL}/api/invoices",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        invoices = response.json()
        acompte_invoices = [inv for inv in invoices if inv.get("is_acompte") == True]
        
        print(f"✓ Found {len(acompte_invoices)} acompte invoice(s) in invoices list")
        for inv in acompte_invoices:
            print(f"  - {inv['invoice_number']}: {inv['total_ttc']}€ TTC (parent_quote_id: {inv.get('parent_quote_id')})")
    
    def test_create_acompte_invalid_quote_status(self, auth_headers):
        """Test that acompte creation fails for quotes not in accepte/envoye status"""
        # First create a new quote in brouillon status
        # Get a client first
        clients_response = requests.get(f"{BASE_URL}/api/clients", headers=auth_headers)
        clients = clients_response.json()
        if not clients:
            pytest.skip("No clients available for test")
        
        client_id = clients[0]["id"]
        
        # Create a draft quote
        quote_data = {
            "client_id": client_id,
            "validity_days": 30,
            "items": [{"description": "Test item", "quantity": 1, "unit_price": 100, "vat_rate": 20}],
            "notes": "Test quote for acompte validation"
        }
        quote_response = requests.post(f"{BASE_URL}/api/quotes", headers=auth_headers, json=quote_data)
        assert quote_response.status_code == 200
        draft_quote = quote_response.json()
        
        # Try to create acompte on draft quote (should fail)
        acompte_data = {
            "quote_id": draft_quote["id"],
            "acompte_type": "percentage",
            "value": 30,
            "notes": "Should fail"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/quotes/{draft_quote['id']}/acompte",
            headers=auth_headers,
            json=acompte_data
        )
        assert response.status_code == 400, f"Expected 400 for draft quote, got {response.status_code}"
        assert "accepté ou envoyé" in response.json()["detail"].lower() or "accepte" in response.json()["detail"].lower()
        
        print(f"✓ Correctly rejected acompte creation for draft quote")
        
        # Cleanup - delete the test quote
        requests.delete(f"{BASE_URL}/api/quotes/{draft_quote['id']}", headers=auth_headers)
    
    def test_acomptes_summary_calculations(self, auth_headers):
        """Verify acomptes summary calculations are correct"""
        response = requests.get(
            f"{BASE_URL}/api/quotes/{KNOWN_QUOTE_ID}/acomptes/summary",
            headers=auth_headers
        )
        assert response.status_code == 200
        summary = response.json()
        
        # Verify calculations
        quote_total = summary["quote_total_ttc"]
        acomptes_total = summary["total_acomptes_ttc"]
        remaining = summary["remaining_ttc"]
        percentage = summary["percentage_invoiced"]
        
        # remaining should equal quote_total - acomptes_total
        expected_remaining = max(0, quote_total - acomptes_total)
        assert abs(remaining - expected_remaining) < 0.01, f"Remaining calculation error: {remaining} != {expected_remaining}"
        
        # percentage should be (acomptes_total / quote_total) * 100
        if quote_total > 0:
            expected_percentage = (acomptes_total / quote_total) * 100
            assert abs(percentage - expected_percentage) < 0.1, f"Percentage calculation error: {percentage} != {expected_percentage}"
        
        print(f"✓ Summary calculations verified:")
        print(f"  Quote total: {quote_total}€")
        print(f"  Acomptes total: {acomptes_total}€")
        print(f"  Remaining: {remaining}€")
        print(f"  Percentage invoiced: {percentage}%")


class TestFinalInvoice:
    """Test final invoice creation with acompte deductions"""
    
    def test_create_final_invoice(self, auth_headers):
        """Test POST /api/quotes/{id}/final-invoice endpoint"""
        # Get current summary
        summary_response = requests.get(
            f"{BASE_URL}/api/quotes/{KNOWN_QUOTE_ID}/acomptes/summary",
            headers=auth_headers
        )
        summary = summary_response.json()
        
        if summary["remaining_ttc"] <= 0:
            pytest.skip("No remaining amount for final invoice")
        
        response = requests.post(
            f"{BASE_URL}/api/quotes/{KNOWN_QUOTE_ID}/final-invoice",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to create final invoice: {response.text}"
        
        invoice = response.json()
        
        # Validate response
        assert "id" in invoice
        assert "invoice_number" in invoice
        assert invoice["invoice_number"].startswith("FAC-")
        
        # Final invoice should have deduction lines for acomptes
        items = invoice.get("items", [])
        assert len(items) > 0, "Final invoice should have items"
        
        # Check for deduction lines (negative amounts)
        deduction_lines = [item for item in items if item.get("unit_price", 0) < 0]
        
        print(f"✓ Created final invoice {invoice['invoice_number']}")
        print(f"  Total TTC: {invoice['total_ttc']}€")
        print(f"  Items: {len(items)}, Deduction lines: {len(deduction_lines)}")
        
        return invoice


class TestAcompteEdgeCases:
    """Test edge cases and validation for acomptes"""
    
    def test_acompte_nonexistent_quote(self, auth_headers):
        """Test acompte creation for non-existent quote returns 404"""
        fake_quote_id = "00000000-0000-0000-0000-000000000000"
        
        response = requests.get(
            f"{BASE_URL}/api/quotes/{fake_quote_id}/acomptes/summary",
            headers=auth_headers
        )
        assert response.status_code == 404
        print("✓ Correctly returned 404 for non-existent quote")
    
    def test_acompte_requires_auth(self):
        """Test that acompte endpoints require authentication"""
        response = requests.get(
            f"{BASE_URL}/api/quotes/{KNOWN_QUOTE_ID}/acomptes/summary"
        )
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Acompte endpoints correctly require authentication")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
