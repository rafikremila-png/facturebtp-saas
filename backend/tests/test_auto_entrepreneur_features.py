"""
Test suite for new BTP Invoice features:
1. Auto-entrepreneur mode (TVA non applicable)
2. Extended legal fields (RCS, Code APE, Capital social, IBAN/BIC)
3. Configurable payment delay with legal mentions on invoices
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@btp.fr"
TEST_PASSWORD = "Test123!"


class TestAuthAndSetup:
    """Authentication and setup tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        # Try to register if login fails
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "name": "Test User BTP"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed - skipping authenticated tests")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data


class TestCompanySettingsNewFields:
    """Test new company settings fields: RCS, Code APE, Capital, IBAN, BIC, auto-entrepreneur, payment delay"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_get_settings_has_new_fields(self, auth_headers):
        """Test that GET /api/settings returns all new fields"""
        response = requests.get(f"{BASE_URL}/api/settings", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Check new legal fields exist
        assert "rcs_rm" in data, "Missing rcs_rm field"
        assert "code_ape" in data, "Missing code_ape field"
        assert "capital_social" in data, "Missing capital_social field"
        
        # Check bank fields exist
        assert "iban" in data, "Missing iban field"
        assert "bic" in data, "Missing bic field"
        
        # Check auto-entrepreneur fields exist
        assert "is_auto_entrepreneur" in data, "Missing is_auto_entrepreneur field"
        assert "auto_entrepreneur_mention" in data, "Missing auto_entrepreneur_mention field"
        
        # Check payment delay fields exist
        assert "default_payment_delay_days" in data, "Missing default_payment_delay_days field"
        assert "late_payment_rate" in data, "Missing late_payment_rate field"
    
    def test_update_legal_fields(self, auth_headers):
        """Test updating RCS, Code APE, Capital social"""
        settings_update = {
            "company_name": "Test BTP SARL",
            "address": "123 Rue du Test, 75001 Paris",
            "phone": "01 23 45 67 89",
            "email": "contact@testbtp.fr",
            "siret": "12345678901234",
            "vat_number": "FR12345678901",
            "rcs_rm": "RCS Paris B 123 456 789",
            "code_ape": "4120A",
            "capital_social": "10 000 €",
            "default_vat_rates": [20.0, 10.0, 5.5, 2.1],
            "is_auto_entrepreneur": False,
            "auto_entrepreneur_mention": "TVA non applicable, art. 293B du CGI",
            "default_payment_delay_days": 30,
            "late_payment_rate": 3.0,
            "iban": "",
            "bic": ""
        }
        
        response = requests.put(f"{BASE_URL}/api/settings", headers=auth_headers, json=settings_update)
        assert response.status_code == 200
        data = response.json()
        
        # Verify legal fields were saved
        assert data["rcs_rm"] == "RCS Paris B 123 456 789"
        assert data["code_ape"] == "4120A"
        assert data["capital_social"] == "10 000 €"
    
    def test_update_bank_fields(self, auth_headers):
        """Test updating IBAN and BIC"""
        # First get current settings
        response = requests.get(f"{BASE_URL}/api/settings", headers=auth_headers)
        current_settings = response.json()
        
        # Update with bank info
        current_settings["iban"] = "FR76 1234 5678 9012 3456 7890 123"
        current_settings["bic"] = "BNPAFRPP"
        
        response = requests.put(f"{BASE_URL}/api/settings", headers=auth_headers, json=current_settings)
        assert response.status_code == 200
        data = response.json()
        
        # Verify bank fields were saved
        assert data["iban"] == "FR76 1234 5678 9012 3456 7890 123"
        assert data["bic"] == "BNPAFRPP"
    
    def test_update_payment_delay(self, auth_headers):
        """Test updating default payment delay"""
        # First get current settings
        response = requests.get(f"{BASE_URL}/api/settings", headers=auth_headers)
        current_settings = response.json()
        
        # Update payment delay to 45 days
        current_settings["default_payment_delay_days"] = 45
        
        response = requests.put(f"{BASE_URL}/api/settings", headers=auth_headers, json=current_settings)
        assert response.status_code == 200
        data = response.json()
        
        assert data["default_payment_delay_days"] == 45
        
        # Reset to 30 days
        current_settings["default_payment_delay_days"] = 30
        requests.put(f"{BASE_URL}/api/settings", headers=auth_headers, json=current_settings)


class TestAutoEntrepreneurMode:
    """Test auto-entrepreneur mode functionality"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    @pytest.fixture(scope="class")
    def test_client(self, auth_headers):
        """Create a test client for quotes/invoices"""
        client_data = {
            "name": "TEST_AutoEntrepreneur_Client",
            "address": "456 Avenue Test",
            "phone": "06 12 34 56 78",
            "email": "client@test.fr"
        }
        response = requests.post(f"{BASE_URL}/api/clients", headers=auth_headers, json=client_data)
        if response.status_code == 200:
            return response.json()
        # Try to find existing client
        response = requests.get(f"{BASE_URL}/api/clients", headers=auth_headers)
        clients = response.json()
        for c in clients:
            if c["name"] == "TEST_AutoEntrepreneur_Client":
                return c
        pytest.skip("Could not create test client")
    
    def test_enable_auto_entrepreneur_mode(self, auth_headers):
        """Test enabling auto-entrepreneur mode"""
        # Get current settings
        response = requests.get(f"{BASE_URL}/api/settings", headers=auth_headers)
        current_settings = response.json()
        
        # Enable auto-entrepreneur mode
        current_settings["is_auto_entrepreneur"] = True
        current_settings["auto_entrepreneur_mention"] = "TVA non applicable, art. 293B du CGI"
        
        response = requests.put(f"{BASE_URL}/api/settings", headers=auth_headers, json=current_settings)
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_auto_entrepreneur"] == True
        assert data["auto_entrepreneur_mention"] == "TVA non applicable, art. 293B du CGI"
    
    def test_invoice_creation_auto_entrepreneur_no_vat(self, auth_headers, test_client):
        """Test that invoices created in auto-entrepreneur mode have no VAT"""
        # First ensure auto-entrepreneur mode is enabled
        response = requests.get(f"{BASE_URL}/api/settings", headers=auth_headers)
        settings = response.json()
        settings["is_auto_entrepreneur"] = True
        requests.put(f"{BASE_URL}/api/settings", headers=auth_headers, json=settings)
        
        # Create an invoice
        invoice_data = {
            "client_id": test_client["id"],
            "items": [
                {"description": "Service test auto-entrepreneur", "quantity": 2, "unit_price": 100.0, "vat_rate": 20.0}
            ],
            "notes": "Test auto-entrepreneur invoice"
        }
        
        response = requests.post(f"{BASE_URL}/api/invoices", headers=auth_headers, json=invoice_data)
        assert response.status_code == 200
        data = response.json()
        
        # In auto-entrepreneur mode, VAT should be 0
        assert data["total_vat"] == 0.0, f"Expected total_vat=0, got {data['total_vat']}"
        assert data["total_ht"] == 200.0, f"Expected total_ht=200, got {data['total_ht']}"
        assert data["total_ttc"] == 200.0, f"Expected total_ttc=200 (same as HT), got {data['total_ttc']}"
        
        # Clean up - delete the invoice
        requests.delete(f"{BASE_URL}/api/invoices/{data['id']}", headers=auth_headers)
    
    def test_disable_auto_entrepreneur_mode(self, auth_headers):
        """Test disabling auto-entrepreneur mode"""
        # Get current settings
        response = requests.get(f"{BASE_URL}/api/settings", headers=auth_headers)
        current_settings = response.json()
        
        # Disable auto-entrepreneur mode
        current_settings["is_auto_entrepreneur"] = False
        
        response = requests.put(f"{BASE_URL}/api/settings", headers=auth_headers, json=current_settings)
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_auto_entrepreneur"] == False
    
    def test_invoice_creation_normal_mode_with_vat(self, auth_headers, test_client):
        """Test that invoices created in normal mode have VAT"""
        # Ensure auto-entrepreneur mode is disabled
        response = requests.get(f"{BASE_URL}/api/settings", headers=auth_headers)
        settings = response.json()
        settings["is_auto_entrepreneur"] = False
        requests.put(f"{BASE_URL}/api/settings", headers=auth_headers, json=settings)
        
        # Create an invoice
        invoice_data = {
            "client_id": test_client["id"],
            "items": [
                {"description": "Service test normal mode", "quantity": 2, "unit_price": 100.0, "vat_rate": 20.0}
            ],
            "notes": "Test normal mode invoice"
        }
        
        response = requests.post(f"{BASE_URL}/api/invoices", headers=auth_headers, json=invoice_data)
        assert response.status_code == 200
        data = response.json()
        
        # In normal mode, VAT should be calculated
        assert data["total_ht"] == 200.0
        assert data["total_vat"] == 40.0, f"Expected total_vat=40, got {data['total_vat']}"
        assert data["total_ttc"] == 240.0, f"Expected total_ttc=240, got {data['total_ttc']}"
        
        # Clean up - delete the invoice
        requests.delete(f"{BASE_URL}/api/invoices/{data['id']}", headers=auth_headers)


class TestInvoicePaymentDueDate:
    """Test invoice payment due date calculation"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    @pytest.fixture(scope="class")
    def test_client(self, auth_headers):
        """Create a test client for invoices"""
        client_data = {
            "name": "TEST_PaymentDelay_Client",
            "address": "789 Boulevard Test",
            "phone": "06 98 76 54 32",
            "email": "payment@test.fr"
        }
        response = requests.post(f"{BASE_URL}/api/clients", headers=auth_headers, json=client_data)
        if response.status_code == 200:
            return response.json()
        # Try to find existing client
        response = requests.get(f"{BASE_URL}/api/clients", headers=auth_headers)
        clients = response.json()
        for c in clients:
            if c["name"] == "TEST_PaymentDelay_Client":
                return c
        pytest.skip("Could not create test client")
    
    def test_invoice_has_payment_due_date(self, auth_headers, test_client):
        """Test that invoices have payment_due_date field"""
        # Ensure normal mode
        response = requests.get(f"{BASE_URL}/api/settings", headers=auth_headers)
        settings = response.json()
        settings["is_auto_entrepreneur"] = False
        settings["default_payment_delay_days"] = 30
        requests.put(f"{BASE_URL}/api/settings", headers=auth_headers, json=settings)
        
        # Create an invoice
        invoice_data = {
            "client_id": test_client["id"],
            "items": [
                {"description": "Service test payment due", "quantity": 1, "unit_price": 500.0, "vat_rate": 20.0}
            ],
            "notes": "Test payment due date"
        }
        
        response = requests.post(f"{BASE_URL}/api/invoices", headers=auth_headers, json=invoice_data)
        assert response.status_code == 200
        data = response.json()
        
        # Check payment_due_date exists
        assert "payment_due_date" in data, "Missing payment_due_date field"
        assert data["payment_due_date"] is not None
        
        # Verify due date is approximately 30 days from issue date
        issue_date = datetime.fromisoformat(data["issue_date"].replace("Z", "+00:00"))
        due_date = datetime.fromisoformat(data["payment_due_date"].replace("Z", "+00:00"))
        days_diff = (due_date - issue_date).days
        
        assert 29 <= days_diff <= 31, f"Expected ~30 days difference, got {days_diff}"
        
        # Clean up
        requests.delete(f"{BASE_URL}/api/invoices/{data['id']}", headers=auth_headers)
    
    def test_invoice_custom_payment_delay(self, auth_headers, test_client):
        """Test creating invoice with custom payment delay"""
        # Create an invoice with custom 60-day payment delay
        invoice_data = {
            "client_id": test_client["id"],
            "items": [
                {"description": "Service test custom delay", "quantity": 1, "unit_price": 300.0, "vat_rate": 20.0}
            ],
            "notes": "Test custom payment delay",
            "payment_delay_days": 60
        }
        
        response = requests.post(f"{BASE_URL}/api/invoices", headers=auth_headers, json=invoice_data)
        assert response.status_code == 200
        data = response.json()
        
        # Verify due date is approximately 60 days from issue date
        issue_date = datetime.fromisoformat(data["issue_date"].replace("Z", "+00:00"))
        due_date = datetime.fromisoformat(data["payment_due_date"].replace("Z", "+00:00"))
        days_diff = (due_date - issue_date).days
        
        assert 59 <= days_diff <= 61, f"Expected ~60 days difference, got {days_diff}"
        
        # Clean up
        requests.delete(f"{BASE_URL}/api/invoices/{data['id']}", headers=auth_headers)


class TestPDFGeneration:
    """Test PDF generation with new legal fields"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_quote_pdf_endpoint_exists(self, auth_headers):
        """Test that quote PDF endpoint exists"""
        # Get a quote first
        response = requests.get(f"{BASE_URL}/api/quotes", headers=auth_headers)
        if response.status_code == 200 and len(response.json()) > 0:
            quote = response.json()[0]
            pdf_response = requests.get(f"{BASE_URL}/api/quotes/{quote['id']}/pdf", headers=auth_headers)
            assert pdf_response.status_code == 200
            assert pdf_response.headers.get("content-type") == "application/pdf"
    
    def test_invoice_pdf_endpoint_exists(self, auth_headers):
        """Test that invoice PDF endpoint exists"""
        # Get an invoice first
        response = requests.get(f"{BASE_URL}/api/invoices", headers=auth_headers)
        if response.status_code == 200 and len(response.json()) > 0:
            invoice = response.json()[0]
            pdf_response = requests.get(f"{BASE_URL}/api/invoices/{invoice['id']}/pdf", headers=auth_headers)
            assert pdf_response.status_code == 200
            assert pdf_response.headers.get("content-type") == "application/pdf"


class TestCleanup:
    """Cleanup test data"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_cleanup_test_clients(self, auth_headers):
        """Clean up test clients created during testing"""
        response = requests.get(f"{BASE_URL}/api/clients", headers=auth_headers)
        if response.status_code == 200:
            clients = response.json()
            for client in clients:
                if client["name"].startswith("TEST_"):
                    requests.delete(f"{BASE_URL}/api/clients/{client['id']}", headers=auth_headers)
        
        # Reset settings to normal mode
        response = requests.get(f"{BASE_URL}/api/settings", headers=auth_headers)
        if response.status_code == 200:
            settings = response.json()
            settings["is_auto_entrepreneur"] = False
            settings["default_payment_delay_days"] = 30
            requests.put(f"{BASE_URL}/api/settings", headers=auth_headers, json=settings)
        
        assert True  # Cleanup completed
