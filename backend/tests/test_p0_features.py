"""
Test P0 Features: Profile Completion, Work Library, Projects
Tests for FactureBTP SaaS platform new features
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@btpfacture.com"
ADMIN_PASSWORD = "Admin123!"


class TestAuthentication:
    """Authentication tests - required for other tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        return data["access_token"]
    
    def test_login_success(self):
        """Test admin login works"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == ADMIN_EMAIL


class TestProfileCompletion:
    """Profile completion API tests"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_profile_completion_endpoint(self, auth_headers):
        """Test GET /api/profile/completion returns correct structure"""
        response = requests.get(f"{BASE_URL}/api/profile/completion", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        # Verify required fields
        assert "completion_percentage" in data
        assert "completed_count" in data
        assert "total_count" in data
        assert "items" in data
        assert "summary" in data
        
        # Verify percentage is valid
        assert 0 <= data["completion_percentage"] <= 100
        
        # Verify items structure
        assert isinstance(data["items"], list)
        if len(data["items"]) > 0:
            item = data["items"][0]
            assert "key" in item
            assert "label" in item
            assert "completed" in item
            assert "category" in item
    
    def test_profile_completion_categories(self, auth_headers):
        """Test profile completion has all 4 categories"""
        response = requests.get(f"{BASE_URL}/api/profile/completion", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        summary = data["summary"]
        
        # Verify all 4 categories exist
        expected_categories = ["profil", "entreprise", "legal", "bancaire"]
        for cat in expected_categories:
            assert cat in summary, f"Missing category: {cat}"
            assert f"{cat}_total" in summary, f"Missing {cat}_total"
    
    def test_profile_completion_items_count(self, auth_headers):
        """Test profile completion has expected number of items"""
        response = requests.get(f"{BASE_URL}/api/profile/completion", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        # Should have 11 items based on code review
        assert data["total_count"] == 11, f"Expected 11 items, got {data['total_count']}"


class TestWorkItemsAPI:
    """Work Items (Bibliothèque d'ouvrages) API tests"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.fixture(scope="class")
    def created_item_id(self, auth_headers):
        """Create a test work item and return its ID"""
        test_item = {
            "name": f"TEST_Pose carrelage {uuid.uuid4().hex[:6]}",
            "description": "Test work item for automated testing",
            "category": "carrelage",
            "unit": "m²",
            "unit_price": 45.50,
            "vat_rate": 20,
            "labor_cost": 30.00,
            "material_cost": 15.50
        }
        response = requests.post(f"{BASE_URL}/api/work-items", json=test_item, headers=auth_headers)
        assert response.status_code == 200, f"Failed to create work item: {response.text}"
        return response.json()["id"]
    
    def test_list_work_items(self, auth_headers):
        """Test GET /api/work-items returns list"""
        response = requests.get(f"{BASE_URL}/api/work-items", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_categories(self, auth_headers):
        """Test GET /api/work-items/categories returns categories"""
        response = requests.get(f"{BASE_URL}/api/work-items/categories", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "categories" in data
        assert isinstance(data["categories"], list)
    
    def test_get_units(self, auth_headers):
        """Test GET /api/work-items/units returns units"""
        response = requests.get(f"{BASE_URL}/api/work-items/units", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        # Should have common units
        unit_values = [u["value"] for u in data]
        assert "m²" in unit_values or "u" in unit_values
    
    def test_create_work_item(self, auth_headers):
        """Test POST /api/work-items creates item"""
        test_item = {
            "name": f"TEST_Peinture mur {uuid.uuid4().hex[:6]}",
            "description": "Test painting work item",
            "category": "peinture",
            "unit": "m²",
            "unit_price": 25.00,
            "vat_rate": 10
        }
        response = requests.post(f"{BASE_URL}/api/work-items", json=test_item, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == test_item["name"]
        assert data["category"] == test_item["category"]
        assert data["unit_price"] == test_item["unit_price"]
        assert "id" in data
        
        # Cleanup - delete the created item
        requests.delete(f"{BASE_URL}/api/work-items/{data['id']}", headers=auth_headers)
    
    def test_get_work_item_by_id(self, auth_headers, created_item_id):
        """Test GET /api/work-items/{id} returns item"""
        response = requests.get(f"{BASE_URL}/api/work-items/{created_item_id}", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == created_item_id
        assert "name" in data
        assert "category" in data
    
    def test_update_work_item(self, auth_headers, created_item_id):
        """Test PUT /api/work-items/{id} updates item"""
        update_data = {
            "unit_price": 55.00,
            "description": "Updated description"
        }
        response = requests.put(f"{BASE_URL}/api/work-items/{created_item_id}", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["unit_price"] == 55.00
        assert data["description"] == "Updated description"
        
        # Verify persistence with GET
        get_response = requests.get(f"{BASE_URL}/api/work-items/{created_item_id}", headers=auth_headers)
        assert get_response.status_code == 200
        assert get_response.json()["unit_price"] == 55.00
    
    def test_duplicate_work_item(self, auth_headers, created_item_id):
        """Test POST /api/work-items/{id}/duplicate creates copy"""
        response = requests.post(f"{BASE_URL}/api/work-items/{created_item_id}/duplicate", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] != created_item_id
        assert "Copie" in data["name"] or data["name"].startswith("TEST_")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/work-items/{data['id']}", headers=auth_headers)
    
    def test_delete_work_item(self, auth_headers):
        """Test DELETE /api/work-items/{id} removes item"""
        # Create item to delete
        test_item = {
            "name": f"TEST_ToDelete {uuid.uuid4().hex[:6]}",
            "category": "autres",
            "unit": "u",
            "unit_price": 10.00
        }
        create_response = requests.post(f"{BASE_URL}/api/work-items", json=test_item, headers=auth_headers)
        item_id = create_response.json()["id"]
        
        # Delete
        delete_response = requests.delete(f"{BASE_URL}/api/work-items/{item_id}", headers=auth_headers)
        assert delete_response.status_code == 200
        
        # Verify deleted
        get_response = requests.get(f"{BASE_URL}/api/work-items/{item_id}", headers=auth_headers)
        assert get_response.status_code == 404
    
    def test_work_item_filter_by_category(self, auth_headers):
        """Test filtering work items by category"""
        response = requests.get(f"{BASE_URL}/api/work-items?category=carrelage", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        # All items should be in carrelage category (if any exist)
        for item in data:
            assert item["category"] == "carrelage"


class TestProjectsAPI:
    """Projects (Chantiers) API tests"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.fixture(scope="class")
    def created_project_id(self, auth_headers):
        """Create a test project and return its ID"""
        test_project = {
            "project_name": f"TEST_Chantier {uuid.uuid4().hex[:6]}",
            "description": "Test project for automated testing",
            "address": "123 Rue Test",
            "city": "Paris",
            "postal_code": "75001",
            "status": "planning",
            "budget": 50000.00,
            "estimated_cost": 45000.00
        }
        response = requests.post(f"{BASE_URL}/api/projects", json=test_project, headers=auth_headers)
        assert response.status_code == 200, f"Failed to create project: {response.text}"
        return response.json()["id"]
    
    def test_list_projects(self, auth_headers):
        """Test GET /api/projects returns list"""
        response = requests.get(f"{BASE_URL}/api/projects", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_create_project(self, auth_headers):
        """Test POST /api/projects creates project"""
        test_project = {
            "project_name": f"TEST_Renovation {uuid.uuid4().hex[:6]}",
            "description": "Test renovation project",
            "address": "456 Avenue Test",
            "city": "Lyon",
            "postal_code": "69001",
            "status": "planning",
            "budget": 75000.00
        }
        response = requests.post(f"{BASE_URL}/api/projects", json=test_project, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["project_name"] == test_project["project_name"]
        assert data["city"] == test_project["city"]
        assert data["status"] == "planning"
        assert "id" in data
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/projects/{data['id']}", headers=auth_headers)
    
    def test_get_project_by_id(self, auth_headers, created_project_id):
        """Test GET /api/projects/{id} returns project"""
        response = requests.get(f"{BASE_URL}/api/projects/{created_project_id}", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == created_project_id
        assert "project_name" in data
        assert "status" in data
    
    def test_update_project(self, auth_headers, created_project_id):
        """Test PUT /api/projects/{id} updates project"""
        update_data = {
            "status": "in_progress",
            "budget": 60000.00
        }
        response = requests.put(f"{BASE_URL}/api/projects/{created_project_id}", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "in_progress"
        assert data["budget"] == 60000.00
        
        # Verify persistence
        get_response = requests.get(f"{BASE_URL}/api/projects/{created_project_id}", headers=auth_headers)
        assert get_response.status_code == 200
        assert get_response.json()["status"] == "in_progress"
    
    def test_delete_project(self, auth_headers):
        """Test DELETE /api/projects/{id} removes project"""
        # Create project to delete
        test_project = {
            "project_name": f"TEST_ToDelete {uuid.uuid4().hex[:6]}",
            "status": "planning",
            "budget": 10000.00
        }
        create_response = requests.post(f"{BASE_URL}/api/projects", json=test_project, headers=auth_headers)
        project_id = create_response.json()["id"]
        
        # Delete
        delete_response = requests.delete(f"{BASE_URL}/api/projects/{project_id}", headers=auth_headers)
        assert delete_response.status_code == 200
        
        # Verify deleted
        get_response = requests.get(f"{BASE_URL}/api/projects/{project_id}", headers=auth_headers)
        assert get_response.status_code == 404
    
    def test_project_filter_by_status(self, auth_headers):
        """Test filtering projects by status"""
        response = requests.get(f"{BASE_URL}/api/projects?status=planning", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        # All projects should have planning status (if any exist)
        for project in data:
            assert project["status"] == "planning"
    
    def test_project_timeline(self, auth_headers):
        """Test GET /api/projects/timeline returns timeline data"""
        response = requests.get(f"{BASE_URL}/api/projects/timeline", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, (list, dict))
    
    def test_project_margins(self, auth_headers):
        """Test GET /api/projects/margins returns margin data"""
        response = requests.get(f"{BASE_URL}/api/projects/margins", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)


class TestCleanup:
    """Cleanup test data"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_cleanup_test_work_items(self, auth_headers):
        """Clean up TEST_ prefixed work items"""
        response = requests.get(f"{BASE_URL}/api/work-items", headers=auth_headers)
        if response.status_code == 200:
            items = response.json()
            for item in items:
                if item["name"].startswith("TEST_"):
                    requests.delete(f"{BASE_URL}/api/work-items/{item['id']}", headers=auth_headers)
        assert True  # Cleanup always passes
    
    def test_cleanup_test_projects(self, auth_headers):
        """Clean up TEST_ prefixed projects"""
        response = requests.get(f"{BASE_URL}/api/projects", headers=auth_headers)
        if response.status_code == 200:
            projects = response.json()
            for project in projects:
                if project["project_name"].startswith("TEST_"):
                    requests.delete(f"{BASE_URL}/api/projects/{project['id']}", headers=auth_headers)
        assert True  # Cleanup always passes


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
