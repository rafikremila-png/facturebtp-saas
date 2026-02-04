"""
Test suite for Situations (Progressive Billing) feature
Tests the following endpoints:
- POST /api/quotes/{id}/situation - Create situation invoice (global or per_line mode)
- GET /api/quotes/{id}/situations - List situations for a quote
- GET /api/quotes/{id}/situations/summary - Get situations summary
- POST /api/quotes/{id}/situation/final-invoice - Create final invoice (décompte final)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test_sit@btp.fr"
TEST_PASSWORD = "test123"

# Known quote ID from context (should be in accepte status)
KNOWN_QUOTE_ID = "71a8cca3-dd2a-4e2d-9dc0-d72622b3b1a1"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code != 200:
        # Try alternate credentials
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@btp.fr",
            "password": "Test123!"
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


@pytest.fixture(scope="module")
def test_quote(auth_headers):
    """Get or create a test quote in accepte status for situation testing"""
    # First try to get the known quote
    response = requests.get(
        f"{BASE_URL}/api/quotes/{KNOWN_QUOTE_ID}",
        headers=auth_headers
    )
    
    if response.status_code == 200:
        quote = response.json()
        if quote["status"] in ["accepte", "envoye"]:
            print(f"✓ Using existing quote {quote['quote_number']} (status: {quote['status']})")
            return quote
    
    # If not found or wrong status, create a new quote
    # First get a client
    clients_response = requests.get(f"{BASE_URL}/api/clients", headers=auth_headers)
    clients = clients_response.json()
    
    if not clients:
        # Create a test client
        client_data = {
            "name": "TEST_Client Situation",
            "address": "123 Rue Test",
            "phone": "0123456789",
            "email": "test_situation@example.com"
        }
        client_response = requests.post(f"{BASE_URL}/api/clients", headers=auth_headers, json=client_data)
        client_id = client_response.json()["id"]
    else:
        client_id = clients[0]["id"]
    
    # Create a quote with multiple items for per_line testing
    quote_data = {
        "client_id": client_id,
        "validity_days": 30,
        "items": [
            {"description": "Travaux de maçonnerie", "quantity": 10, "unit_price": 100, "vat_rate": 20},
            {"description": "Pose de carrelage", "quantity": 25, "unit_price": 45, "vat_rate": 20},
            {"description": "Peinture intérieure", "quantity": 50, "unit_price": 18, "vat_rate": 20}
        ],
        "notes": "Test quote for situation testing"
    }
    
    quote_response = requests.post(f"{BASE_URL}/api/quotes", headers=auth_headers, json=quote_data)
    assert quote_response.status_code == 200, f"Failed to create quote: {quote_response.text}"
    quote = quote_response.json()
    
    # Update status to accepte
    update_response = requests.put(
        f"{BASE_URL}/api/quotes/{quote['id']}",
        headers=auth_headers,
        json={"status": "accepte"}
    )
    assert update_response.status_code == 200
    
    quote["status"] = "accepte"
    print(f"✓ Created test quote {quote['quote_number']} with status 'accepte'")
    return quote


class TestSituationsAPI:
    """Test Situations (Progressive Billing) API endpoints"""
    
    def test_get_situations_summary_empty(self, auth_headers, test_quote):
        """Test GET /api/quotes/{id}/situations/summary with no situations"""
        response = requests.get(
            f"{BASE_URL}/api/quotes/{test_quote['id']}/situations/summary",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to get situations summary: {response.text}"
        
        summary = response.json()
        
        # Validate response structure
        assert "quote_total_ht" in summary
        assert "quote_total_vat" in summary
        assert "quote_total_ttc" in summary
        assert "situations_count" in summary
        assert "current_progress_percentage" in summary
        assert "total_situations_ht" in summary
        assert "total_situations_vat" in summary
        assert "total_situations_ttc" in summary
        assert "total_paid" in summary
        assert "remaining_ht" in summary
        assert "remaining_vat" in summary
        assert "remaining_ttc" in summary
        assert "percentage_invoiced" in summary
        assert "percentage_paid" in summary
        assert "situations" in summary
        
        print(f"✓ Situations summary structure validated")
        print(f"  Quote total TTC: {summary['quote_total_ttc']}€")
        print(f"  Current progress: {summary['current_progress_percentage']}%")
        print(f"  Situations count: {summary['situations_count']}")
        
        return summary
    
    def test_list_situations_empty(self, auth_headers, test_quote):
        """Test GET /api/quotes/{id}/situations with no situations"""
        response = requests.get(
            f"{BASE_URL}/api/quotes/{test_quote['id']}/situations",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to list situations: {response.text}"
        
        situations = response.json()
        assert isinstance(situations, list)
        print(f"✓ List situations endpoint works, found {len(situations)} situation(s)")
        
        return situations
    
    def test_create_situation_global_mode(self, auth_headers, test_quote):
        """Test POST /api/quotes/{id}/situation with global percentage mode"""
        # Get current progress
        summary_response = requests.get(
            f"{BASE_URL}/api/quotes/{test_quote['id']}/situations/summary",
            headers=auth_headers
        )
        initial_summary = summary_response.json()
        initial_progress = initial_summary["current_progress_percentage"]
        initial_count = initial_summary["situations_count"]
        
        # Create a 30% global situation
        new_percentage = initial_progress + 30
        if new_percentage > 100:
            new_percentage = 100
        
        situation_data = {
            "quote_id": test_quote["id"],
            "situation_type": "global",
            "global_percentage": new_percentage,
            "notes": "Test situation 30% global",
            "payment_method": "virement",
            "chantier_ref": f"Chantier {test_quote['quote_number']}"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/quotes/{test_quote['id']}/situation",
            headers=auth_headers,
            json=situation_data
        )
        assert response.status_code == 200, f"Failed to create situation: {response.text}"
        
        situation = response.json()
        
        # Validate response structure
        assert "id" in situation
        assert "invoice_number" in situation
        assert situation["invoice_number"].startswith("FAC-")
        assert "situation_type" in situation
        assert situation["situation_type"] == "global"
        assert "situation_number" in situation
        assert situation["situation_number"] == initial_count + 1
        assert "current_percentage" in situation
        assert situation["current_percentage"] == new_percentage
        assert "previous_percentage" in situation
        assert situation["previous_percentage"] == initial_progress
        assert "situation_percentage" in situation
        assert "total_ht" in situation
        assert "total_vat" in situation
        assert "total_ttc" in situation
        assert situation["total_ttc"] > 0
        assert "payment_status" in situation
        assert situation["payment_status"] == "impaye"
        assert "chantier_ref" in situation
        
        # Verify the amount is correct (percentage of quote total)
        expected_situation_pct = new_percentage - initial_progress
        expected_ttc = test_quote["total_ttc"] * (expected_situation_pct / 100)
        assert abs(situation["total_ttc"] - expected_ttc) < 0.01, f"Expected ~{expected_ttc}€, got {situation['total_ttc']}€"
        
        print(f"✓ Created global situation {situation['invoice_number']}")
        print(f"  Situation number: {situation['situation_number']}")
        print(f"  Progress: {situation['previous_percentage']}% → {situation['current_percentage']}%")
        print(f"  This situation: {situation['situation_percentage']}%")
        print(f"  Amount TTC: {situation['total_ttc']}€")
        
        return situation
    
    def test_create_situation_per_line_mode(self, auth_headers, test_quote):
        """Test POST /api/quotes/{id}/situation with per_line mode"""
        # Get current progress
        summary_response = requests.get(
            f"{BASE_URL}/api/quotes/{test_quote['id']}/situations/summary",
            headers=auth_headers
        )
        initial_summary = summary_response.json()
        initial_count = initial_summary["situations_count"]
        
        # Get line progress from previous situations
        line_progress = initial_summary.get("line_progress", [])
        
        # Create per_line situation with different progress per item
        line_items = []
        for i, item in enumerate(test_quote["items"]):
            prev_pct = line_progress[i]["cumulative_percent"] if i < len(line_progress) else 0
            # Add 20% to each line (or up to 100%)
            new_pct = min(100, prev_pct + 20)
            line_items.append({
                "description": item["description"],
                "quantity": item["quantity"],
                "unit_price": item["unit_price"],
                "vat_rate": item["vat_rate"],
                "progress_percent": new_pct
            })
        
        situation_data = {
            "quote_id": test_quote["id"],
            "situation_type": "per_line",
            "line_items": line_items,
            "notes": "Test situation per_line mode",
            "payment_method": "virement",
            "chantier_ref": f"Chantier {test_quote['quote_number']}"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/quotes/{test_quote['id']}/situation",
            headers=auth_headers,
            json=situation_data
        )
        assert response.status_code == 200, f"Failed to create per_line situation: {response.text}"
        
        situation = response.json()
        
        # Validate response
        assert situation["situation_type"] == "per_line"
        assert situation["situation_number"] == initial_count + 1
        assert situation["total_ttc"] > 0
        assert "items" in situation
        assert len(situation["items"]) == len(test_quote["items"])
        
        # Verify each item has cumulative_percent
        for item in situation["items"]:
            assert "cumulative_percent" in item or "situation_percent" in item
            assert "situation_amount_ht" in item
        
        print(f"✓ Created per_line situation {situation['invoice_number']}")
        print(f"  Situation number: {situation['situation_number']}")
        print(f"  Amount TTC: {situation['total_ttc']}€")
        print(f"  Items progress:")
        for item in situation["items"]:
            print(f"    - {item['description']}: {item.get('cumulative_percent', item.get('situation_percent', 0))}%")
        
        return situation
    
    def test_situations_summary_after_creation(self, auth_headers, test_quote):
        """Verify situations summary is updated after creating situations"""
        response = requests.get(
            f"{BASE_URL}/api/quotes/{test_quote['id']}/situations/summary",
            headers=auth_headers
        )
        assert response.status_code == 200
        summary = response.json()
        
        # Should have at least 1 situation now
        assert summary["situations_count"] >= 1, "Expected at least 1 situation"
        assert summary["current_progress_percentage"] > 0, "Expected progress > 0%"
        assert summary["total_situations_ttc"] > 0, "Expected total_situations_ttc > 0"
        
        # Verify calculations
        quote_total = summary["quote_total_ttc"]
        situations_total = summary["total_situations_ttc"]
        remaining = summary["remaining_ttc"]
        
        expected_remaining = max(0, quote_total - situations_total)
        assert abs(remaining - expected_remaining) < 0.01, f"Remaining calculation error"
        
        print(f"✓ Situations summary after creation:")
        print(f"  Situations count: {summary['situations_count']}")
        print(f"  Current progress: {summary['current_progress_percentage']}%")
        print(f"  Total invoiced: {summary['total_situations_ttc']}€")
        print(f"  Remaining: {summary['remaining_ttc']}€")
        
        return summary
    
    def test_list_situations_after_creation(self, auth_headers, test_quote):
        """Verify situations list returns created situations"""
        response = requests.get(
            f"{BASE_URL}/api/quotes/{test_quote['id']}/situations",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        situations = response.json()
        assert len(situations) >= 1, "Expected at least 1 situation"
        
        # Validate structure of each situation
        for sit in situations:
            assert "id" in sit
            assert "invoice_number" in sit
            assert "situation_number" in sit
            assert "situation_type" in sit
            assert "current_percentage" in sit
            assert "previous_percentage" in sit
            assert "situation_percentage" in sit
            assert "total_ht" in sit
            assert "total_vat" in sit
            assert "total_ttc" in sit
            assert "payment_status" in sit
            assert "chantier_ref" in sit
        
        print(f"✓ Found {len(situations)} situation(s):")
        for sit in situations:
            print(f"  - {sit['invoice_number']}: {sit['situation_type']}, {sit['current_percentage']}% cumul, {sit['total_ttc']}€ TTC")
        
        return situations


class TestSituationValidation:
    """Test validation rules for situations"""
    
    def test_situation_percentage_must_increase(self, auth_headers, test_quote):
        """Test that new situation percentage must be greater than previous cumulative"""
        # Get current progress
        summary_response = requests.get(
            f"{BASE_URL}/api/quotes/{test_quote['id']}/situations/summary",
            headers=auth_headers
        )
        summary = summary_response.json()
        current_progress = summary["current_progress_percentage"]
        
        if current_progress == 0:
            pytest.skip("No previous situations to test against")
        
        # Try to create situation with percentage <= current progress
        situation_data = {
            "quote_id": test_quote["id"],
            "situation_type": "global",
            "global_percentage": current_progress - 5,  # Less than current
            "notes": "Should fail"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/quotes/{test_quote['id']}/situation",
            headers=auth_headers,
            json=situation_data
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert "supérieur" in response.json()["detail"].lower() or "cumul" in response.json()["detail"].lower()
        
        print(f"✓ Correctly rejected situation with percentage <= current progress ({current_progress}%)")
    
    def test_situation_percentage_max_100(self, auth_headers, test_quote):
        """Test that situation percentage cannot exceed 100%"""
        situation_data = {
            "quote_id": test_quote["id"],
            "situation_type": "global",
            "global_percentage": 150,  # Over 100%
            "notes": "Should fail"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/quotes/{test_quote['id']}/situation",
            headers=auth_headers,
            json=situation_data
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert "100" in response.json()["detail"] or "dépasser" in response.json()["detail"].lower()
        
        print("✓ Correctly rejected situation with percentage > 100%")
    
    def test_situation_requires_accepte_status(self, auth_headers):
        """Test that situation creation requires quote in accepte/envoye status"""
        # Get a client
        clients_response = requests.get(f"{BASE_URL}/api/clients", headers=auth_headers)
        clients = clients_response.json()
        if not clients:
            pytest.skip("No clients available")
        
        # Create a draft quote
        quote_data = {
            "client_id": clients[0]["id"],
            "validity_days": 30,
            "items": [{"description": "Test", "quantity": 1, "unit_price": 100, "vat_rate": 20}],
            "notes": "Draft quote for validation test"
        }
        quote_response = requests.post(f"{BASE_URL}/api/quotes", headers=auth_headers, json=quote_data)
        draft_quote = quote_response.json()
        
        # Try to create situation on draft quote
        situation_data = {
            "quote_id": draft_quote["id"],
            "situation_type": "global",
            "global_percentage": 30,
            "notes": "Should fail"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/quotes/{draft_quote['id']}/situation",
            headers=auth_headers,
            json=situation_data
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert "accepté" in response.json()["detail"].lower() or "envoyé" in response.json()["detail"].lower()
        
        print("✓ Correctly rejected situation for draft quote")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/quotes/{draft_quote['id']}", headers=auth_headers)
    
    def test_per_line_requires_line_items(self, auth_headers, test_quote):
        """Test that per_line mode requires line_items"""
        situation_data = {
            "quote_id": test_quote["id"],
            "situation_type": "per_line",
            "line_items": [],  # Empty
            "notes": "Should fail"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/quotes/{test_quote['id']}/situation",
            headers=auth_headers,
            json=situation_data
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        
        print("✓ Correctly rejected per_line situation without line_items")
    
    def test_global_requires_percentage(self, auth_headers, test_quote):
        """Test that global mode requires global_percentage"""
        situation_data = {
            "quote_id": test_quote["id"],
            "situation_type": "global",
            # Missing global_percentage
            "notes": "Should fail"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/quotes/{test_quote['id']}/situation",
            headers=auth_headers,
            json=situation_data
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        
        print("✓ Correctly rejected global situation without percentage")


class TestSituationFinalInvoice:
    """Test final invoice (décompte final) creation after situations"""
    
    def test_create_situation_final_invoice(self, auth_headers, test_quote):
        """Test POST /api/quotes/{id}/situation/final-invoice endpoint"""
        # First ensure we have at least one situation
        summary_response = requests.get(
            f"{BASE_URL}/api/quotes/{test_quote['id']}/situations/summary",
            headers=auth_headers
        )
        summary = summary_response.json()
        
        if summary["situations_count"] == 0:
            # Create a situation first
            situation_data = {
                "quote_id": test_quote["id"],
                "situation_type": "global",
                "global_percentage": 50,
                "notes": "Situation for final invoice test"
            }
            requests.post(
                f"{BASE_URL}/api/quotes/{test_quote['id']}/situation",
                headers=auth_headers,
                json=situation_data
            )
        
        # Create final invoice
        response = requests.post(
            f"{BASE_URL}/api/quotes/{test_quote['id']}/situation/final-invoice",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to create final invoice: {response.text}"
        
        invoice = response.json()
        
        # Validate response
        assert "id" in invoice
        assert "invoice_number" in invoice
        assert invoice["invoice_number"].startswith("FAC-")
        assert "total_ht" in invoice
        assert "total_vat" in invoice
        assert "total_ttc" in invoice
        
        print(f"✓ Created final invoice {invoice['invoice_number']}")
        print(f"  Total TTC: {invoice['total_ttc']}€")
        
        return invoice
    
    def test_final_invoice_requires_situations(self, auth_headers):
        """Test that final invoice requires at least one situation"""
        # Create a new quote without situations
        clients_response = requests.get(f"{BASE_URL}/api/clients", headers=auth_headers)
        clients = clients_response.json()
        if not clients:
            pytest.skip("No clients available")
        
        quote_data = {
            "client_id": clients[0]["id"],
            "validity_days": 30,
            "items": [{"description": "Test", "quantity": 1, "unit_price": 100, "vat_rate": 20}],
            "notes": "Quote without situations"
        }
        quote_response = requests.post(f"{BASE_URL}/api/quotes", headers=auth_headers, json=quote_data)
        quote = quote_response.json()
        
        # Update to accepte
        requests.put(
            f"{BASE_URL}/api/quotes/{quote['id']}",
            headers=auth_headers,
            json={"status": "accepte"}
        )
        
        # Try to create final invoice without situations
        response = requests.post(
            f"{BASE_URL}/api/quotes/{quote['id']}/situation/final-invoice",
            headers=auth_headers
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert "situation" in response.json()["detail"].lower()
        
        print("✓ Correctly rejected final invoice without situations")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/quotes/{quote['id']}", headers=auth_headers)


class TestSituationEdgeCases:
    """Test edge cases for situations"""
    
    def test_situation_nonexistent_quote(self, auth_headers):
        """Test situation endpoints for non-existent quote return 404"""
        fake_quote_id = "00000000-0000-0000-0000-000000000000"
        
        response = requests.get(
            f"{BASE_URL}/api/quotes/{fake_quote_id}/situations/summary",
            headers=auth_headers
        )
        assert response.status_code == 404
        print("✓ Correctly returned 404 for non-existent quote")
    
    def test_situation_requires_auth(self):
        """Test that situation endpoints require authentication"""
        response = requests.get(
            f"{BASE_URL}/api/quotes/{KNOWN_QUOTE_ID}/situations/summary"
        )
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Situation endpoints correctly require authentication")
    
    def test_situation_appears_in_invoices_list(self, auth_headers, test_quote):
        """Verify situation invoices appear in the invoices list with is_situation flag"""
        response = requests.get(
            f"{BASE_URL}/api/invoices",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        invoices = response.json()
        situation_invoices = [inv for inv in invoices if inv.get("is_situation") == True]
        
        print(f"✓ Found {len(situation_invoices)} situation invoice(s) in invoices list")
        for inv in situation_invoices:
            print(f"  - {inv['invoice_number']}: {inv['total_ttc']}€ TTC (situation #{inv.get('situation_number')})")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
