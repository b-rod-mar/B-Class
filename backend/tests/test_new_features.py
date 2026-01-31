"""
Test suite for new features:
1. Classi Chat endpoint (/api/classi/chat)
2. HS Code Auto-suggest endpoint (/api/hs-codes/suggest)
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "testuser@test.com"
TEST_PASSWORD = "password123"


class TestAuthentication:
    """Test authentication to get token for subsequent tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        if response.status_code == 200:
            return response.json().get("token")
        # Try to register if login fails
        register_response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "name": "Test User"
            }
        )
        if register_response.status_code in [200, 201]:
            return register_response.json().get("token")
        pytest.skip("Authentication failed - cannot proceed with tests")
    
    def test_login_success(self):
        """Test login endpoint works"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        # Either login succeeds or user doesn't exist yet
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            data = response.json()
            assert "token" in data
            assert "user" in data


class TestClassiChat:
    """Test Classi Chat helpdesk endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers for authenticated requests"""
        # First try login
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        if response.status_code == 200:
            token = response.json().get("token")
            return {"Authorization": f"Bearer {token}"}
        
        # Try register if login fails
        register_response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "name": "Test User"
            }
        )
        if register_response.status_code in [200, 201]:
            token = register_response.json().get("token")
            return {"Authorization": f"Bearer {token}"}
        
        pytest.skip("Cannot authenticate")
    
    def test_classi_chat_endpoint_exists(self, auth_headers):
        """Test that Classi chat endpoint exists and responds"""
        response = requests.post(
            f"{BASE_URL}/api/classi/chat",
            json={"message": "Hello"},
            headers=auth_headers
        )
        # Should return 200 (success) or 422 (validation error if message format wrong)
        assert response.status_code in [200, 422], f"Unexpected status: {response.status_code}, body: {response.text}"
    
    def test_classi_chat_forms_question(self, auth_headers):
        """Test Classi responds to forms question"""
        response = requests.post(
            f"{BASE_URL}/api/classi/chat",
            json={"message": "What forms do I need for importing goods to The Bahamas?"},
            headers=auth_headers,
            timeout=60  # AI responses can take time
        )
        assert response.status_code == 200, f"Status: {response.status_code}, body: {response.text}"
        data = response.json()
        assert "response" in data
        assert len(data["response"]) > 0
        print(f"Classi response: {data['response'][:200]}...")
    
    def test_classi_chat_hs_code_help(self, auth_headers):
        """Test Classi responds to HS code help question"""
        response = requests.post(
            f"{BASE_URL}/api/classi/chat",
            json={"message": "How do I find the correct HS code for my product?"},
            headers=auth_headers,
            timeout=60
        )
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert len(data["response"]) > 0
        print(f"Classi HS code help response: {data['response'][:200]}...")
    
    def test_classi_chat_requires_auth(self):
        """Test that Classi chat requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/classi/chat",
            json={"message": "Hello"}
        )
        # Should return 401 or 403 without auth
        assert response.status_code in [401, 403]


class TestHSCodeAutoSuggest:
    """Test HS Code auto-suggest endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers for authenticated requests"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        if response.status_code == 200:
            token = response.json().get("token")
            return {"Authorization": f"Bearer {token}"}
        
        register_response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "name": "Test User"
            }
        )
        if register_response.status_code in [200, 201]:
            token = register_response.json().get("token")
            return {"Authorization": f"Bearer {token}"}
        
        pytest.skip("Cannot authenticate")
    
    def test_suggest_endpoint_exists(self, auth_headers):
        """Test that suggest endpoint exists"""
        response = requests.get(
            f"{BASE_URL}/api/hs-codes/suggest?q=wine",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Status: {response.status_code}, body: {response.text}"
        data = response.json()
        assert "suggestions" in data
    
    def test_suggest_returns_array(self, auth_headers):
        """Test that suggest returns an array of suggestions"""
        response = requests.get(
            f"{BASE_URL}/api/hs-codes/suggest?q=phone",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
        assert isinstance(data["suggestions"], list)
        print(f"Suggestions for 'phone': {data['suggestions']}")
    
    def test_suggest_short_query_returns_empty(self, auth_headers):
        """Test that queries less than 2 chars return empty"""
        response = requests.get(
            f"{BASE_URL}/api/hs-codes/suggest?q=a",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["suggestions"] == []
    
    def test_suggest_requires_auth(self):
        """Test that suggest requires authentication"""
        response = requests.get(
            f"{BASE_URL}/api/hs-codes/suggest?q=wine"
        )
        assert response.status_code in [401, 403]
    
    def test_suggest_with_limit(self, auth_headers):
        """Test suggest with custom limit"""
        response = requests.get(
            f"{BASE_URL}/api/hs-codes/suggest?q=22&limit=5",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
        # Should not exceed limit
        assert len(data["suggestions"]) <= 5


class TestHSCodeLibrarySearch:
    """Test HS Code library search functionality"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        if response.status_code == 200:
            token = response.json().get("token")
            return {"Authorization": f"Bearer {token}"}
        
        register_response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "name": "Test User"
            }
        )
        if register_response.status_code in [200, 201]:
            token = register_response.json().get("token")
            return {"Authorization": f"Bearer {token}"}
        
        pytest.skip("Cannot authenticate")
    
    def test_hs_codes_list(self, auth_headers):
        """Test listing HS codes"""
        response = requests.get(
            f"{BASE_URL}/api/hs-codes",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Total HS codes in library: {len(data)}")
    
    def test_hs_codes_search(self, auth_headers):
        """Test searching HS codes"""
        response = requests.get(
            f"{BASE_URL}/api/hs-codes?search=wine",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"HS codes matching 'wine': {len(data)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
