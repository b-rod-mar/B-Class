"""
Vehicle Calculator API Tests
Tests for the Vehicle Brokering Calculator module for The Bahamas HS Code Classification app.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://customsai-1.preview.emergentagent.com').rstrip('/')

# Test credentials
TEST_EMAIL = "vehicletest@test.com"
TEST_PASSWORD = "test123"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for tests"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip("Authentication failed - skipping tests")


@pytest.fixture
def api_client(auth_token):
    """Create authenticated API client"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session


class TestVehicleRatesEndpoint:
    """Tests for /api/vehicle/rates endpoint"""
    
    def test_get_rates_returns_200(self, api_client):
        """Test that rates endpoint returns 200"""
        response = api_client.get(f"{BASE_URL}/api/vehicle/rates")
        assert response.status_code == 200
    
    def test_rates_contains_all_vehicle_types(self, api_client):
        """Test that rates contain all vehicle types"""
        response = api_client.get(f"{BASE_URL}/api/vehicle/rates")
        data = response.json()
        
        assert "rates" in data
        rates = data["rates"]
        
        # Check all vehicle types are present
        expected_types = ["electric", "hybrid", "gasoline", "diesel", "commercial"]
        for vtype in expected_types:
            assert vtype in rates, f"Missing vehicle type: {vtype}"
    
    def test_electric_rates_have_correct_tiers(self, api_client):
        """Test electric vehicle rate tiers"""
        response = api_client.get(f"{BASE_URL}/api/vehicle/rates")
        data = response.json()
        
        electric = data["rates"]["electric"]
        assert electric["hs_code"] == "8703.80"
        assert len(electric["tiers"]) == 2
        
        # Under $50k should be 10%
        tier1 = electric["tiers"][0]
        assert tier1["rate"] == 0.10
        assert tier1["max_value"] == 50000
        
        # Over $50k should be 25%
        tier2 = electric["tiers"][1]
        assert tier2["rate"] == 0.25
    
    def test_rates_include_additional_fees(self, api_client):
        """Test that rates include VAT, environmental levy, etc."""
        response = api_client.get(f"{BASE_URL}/api/vehicle/rates")
        data = response.json()
        
        assert "vat_rate" in data
        assert "environmental_levy_rate" in data
        assert "stamp_duty_rate" in data
        assert "processing_fee" in data
        
        assert data["vat_rate"] == 0.10
        assert data["environmental_levy_rate"] == 0.01
        assert data["stamp_duty_rate"] == 0.07
        assert data["processing_fee"] == 100.0


class TestVehicleChecklistEndpoint:
    """Tests for /api/vehicle/checklist endpoint"""
    
    def test_get_checklist_returns_200(self, api_client):
        """Test that checklist endpoint returns 200"""
        response = api_client.get(f"{BASE_URL}/api/vehicle/checklist")
        assert response.status_code == 200
    
    def test_checklist_has_client_and_broker_sections(self, api_client):
        """Test checklist structure"""
        response = api_client.get(f"{BASE_URL}/api/vehicle/checklist")
        data = response.json()
        
        assert "client_checklist" in data
        assert "broker_checklist" in data
        assert "important_contacts" in data
    
    def test_client_checklist_has_required_categories(self, api_client):
        """Test client checklist categories"""
        response = api_client.get(f"{BASE_URL}/api/vehicle/checklist")
        data = response.json()
        
        client_checklist = data["client_checklist"]
        categories = [item["category"] for item in client_checklist]
        
        assert "Vehicle Documents" in categories
        assert "Shipping Documents" in categories
        assert "Personal Documents" in categories


class TestVehicleCalculateEndpoint:
    """Tests for /api/vehicle/calculate endpoint"""
    
    def test_electric_under_50k_gets_10_percent(self, api_client):
        """Electric vehicle under $50k should get 10% duty"""
        response = api_client.post(
            f"{BASE_URL}/api/vehicle/calculate",
            json={
                "make": "Tesla",
                "model": "Model 3",
                "year": 2024,
                "vehicle_type": "electric",
                "cif_value": 40000,
                "country_of_origin": "USA",
                "is_new": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["duty_rate"] == 0.10
        assert data["import_duty"] == 4000.0  # 40000 * 0.10
        assert "10%" in data["duty_rate_display"]
    
    def test_electric_over_50k_gets_25_percent(self, api_client):
        """Electric vehicle over $50k should get 25% duty"""
        response = api_client.post(
            f"{BASE_URL}/api/vehicle/calculate",
            json={
                "make": "Tesla",
                "model": "Model S",
                "year": 2024,
                "vehicle_type": "electric",
                "cif_value": 80000,
                "country_of_origin": "USA",
                "is_new": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["duty_rate"] == 0.25
        assert data["import_duty"] == 20000.0  # 80000 * 0.25
        assert "25%" in data["duty_rate_display"]
    
    def test_gasoline_under_1500cc_gets_45_percent(self, api_client):
        """Gasoline vehicle with engine <1.5L should get 45% duty"""
        response = api_client.post(
            f"{BASE_URL}/api/vehicle/calculate",
            json={
                "make": "Toyota",
                "model": "Yaris",
                "year": 2023,
                "vehicle_type": "gasoline",
                "engine_size_cc": 1200,
                "cif_value": 25000,
                "country_of_origin": "Japan",
                "is_new": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["duty_rate"] == 0.45
        assert data["import_duty"] == 11250.0  # 25000 * 0.45
        assert "45%" in data["duty_rate_display"]
        assert "Small" in data["engine_category"]
    
    def test_gasoline_1500_2000cc_under_50k_gets_45_percent(self, api_client):
        """Gasoline 1.5-2.0L under $50k should get 45% duty"""
        response = api_client.post(
            f"{BASE_URL}/api/vehicle/calculate",
            json={
                "make": "Honda",
                "model": "Civic",
                "year": 2023,
                "vehicle_type": "gasoline",
                "engine_size_cc": 1800,
                "cif_value": 35000,
                "country_of_origin": "Japan",
                "is_new": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["duty_rate"] == 0.45
        assert data["import_duty"] == 15750.0  # 35000 * 0.45
        assert "Medium" in data["engine_category"]
    
    def test_gasoline_1500_2000cc_over_50k_gets_65_percent(self, api_client):
        """Gasoline 1.5-2.0L over $50k should get 65% duty"""
        response = api_client.post(
            f"{BASE_URL}/api/vehicle/calculate",
            json={
                "make": "BMW",
                "model": "320i",
                "year": 2024,
                "vehicle_type": "gasoline",
                "engine_size_cc": 1998,
                "cif_value": 60000,
                "country_of_origin": "Germany",
                "is_new": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["duty_rate"] == 0.65
        assert data["import_duty"] == 39000.0  # 60000 * 0.65
        assert "65%" in data["duty_rate_display"]
    
    def test_gasoline_over_2000cc_gets_65_percent(self, api_client):
        """Gasoline vehicle with engine >2.0L should get 65% duty"""
        response = api_client.post(
            f"{BASE_URL}/api/vehicle/calculate",
            json={
                "make": "Ford",
                "model": "Mustang",
                "year": 2024,
                "vehicle_type": "gasoline",
                "engine_size_cc": 5000,
                "cif_value": 55000,
                "country_of_origin": "USA",
                "is_new": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["duty_rate"] == 0.65
        assert data["import_duty"] == 35750.0  # 55000 * 0.65
        assert "Large" in data["engine_category"]
    
    def test_commercial_vehicle_gets_65_percent(self, api_client):
        """Commercial vehicle should get 65% duty"""
        response = api_client.post(
            f"{BASE_URL}/api/vehicle/calculate",
            json={
                "make": "Ford",
                "model": "F-150",
                "year": 2024,
                "vehicle_type": "commercial",
                "cif_value": 45000,
                "country_of_origin": "USA",
                "is_new": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["duty_rate"] == 0.65
        assert data["import_duty"] == 29250.0  # 45000 * 0.65
        assert "Commercial" in data["warnings"][0]
    
    def test_total_landed_cost_calculation(self, api_client):
        """Test total landed cost includes all fees"""
        response = api_client.post(
            f"{BASE_URL}/api/vehicle/calculate",
            json={
                "make": "Toyota",
                "model": "Camry",
                "year": 2024,
                "vehicle_type": "gasoline",
                "engine_size_cc": 2500,
                "cif_value": 30000,
                "country_of_origin": "Japan",
                "is_new": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify all components are present
        assert "cif_value" in data
        assert "import_duty" in data
        assert "environmental_levy" in data
        assert "stamp_duty" in data
        assert "vat" in data
        assert "processing_fee" in data
        assert "total_landed_cost" in data
        
        # Verify rates
        assert data["environmental_levy_rate"] == "1%"
        assert data["stamp_duty_rate"] == "7%"
        assert data["vat_rate"] == "10%"
        assert data["processing_fee"] == 100.0
        
        # Verify calculation
        cif = data["cif_value"]
        duty = data["import_duty"]
        env_levy = data["environmental_levy"]
        stamp = data["stamp_duty"]
        vat = data["vat"]
        fee = data["processing_fee"]
        
        expected_total = cif + duty + env_levy + stamp + vat + fee
        assert abs(data["total_landed_cost"] - expected_total) < 0.01
    
    def test_hybrid_vehicle_same_as_electric(self, api_client):
        """Hybrid vehicle should have same rates as electric"""
        response = api_client.post(
            f"{BASE_URL}/api/vehicle/calculate",
            json={
                "make": "Toyota",
                "model": "Prius",
                "year": 2024,
                "vehicle_type": "hybrid",
                "cif_value": 35000,
                "country_of_origin": "Japan",
                "is_new": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Under $50k should be 10%
        assert data["duty_rate"] == 0.10
        assert data["hs_code"] == "8703.40"
    
    def test_missing_required_fields_returns_422(self, api_client):
        """Test validation for missing required fields"""
        response = api_client.post(
            f"{BASE_URL}/api/vehicle/calculate",
            json={
                "make": "Toyota"
                # Missing model, year, vehicle_type, cif_value, country_of_origin
            }
        )
        
        assert response.status_code == 422


class TestVehicleCalculationsHistory:
    """Tests for /api/vehicle/calculations endpoint"""
    
    def test_get_calculations_returns_200(self, api_client):
        """Test that calculations history endpoint returns 200"""
        response = api_client.get(f"{BASE_URL}/api/vehicle/calculations")
        assert response.status_code == 200
    
    def test_calculations_returns_list(self, api_client):
        """Test that calculations returns a list"""
        response = api_client.get(f"{BASE_URL}/api/vehicle/calculations")
        data = response.json()
        
        assert isinstance(data, list)


class TestVehicleTemplate:
    """Tests for /api/vehicle/template endpoint"""
    
    def test_get_template_returns_200(self, api_client):
        """Test that template endpoint returns 200"""
        response = api_client.get(f"{BASE_URL}/api/vehicle/template")
        assert response.status_code == 200
    
    def test_template_is_csv(self, api_client):
        """Test that template is CSV format"""
        response = api_client.get(f"{BASE_URL}/api/vehicle/template")
        
        content_type = response.headers.get("content-type", "")
        assert "text/csv" in content_type or "text/plain" in content_type
        
        # Check CSV has expected headers
        content = response.text
        assert "make" in content.lower()
        assert "model" in content.lower()
        assert "vehicle_type" in content.lower()
        assert "cif_value" in content.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
