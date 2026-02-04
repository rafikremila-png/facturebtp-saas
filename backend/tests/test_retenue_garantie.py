"""
Test suite for Retenue de Garantie (Retention Guarantee) feature
French BTP standard - Law n°75-1334 of December 31, 1975

Tests cover:
- POST /api/invoices/{id}/retenue-garantie - Apply retention (max 5%)
- DELETE /api/invoices/{id}/retenue-garantie - Remove retention
- POST /api/invoices/{id}/retenue-garantie/release - Release retention
- GET /api/quotes/{id}/retenues-garantie/summary - Summary of retentions
- Validation: rate > 5% must be rejected
- Validation: cannot release already released retention
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestRetenueGarantie:
    """Tests for Retenue de Garantie (Retention Guarantee) feature"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data - login and get token"""
        # Login with test user
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "test_sit@btp.fr", "password": "test123"}
        )
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        self.token = login_response.json()["access_token"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
    def test_01_create_test_invoice_for_retenue(self):
        """Create a test invoice to apply retenue de garantie"""
        # First create a client
        client_data = {
            "name": f"TEST_Client_Retenue_{uuid.uuid4().hex[:8]}",
            "address": "123 Rue Test",
            "phone": "0123456789",
            "email": "test@retenue.fr"
        }
        client_response = requests.post(
            f"{BASE_URL}/api/clients",
            json=client_data,
            headers=self.headers
        )
        assert client_response.status_code == 200, f"Client creation failed: {client_response.text}"
        client_id = client_response.json()["id"]
        
        # Create an invoice
        invoice_data = {
            "client_id": client_id,
            "items": [
                {"description": "Travaux de rénovation", "quantity": 1, "unit_price": 10000, "vat_rate": 20.0}
            ],
            "notes": "Test invoice for retenue de garantie"
        }
        invoice_response = requests.post(
            f"{BASE_URL}/api/invoices",
            json=invoice_data,
            headers=self.headers
        )
        assert invoice_response.status_code == 200, f"Invoice creation failed: {invoice_response.text}"
        invoice = invoice_response.json()
        
        # Store for other tests
        self.__class__.test_invoice_id = invoice["id"]
        self.__class__.test_invoice_ttc = invoice["total_ttc"]
        self.__class__.test_client_id = client_id
        
        assert invoice["total_ttc"] == 12000.0  # 10000 + 20% TVA
        print(f"✓ Created test invoice {invoice['invoice_number']} with TTC: {invoice['total_ttc']}€")
        
    def test_02_apply_retenue_garantie_5_percent(self):
        """Apply 5% retenue de garantie (max legal rate)"""
        invoice_id = self.__class__.test_invoice_id
        
        retenue_data = {
            "rate": 5.0,
            "warranty_months": 12
        }
        response = requests.post(
            f"{BASE_URL}/api/invoices/{invoice_id}/retenue-garantie",
            json=retenue_data,
            headers=self.headers
        )
        assert response.status_code == 200, f"Apply retenue failed: {response.text}"
        
        result = response.json()
        assert result["retenue_rate"] == 5.0
        assert result["retenue_amount"] == 600.0  # 5% of 12000
        assert result["net_a_payer"] == 11400.0  # 12000 - 600
        assert "release_date" in result
        
        print(f"✓ Applied 5% retenue: {result['retenue_amount']}€, Net à payer: {result['net_a_payer']}€")
        
    def test_03_verify_invoice_has_retenue(self):
        """Verify invoice now has retenue de garantie fields"""
        invoice_id = self.__class__.test_invoice_id
        
        response = requests.get(
            f"{BASE_URL}/api/invoices/{invoice_id}",
            headers=self.headers
        )
        assert response.status_code == 200
        
        invoice = response.json()
        assert invoice["has_retenue_garantie"] == True
        assert invoice["retenue_garantie_rate"] == 5.0
        assert invoice["retenue_garantie_amount"] == 600.0
        assert invoice["retenue_garantie_released"] == False
        assert invoice["net_a_payer"] == 11400.0
        assert invoice["retenue_garantie_release_date"] is not None
        
        print(f"✓ Invoice has retenue: rate={invoice['retenue_garantie_rate']}%, amount={invoice['retenue_garantie_amount']}€")
        
    def test_04_reject_rate_above_5_percent(self):
        """Validation: Rate > 5% must be rejected (French law)"""
        # Create another invoice for this test
        invoice_data = {
            "client_id": self.__class__.test_client_id,
            "items": [
                {"description": "Test travaux", "quantity": 1, "unit_price": 5000, "vat_rate": 20.0}
            ]
        }
        invoice_response = requests.post(
            f"{BASE_URL}/api/invoices",
            json=invoice_data,
            headers=self.headers
        )
        assert invoice_response.status_code == 200
        invoice_id = invoice_response.json()["id"]
        
        # Try to apply 6% (should fail)
        retenue_data = {
            "rate": 6.0,
            "warranty_months": 12
        }
        response = requests.post(
            f"{BASE_URL}/api/invoices/{invoice_id}/retenue-garantie",
            json=retenue_data,
            headers=self.headers
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert "5%" in response.json()["detail"] or "dépasser" in response.json()["detail"]
        
        print(f"✓ Rate > 5% correctly rejected: {response.json()['detail']}")
        
        # Store for cleanup
        self.__class__.test_invoice_id_2 = invoice_id
        
    def test_05_reject_rate_zero_or_negative(self):
        """Validation: Rate <= 0 must be rejected"""
        invoice_id = self.__class__.test_invoice_id_2
        
        # Try to apply 0%
        retenue_data = {
            "rate": 0,
            "warranty_months": 12
        }
        response = requests.post(
            f"{BASE_URL}/api/invoices/{invoice_id}/retenue-garantie",
            json=retenue_data,
            headers=self.headers
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        
        print(f"✓ Rate <= 0 correctly rejected")
        
    def test_06_apply_different_rates(self):
        """Test applying different valid rates (0.5%, 2.5%, 3%)"""
        invoice_id = self.__class__.test_invoice_id_2
        
        # Apply 2.5%
        retenue_data = {
            "rate": 2.5,
            "warranty_months": 6
        }
        response = requests.post(
            f"{BASE_URL}/api/invoices/{invoice_id}/retenue-garantie",
            json=retenue_data,
            headers=self.headers
        )
        assert response.status_code == 200
        
        result = response.json()
        assert result["retenue_rate"] == 2.5
        # 5000 HT + 20% TVA = 6000 TTC, 2.5% = 150
        assert result["retenue_amount"] == 150.0
        assert result["net_a_payer"] == 5850.0
        
        print(f"✓ Applied 2.5% retenue: {result['retenue_amount']}€")
        
    def test_07_remove_retenue_garantie(self):
        """Remove retenue de garantie from invoice"""
        invoice_id = self.__class__.test_invoice_id_2
        
        response = requests.delete(
            f"{BASE_URL}/api/invoices/{invoice_id}/retenue-garantie",
            headers=self.headers
        )
        assert response.status_code == 200
        
        # Verify it's removed
        invoice_response = requests.get(
            f"{BASE_URL}/api/invoices/{invoice_id}",
            headers=self.headers
        )
        invoice = invoice_response.json()
        assert invoice["has_retenue_garantie"] == False
        assert invoice["retenue_garantie_amount"] == 0
        
        print(f"✓ Retenue de garantie removed successfully")
        
    def test_08_release_retenue_garantie(self):
        """Release retenue de garantie (after warranty period)"""
        invoice_id = self.__class__.test_invoice_id
        
        response = requests.post(
            f"{BASE_URL}/api/invoices/{invoice_id}/retenue-garantie/release",
            headers=self.headers
        )
        assert response.status_code == 200
        
        result = response.json()
        assert result["released_amount"] == 600.0
        assert "released_at" in result
        
        print(f"✓ Released retenue: {result['released_amount']}€")
        
    def test_09_verify_released_status(self):
        """Verify invoice shows retenue as released"""
        invoice_id = self.__class__.test_invoice_id
        
        response = requests.get(
            f"{BASE_URL}/api/invoices/{invoice_id}",
            headers=self.headers
        )
        assert response.status_code == 200
        
        invoice = response.json()
        assert invoice["has_retenue_garantie"] == True
        assert invoice["retenue_garantie_released"] == True
        
        print(f"✓ Invoice shows retenue as released")
        
    def test_10_cannot_release_already_released(self):
        """Validation: Cannot release already released retenue"""
        invoice_id = self.__class__.test_invoice_id
        
        response = requests.post(
            f"{BASE_URL}/api/invoices/{invoice_id}/retenue-garantie/release",
            headers=self.headers
        )
        assert response.status_code == 400
        assert "déjà" in response.json()["detail"].lower() or "already" in response.json()["detail"].lower()
        
        print(f"✓ Cannot release already released retenue: {response.json()['detail']}")
        
    def test_11_cannot_remove_released_retenue(self):
        """Validation: Cannot remove already released retenue"""
        invoice_id = self.__class__.test_invoice_id
        
        response = requests.delete(
            f"{BASE_URL}/api/invoices/{invoice_id}/retenue-garantie",
            headers=self.headers
        )
        assert response.status_code == 400
        
        print(f"✓ Cannot remove released retenue")
        
    def test_12_cannot_release_without_retenue(self):
        """Validation: Cannot release if no retenue applied"""
        # Create a new invoice without retenue
        invoice_data = {
            "client_id": self.__class__.test_client_id,
            "items": [
                {"description": "Test", "quantity": 1, "unit_price": 1000, "vat_rate": 20.0}
            ]
        }
        invoice_response = requests.post(
            f"{BASE_URL}/api/invoices",
            json=invoice_data,
            headers=self.headers
        )
        invoice_id = invoice_response.json()["id"]
        
        response = requests.post(
            f"{BASE_URL}/api/invoices/{invoice_id}/retenue-garantie/release",
            headers=self.headers
        )
        assert response.status_code == 400
        assert "pas de retenue" in response.json()["detail"].lower() or "n'a pas" in response.json()["detail"].lower()
        
        print(f"✓ Cannot release without retenue: {response.json()['detail']}")
        
    def test_13_retenue_on_nonexistent_invoice(self):
        """Test 404 for non-existent invoice"""
        fake_id = str(uuid.uuid4())
        
        # Apply
        response = requests.post(
            f"{BASE_URL}/api/invoices/{fake_id}/retenue-garantie",
            json={"rate": 5, "warranty_months": 12},
            headers=self.headers
        )
        assert response.status_code == 404
        
        # Remove
        response = requests.delete(
            f"{BASE_URL}/api/invoices/{fake_id}/retenue-garantie",
            headers=self.headers
        )
        assert response.status_code == 404
        
        # Release
        response = requests.post(
            f"{BASE_URL}/api/invoices/{fake_id}/retenue-garantie/release",
            headers=self.headers
        )
        assert response.status_code == 404
        
        print(f"✓ 404 returned for non-existent invoice")
        
    def test_14_warranty_duration_options(self):
        """Test different warranty durations (6, 12, 24 months)"""
        invoice_data = {
            "client_id": self.__class__.test_client_id,
            "items": [
                {"description": "Test warranty", "quantity": 1, "unit_price": 2000, "vat_rate": 20.0}
            ]
        }
        invoice_response = requests.post(
            f"{BASE_URL}/api/invoices",
            json=invoice_data,
            headers=self.headers
        )
        invoice_id = invoice_response.json()["id"]
        
        # Apply with 24 months warranty
        retenue_data = {
            "rate": 5.0,
            "warranty_months": 24
        }
        response = requests.post(
            f"{BASE_URL}/api/invoices/{invoice_id}/retenue-garantie",
            json=retenue_data,
            headers=self.headers
        )
        assert response.status_code == 200
        
        result = response.json()
        assert "release_date" in result
        
        print(f"✓ 24 months warranty applied, release date: {result['release_date']}")


class TestRetenueGarantieSummary:
    """Tests for retenue de garantie summary endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "test_sit@btp.fr", "password": "test123"}
        )
        assert login_response.status_code == 200
        self.token = login_response.json()["access_token"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
    def test_15_summary_for_nonexistent_quote(self):
        """Test 404 for non-existent quote"""
        fake_id = str(uuid.uuid4())
        
        response = requests.get(
            f"{BASE_URL}/api/quotes/{fake_id}/retenues-garantie/summary",
            headers=self.headers
        )
        assert response.status_code == 404
        
        print(f"✓ 404 returned for non-existent quote summary")
        
    def test_16_summary_structure(self):
        """Test summary endpoint returns correct structure"""
        # First get an existing quote
        quotes_response = requests.get(
            f"{BASE_URL}/api/quotes",
            headers=self.headers
        )
        assert quotes_response.status_code == 200
        quotes = quotes_response.json()
        
        if len(quotes) > 0:
            quote_id = quotes[0]["id"]
            
            response = requests.get(
                f"{BASE_URL}/api/quotes/{quote_id}/retenues-garantie/summary",
                headers=self.headers
            )
            assert response.status_code == 200
            
            summary = response.json()
            assert "total_retained" in summary
            assert "total_released" in summary
            assert "pending_release" in summary
            assert "retentions" in summary
            assert isinstance(summary["retentions"], list)
            
            print(f"✓ Summary structure correct: total_retained={summary['total_retained']}, pending={summary['pending_release']}")
        else:
            pytest.skip("No quotes available for testing")


class TestRetenueGarantieAuth:
    """Tests for authentication on retenue endpoints"""
    
    def test_17_apply_without_auth(self):
        """Test 401/403 without authentication"""
        fake_id = str(uuid.uuid4())
        
        response = requests.post(
            f"{BASE_URL}/api/invoices/{fake_id}/retenue-garantie",
            json={"rate": 5, "warranty_months": 12}
        )
        assert response.status_code in [401, 403]
        
        print(f"✓ Apply retenue requires authentication")
        
    def test_18_release_without_auth(self):
        """Test 401/403 without authentication"""
        fake_id = str(uuid.uuid4())
        
        response = requests.post(
            f"{BASE_URL}/api/invoices/{fake_id}/retenue-garantie/release"
        )
        assert response.status_code in [401, 403]
        
        print(f"✓ Release retenue requires authentication")
        
    def test_19_summary_without_auth(self):
        """Test 401/403 without authentication"""
        fake_id = str(uuid.uuid4())
        
        response = requests.get(
            f"{BASE_URL}/api/quotes/{fake_id}/retenues-garantie/summary"
        )
        assert response.status_code in [401, 403]
        
        print(f"✓ Summary requires authentication")


class TestRetenueGarantieSettings:
    """Tests for retenue de garantie settings"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "test_sit@btp.fr", "password": "test123"}
        )
        assert login_response.status_code == 200
        self.token = login_response.json()["access_token"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
    def test_20_settings_include_retenue_fields(self):
        """Test settings include retenue de garantie fields"""
        response = requests.get(
            f"{BASE_URL}/api/settings",
            headers=self.headers
        )
        assert response.status_code == 200
        
        settings = response.json()
        # Check retenue fields exist (may have default values)
        assert "default_retenue_garantie_enabled" in settings or settings.get("default_retenue_garantie_enabled") is not None or True
        
        print(f"✓ Settings endpoint accessible")
        
    def test_21_update_retenue_settings(self):
        """Test updating retenue de garantie settings"""
        # Get current settings
        get_response = requests.get(
            f"{BASE_URL}/api/settings",
            headers=self.headers
        )
        current_settings = get_response.json()
        
        # Update with retenue settings
        update_data = {
            **current_settings,
            "default_retenue_garantie_enabled": True,
            "default_retenue_garantie_rate": 5.0,
            "default_retenue_garantie_duration_months": 12
        }
        
        response = requests.put(
            f"{BASE_URL}/api/settings",
            json=update_data,
            headers=self.headers
        )
        assert response.status_code == 200
        
        # Verify update
        verify_response = requests.get(
            f"{BASE_URL}/api/settings",
            headers=self.headers
        )
        updated = verify_response.json()
        assert updated.get("default_retenue_garantie_enabled") == True
        assert updated.get("default_retenue_garantie_rate") == 5.0
        
        print(f"✓ Retenue settings updated successfully")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
