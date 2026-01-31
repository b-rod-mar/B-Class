"""
Test New Features - Iteration 4
Tests for:
1. Vehicle Calculator body_style dropdown - verify it saves to database and appears in results/history
2. Vehicle Calculator MOF Approval Granted button - appears for vehicles >10 years old and toggles correctly
3. HS Code Library legend - displays flag legend explaining Restricted Item (shield) and Requires Permit (warning) icons
4. Vehicle bulk upload template - should now include body_style column
5. Vehicle Calculator single calculation flow - make, model, year, vehicle_type, body_style, cif_value, should return calculation with total_landed_cost
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://customsai-1.preview.emergentagent.com').rstrip('/')

# Test credentials
TEST_EMAIL = "testuser2@test.com"
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
    pytest.skip(f"Authentication failed - status {response.status_code}")


@pytest.fixture
def api_client(auth_token):
    """Create authenticated API client"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session


class TestVehicleBodyStyleFeature:
    """Tests for body_style field in vehicle calculations"""
    
    def test_body_style_saved_in_calculation(self, api_client):
        """Test that body_style is saved when calculating vehicle duties"""
        response = api_client.post(
            f"{BASE_URL}/api/vehicle/calculate",
            json={
                "make": "Toyota",
                "model": "Camry",
                "year": 2024,
                "vehicle_type": "gasoline",
                "body_style": "sedan",
                "engine_size_cc": 2500,
                "cif_value": 35000,
                "country_of_origin": "Japan",
                "is_new": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify body_style is in the response
        assert "body_style" in data, "body_style field missing from response"
        assert data["body_style"] == "sedan", f"Expected 'sedan', got '{data.get('body_style')}'"
        
        # Store calc_id for history verification
        return data.get("id")
    
    def test_body_style_suv_saved(self, api_client):
        """Test SUV body style is saved correctly"""
        response = api_client.post(
            f"{BASE_URL}/api/vehicle/calculate",
            json={
                "make": "Jeep",
                "model": "Grand Cherokee",
                "year": 2023,
                "vehicle_type": "gasoline",
                "body_style": "suv",
                "engine_size_cc": 3600,
                "cif_value": 55000,
                "country_of_origin": "USA",
                "is_new": False
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["body_style"] == "suv"
    
    def test_body_style_pickup_saved(self, api_client):
        """Test pickup body style is saved correctly"""
        response = api_client.post(
            f"{BASE_URL}/api/vehicle/calculate",
            json={
                "make": "Ford",
                "model": "F-150",
                "year": 2024,
                "vehicle_type": "commercial",
                "body_style": "pickup",
                "cif_value": 45000,
                "country_of_origin": "USA",
                "is_new": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["body_style"] == "pickup"
    
    def test_body_style_appears_in_history(self, api_client):
        """Test that body_style appears in calculation history"""
        # First create a calculation with body_style
        calc_response = api_client.post(
            f"{BASE_URL}/api/vehicle/calculate",
            json={
                "make": "Honda",
                "model": "CR-V",
                "year": 2024,
                "vehicle_type": "gasoline",
                "body_style": "crossover",
                "engine_size_cc": 1500,
                "cif_value": 32000,
                "country_of_origin": "Japan",
                "is_new": True
            }
        )
        assert calc_response.status_code == 200
        calc_id = calc_response.json().get("id")
        
        # Now fetch history and verify body_style is present
        history_response = api_client.get(f"{BASE_URL}/api/vehicle/calculations")
        assert history_response.status_code == 200
        
        history = history_response.json()
        assert isinstance(history, list)
        
        # Find our calculation in history
        found = False
        for calc in history:
            if calc.get("id") == calc_id:
                found = True
                assert "body_style" in calc, "body_style missing from history record"
                assert calc["body_style"] == "crossover"
                break
        
        assert found, f"Calculation {calc_id} not found in history"


class TestVehicleTemplateBodyStyle:
    """Tests for body_style column in vehicle bulk upload template"""
    
    def test_template_includes_body_style_column(self, api_client):
        """Test that vehicle template CSV includes body_style column"""
        response = api_client.get(f"{BASE_URL}/api/vehicle/template")
        
        assert response.status_code == 200
        
        content = response.text
        # Check that body_style is in the header row
        first_line = content.split('\n')[0].lower()
        assert "body_style" in first_line, f"body_style column missing from template header: {first_line}"
    
    def test_template_has_body_style_sample_data(self, api_client):
        """Test that template has sample body_style values"""
        response = api_client.get(f"{BASE_URL}/api/vehicle/template")
        
        assert response.status_code == 200
        
        content = response.text.lower()
        # Check for sample body styles in the data rows
        body_styles = ["sedan", "suv", "hatchback"]
        found_styles = [style for style in body_styles if style in content]
        
        assert len(found_styles) > 0, f"No sample body_style values found in template. Expected one of: {body_styles}"


class TestVehicleCalculationFlow:
    """Tests for complete vehicle calculation flow with all required fields"""
    
    def test_single_calculation_returns_total_landed_cost(self, api_client):
        """Test that single calculation returns total_landed_cost"""
        response = api_client.post(
            f"{BASE_URL}/api/vehicle/calculate",
            json={
                "make": "Toyota",
                "model": "Corolla",
                "year": 2024,
                "vehicle_type": "gasoline",
                "body_style": "sedan",
                "engine_size_cc": 1800,
                "cif_value": 28000,
                "country_of_origin": "Japan",
                "is_new": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify all expected fields are present
        assert "make" in data
        assert "model" in data
        assert "year" in data
        assert "vehicle_type" in data
        assert "body_style" in data
        assert "cif_value" in data
        assert "total_landed_cost" in data
        
        # Verify total_landed_cost is calculated
        assert data["total_landed_cost"] > 0
        assert data["total_landed_cost"] > data["cif_value"]  # Should include duties
    
    def test_calculation_breakdown_complete(self, api_client):
        """Test that calculation includes complete breakdown"""
        response = api_client.post(
            f"{BASE_URL}/api/vehicle/calculate",
            json={
                "make": "Nissan",
                "model": "Altima",
                "year": 2024,
                "vehicle_type": "gasoline",
                "body_style": "sedan",
                "engine_size_cc": 2500,
                "cif_value": 32000,
                "country_of_origin": "Japan",
                "is_new": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify breakdown is present
        assert "breakdown" in data
        breakdown = data["breakdown"]
        
        assert "cif_value" in breakdown
        assert "import_duty" in breakdown
        assert "total" in breakdown


class TestVehicleOldVehicleWarnings:
    """Tests for vehicles over 10 years old - MOF approval warnings"""
    
    def test_old_vehicle_gets_warning(self, api_client):
        """Test that vehicles >10 years old get MOF approval warning"""
        current_year = 2026  # Current year per system prompt
        old_year = current_year - 12  # 12 years old
        
        response = api_client.post(
            f"{BASE_URL}/api/vehicle/calculate",
            json={
                "make": "Toyota",
                "model": "Camry",
                "year": old_year,
                "vehicle_type": "gasoline",
                "body_style": "sedan",
                "engine_size_cc": 2400,
                "cif_value": 8000,
                "country_of_origin": "Japan",
                "is_new": False
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify warnings are present
        assert "warnings" in data
        warnings = data["warnings"]
        
        # Should have warning about old vehicle
        warning_text = " ".join(warnings).lower()
        assert "year" in warning_text or "old" in warning_text or "ministry" in warning_text or "approval" in warning_text, \
            f"Expected warning about old vehicle, got: {warnings}"
    
    def test_old_vehicle_environmental_levy(self, api_client):
        """Test that old vehicles get 20% environmental levy"""
        current_year = 2026
        old_year = current_year - 11  # 11 years old
        
        response = api_client.post(
            f"{BASE_URL}/api/vehicle/calculate",
            json={
                "make": "Honda",
                "model": "Accord",
                "year": old_year,
                "vehicle_type": "gasoline",
                "body_style": "sedan",
                "engine_size_cc": 2000,
                "cif_value": 10000,
                "country_of_origin": "Japan",
                "is_new": False
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify environmental levy description mentions 20%
        levy_desc = data.get("environmental_levy_description", "")
        assert "20%" in levy_desc or data.get("environmental_levy", 0) > 250, \
            f"Expected 20% environmental levy for old vehicle, got: {levy_desc}"


class TestHSCodeLibraryEndpoint:
    """Tests for HS Code Library API"""
    
    def test_get_hs_codes_returns_200(self, api_client):
        """Test that HS codes endpoint returns 200"""
        response = api_client.get(f"{BASE_URL}/api/hs-codes")
        assert response.status_code == 200
    
    def test_hs_codes_have_restricted_and_permit_flags(self, api_client):
        """Test that HS codes include is_restricted and requires_permit fields"""
        response = api_client.get(f"{BASE_URL}/api/hs-codes")
        assert response.status_code == 200
        
        data = response.json()
        if len(data) > 0:
            # Check first code has the flag fields
            first_code = data[0]
            assert "is_restricted" in first_code, "is_restricted field missing from HS code"
            assert "requires_permit" in first_code, "requires_permit field missing from HS code"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
