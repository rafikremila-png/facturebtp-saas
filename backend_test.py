import requests
import sys
import json
from datetime import datetime

class BTPInvoiceAPITester:
    def __init__(self, base_url="https://btp-invoice.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_resources = {
            'clients': [],
            'quotes': [],
            'invoices': []
        }

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                if files:
                    # Remove Content-Type for file uploads
                    headers.pop('Content-Type', None)
                    response = requests.post(url, headers=headers, files=files)
                else:
                    response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json() if response.content else {}
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_user_registration(self):
        """Test user registration"""
        timestamp = datetime.now().strftime('%H%M%S')
        user_data = {
            "email": f"test_user_{timestamp}@example.com",
            "password": "TestPass123!",
            "name": f"Test User {timestamp}"
        }
        
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data=user_data
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response['user']['id']
            print(f"   Token obtained: {self.token[:20]}...")
            return True
        return False

    def test_user_login(self):
        """Test user login with existing credentials"""
        # Try to login with the registered user
        if not self.user_id:
            return False
            
        # For this test, we'll use the token from registration
        success, _ = self.run_test(
            "Get Current User",
            "GET", 
            "auth/me",
            200
        )
        return success

    def test_dashboard(self):
        """Test dashboard stats"""
        success, response = self.run_test(
            "Dashboard Stats",
            "GET",
            "dashboard",
            200
        )
        
        if success:
            required_fields = ['total_turnover', 'unpaid_invoices_count', 'total_clients', 'total_quotes', 'total_invoices']
            for field in required_fields:
                if field not in response:
                    print(f"   Missing field: {field}")
                    return False
            print(f"   Dashboard data: {json.dumps(response, indent=2)}")
        return success

    def test_client_crud(self):
        """Test client CRUD operations"""
        # Create client
        client_data = {
            "name": "Test Client BTP",
            "address": "123 Rue du Test, 75001 Paris",
            "phone": "01 23 45 67 89",
            "email": "client@test.fr"
        }
        
        success, response = self.run_test(
            "Create Client",
            "POST",
            "clients",
            200,
            data=client_data
        )
        
        if not success:
            return False
            
        client_id = response.get('id')
        if client_id:
            self.created_resources['clients'].append(client_id)
        
        # List clients
        success, response = self.run_test(
            "List Clients",
            "GET",
            "clients",
            200
        )
        
        if not success:
            return False
            
        # Get specific client
        if client_id:
            success, _ = self.run_test(
                "Get Client",
                "GET",
                f"clients/{client_id}",
                200
            )
            
            if not success:
                return False
                
            # Update client
            update_data = {"name": "Updated Test Client BTP"}
            success, _ = self.run_test(
                "Update Client",
                "PUT",
                f"clients/{client_id}",
                200,
                data=update_data
            )
            
            return success
        
        return False

    def test_quote_crud(self):
        """Test quote CRUD operations"""
        # Need a client first
        if not self.created_resources['clients']:
            print("   No clients available for quote test")
            return False
            
        client_id = self.created_resources['clients'][0]
        
        # Create quote
        quote_data = {
            "client_id": client_id,
            "validity_days": 30,
            "items": [
                {
                    "description": "Travaux de maçonnerie",
                    "quantity": 10,
                    "unit_price": 150.0,
                    "vat_rate": 20.0
                },
                {
                    "description": "Fourniture matériaux",
                    "quantity": 1,
                    "unit_price": 500.0,
                    "vat_rate": 20.0
                }
            ],
            "notes": "Devis pour travaux BTP"
        }
        
        success, response = self.run_test(
            "Create Quote",
            "POST",
            "quotes",
            200,
            data=quote_data
        )
        
        if not success:
            return False
            
        quote_id = response.get('id')
        if quote_id:
            self.created_resources['quotes'].append(quote_id)
        
        # List quotes
        success, _ = self.run_test(
            "List Quotes",
            "GET",
            "quotes",
            200
        )
        
        if not success:
            return False
            
        # Get specific quote
        if quote_id:
            success, quote_response = self.run_test(
                "Get Quote",
                "GET",
                f"quotes/{quote_id}",
                200
            )
            
            if not success:
                return False
                
            # Update quote status to accepted
            update_data = {"status": "accepte"}
            success, _ = self.run_test(
                "Update Quote Status",
                "PUT",
                f"quotes/{quote_id}",
                200,
                data=update_data
            )
            
            if not success:
                return False
                
            # Test PDF generation
            success, _ = self.run_test(
                "Generate Quote PDF",
                "GET",
                f"quotes/{quote_id}/pdf",
                200
            )
            
            return success
        
        return False

    def test_invoice_crud(self):
        """Test invoice CRUD operations"""
        # Need a client first
        if not self.created_resources['clients']:
            print("   No clients available for invoice test")
            return False
            
        client_id = self.created_resources['clients'][0]
        
        # Create invoice
        invoice_data = {
            "client_id": client_id,
            "items": [
                {
                    "description": "Travaux réalisés",
                    "quantity": 5,
                    "unit_price": 200.0,
                    "vat_rate": 20.0
                }
            ],
            "notes": "Facture pour travaux terminés",
            "payment_method": "virement"
        }
        
        success, response = self.run_test(
            "Create Invoice",
            "POST",
            "invoices",
            200,
            data=invoice_data
        )
        
        if not success:
            return False
            
        invoice_id = response.get('id')
        if invoice_id:
            self.created_resources['invoices'].append(invoice_id)
        
        # List invoices
        success, _ = self.run_test(
            "List Invoices",
            "GET",
            "invoices",
            200
        )
        
        if not success:
            return False
            
        # Get specific invoice
        if invoice_id:
            success, invoice_response = self.run_test(
                "Get Invoice",
                "GET",
                f"invoices/{invoice_id}",
                200
            )
            
            if not success:
                return False
                
            # Update payment status
            update_data = {
                "payment_status": "paye",
                "paid_amount": invoice_response.get('total_ttc', 0)
            }
            success, _ = self.run_test(
                "Update Invoice Payment",
                "PUT",
                f"invoices/{invoice_id}",
                200,
                data=update_data
            )
            
            if not success:
                return False
                
            # Test PDF generation
            success, _ = self.run_test(
                "Generate Invoice PDF",
                "GET",
                f"invoices/{invoice_id}/pdf",
                200
            )
            
            return success
        
        return False

    def test_quote_to_invoice_conversion(self):
        """Test converting accepted quote to invoice"""
        if not self.created_resources['quotes']:
            print("   No quotes available for conversion test")
            return False
            
        quote_id = self.created_resources['quotes'][0]
        
        success, response = self.run_test(
            "Convert Quote to Invoice",
            "POST",
            f"quotes/{quote_id}/convert",
            200
        )
        
        if success and response.get('id'):
            self.created_resources['invoices'].append(response['id'])
            print(f"   Created invoice: {response.get('invoice_number')}")
        
        return success

    def test_company_settings(self):
        """Test company settings"""
        # Get current settings
        success, response = self.run_test(
            "Get Company Settings",
            "GET",
            "settings",
            200
        )
        
        if not success:
            return False
            
        # Update settings
        settings_data = {
            "company_name": "Test BTP Company",
            "address": "456 Avenue du Test, 75002 Paris",
            "phone": "01 98 76 54 32",
            "email": "contact@testbtp.fr",
            "siret": "12345678900123",
            "vat_number": "FR12345678901",
            "default_vat_rates": [20.0, 10.0, 5.5, 2.1]
        }
        
        success, _ = self.run_test(
            "Update Company Settings",
            "PUT",
            "settings",
            200,
            data=settings_data
        )
        
        return success

    def test_predefined_items_api(self):
        """Test predefined items API functionality"""
        # Get categories (should auto-initialize default items)
        success, response = self.run_test(
            "Get Predefined Categories",
            "GET",
            "predefined-items/categories",
            200
        )
        
        if not success:
            return False
            
        # Verify we have the expected 8 BTP categories
        expected_categories = [
            "Menuiserie", "Plomberie", "Électricité", "Peinture", 
            "Maçonnerie", "Carrelage", "Plâtrerie / Isolation", "Rénovation générale"
        ]
        
        categories = response
        category_names = [cat['name'] for cat in categories]
        
        for expected_cat in expected_categories:
            if expected_cat not in category_names:
                print(f"   Missing expected category: {expected_cat}")
                return False
        
        print(f"   Found {len(categories)} categories with items")
        
        # Test getting items for a specific category
        success, response = self.run_test(
            "Get Items by Category",
            "GET",
            "predefined-items?category=Menuiserie",
            200
        )
        
        if not success:
            return False
            
        # Test creating a new predefined item
        new_item_data = {
            "category": "Menuiserie",
            "description": "Test Custom Item",
            "unit": "unité",
            "default_price": 99.99,
            "default_vat_rate": 20.0
        }
        
        success, response = self.run_test(
            "Create Predefined Item",
            "POST",
            "predefined-items",
            200,
            data=new_item_data
        )
        
        if not success:
            return False
            
        created_item_id = response.get('id')
        if not created_item_id:
            print("   No item ID returned from creation")
            return False
            
        # Test updating the created item
        update_data = {
            "description": "Updated Test Custom Item",
            "default_price": 149.99
        }
        
        success, _ = self.run_test(
            "Update Predefined Item",
            "PUT",
            f"predefined-items/{created_item_id}",
            200,
            data=update_data
        )
        
        if not success:
            return False
            
        # Test deleting the created item
        success, _ = self.run_test(
            "Delete Predefined Item",
            "DELETE",
            f"predefined-items/{created_item_id}",
            200
        )
        
        if not success:
            return False
            
        # Test reset functionality (this will restore defaults)
        success, _ = self.run_test(
            "Reset Predefined Items",
            "POST",
            "predefined-items/reset",
            200
        )
        
        return success

    def cleanup_resources(self):
        """Clean up created test resources"""
        print("\n🧹 Cleaning up test resources...")
        
        # Delete invoices
        for invoice_id in self.created_resources['invoices']:
            self.run_test(
                f"Delete Invoice {invoice_id}",
                "DELETE",
                f"invoices/{invoice_id}",
                200
            )
        
        # Delete quotes
        for quote_id in self.created_resources['quotes']:
            self.run_test(
                f"Delete Quote {quote_id}",
                "DELETE",
                f"quotes/{quote_id}",
                200
            )
        
        # Delete clients
        for client_id in self.created_resources['clients']:
            self.run_test(
                f"Delete Client {client_id}",
                "DELETE",
                f"clients/{client_id}",
                200
            )

def main():
    print("🚀 Starting BTP Invoice Management API Tests")
    print("=" * 50)
    
    tester = BTPInvoiceAPITester()
    
    # Test sequence
    test_results = []
    
    # Authentication tests
    if tester.test_user_registration():
        test_results.append("✅ User Registration")
        if tester.test_user_login():
            test_results.append("✅ User Authentication")
        else:
            test_results.append("❌ User Authentication")
    else:
        test_results.append("❌ User Registration")
        print("❌ Cannot proceed without authentication")
        return 1
    
    # Dashboard test
    if tester.test_dashboard():
        test_results.append("✅ Dashboard Stats")
    else:
        test_results.append("❌ Dashboard Stats")
    
    # CRUD tests
    if tester.test_client_crud():
        test_results.append("✅ Client CRUD")
    else:
        test_results.append("❌ Client CRUD")
    
    if tester.test_quote_crud():
        test_results.append("✅ Quote CRUD")
    else:
        test_results.append("❌ Quote CRUD")
    
    if tester.test_invoice_crud():
        test_results.append("✅ Invoice CRUD")
    else:
        test_results.append("❌ Invoice CRUD")
    
    # Conversion test
    if tester.test_quote_to_invoice_conversion():
        test_results.append("✅ Quote to Invoice Conversion")
    else:
        test_results.append("❌ Quote to Invoice Conversion")
    
    # Settings test
    if tester.test_company_settings():
        test_results.append("✅ Company Settings")
    else:
        test_results.append("❌ Company Settings")
    
    # Predefined items test
    if tester.test_predefined_items_api():
        test_results.append("✅ Predefined Items API")
    else:
        test_results.append("❌ Predefined Items API")
    
    # Cleanup
    tester.cleanup_resources()
    
    # Print results
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    for result in test_results:
        print(result)
    
    print(f"\n📈 Overall: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    success_rate = (tester.tests_passed / tester.tests_run) * 100 if tester.tests_run > 0 else 0
    print(f"🎯 Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("🎉 Backend API tests PASSED!")
        return 0
    else:
        print("⚠️  Backend API tests have issues")
        return 1

if __name__ == "__main__":
    sys.exit(main())