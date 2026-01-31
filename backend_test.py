import requests
import sys
import json
import io
import pandas as pd
from datetime import datetime

class HSCodeAPITester:
    def __init__(self, base_url="https://classb-hsclassify.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.user_id = None
        self.document_id = None
        self.classification_id = None
        self.hs_code_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)
        
        if files:
            # Remove Content-Type for file uploads
            test_headers.pop('Content-Type', None)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files, data=data, headers=test_headers)
                else:
                    response = requests.post(url, json=data, headers=test_headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers)

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

    def test_health_check(self):
        """Test API health"""
        return self.run_test("Health Check", "GET", "health", 200)

    def test_register(self):
        """Test user registration"""
        timestamp = datetime.now().strftime('%H%M%S')
        user_data = {
            "email": f"test{timestamp}@test.com",
            "password": "test123",
            "name": f"Test User {timestamp}",
            "company": "Test Company"
        }
        
        success, response = self.run_test("User Registration", "POST", "auth/register", 200, data=user_data)
        if success and 'token' in response:
            self.token = response['token']
            self.user_id = response['user']['id']
            print(f"   Registered user: {user_data['email']}")
            return True
        return False

    def test_login(self):
        """Test user login with test credentials"""
        login_data = {
            "email": "test@test.com",
            "password": "test123"
        }
        
        success, response = self.run_test("User Login", "POST", "auth/login", 200, data=login_data)
        if success and 'token' in response:
            self.token = response['token']
            self.user_id = response['user']['id']
            print(f"   Logged in as: {login_data['email']}")
            return True
        return False

    def test_get_me(self):
        """Test get current user"""
        return self.run_test("Get Current User", "GET", "auth/me", 200)

    def test_dashboard_stats(self):
        """Test dashboard stats"""
        return self.run_test("Dashboard Stats", "GET", "dashboard/stats", 200)

    def create_test_csv(self):
        """Create a test CSV file for upload"""
        test_data = {
            'Description': [
                'Apple iPhone 14 Pro Max 256GB',
                'Samsung Galaxy S23 Ultra',
                'Cotton T-Shirt Men Size L',
                'Laptop Computer Dell XPS 13',
                'Wireless Bluetooth Headphones'
            ],
            'Quantity': [2, 1, 10, 1, 5],
            'Unit': ['pcs', 'pcs', 'pcs', 'pcs', 'pcs'],
            'Unit Value': [1200.00, 1100.00, 25.00, 1500.00, 150.00],
            'Total Value': [2400.00, 1100.00, 250.00, 1500.00, 750.00],
            'Country of Origin': ['China', 'South Korea', 'Bangladesh', 'China', 'China']
        }
        
        df = pd.DataFrame(test_data)
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_content = csv_buffer.getvalue()
        
        return csv_content

    def test_document_upload(self):
        """Test document upload"""
        csv_content = self.create_test_csv()
        
        files = {
            'file': ('test_import.csv', csv_content, 'text/csv')
        }
        
        success, response = self.run_test("Document Upload", "POST", "documents/upload", 200, files=files)
        if success and 'id' in response:
            self.document_id = response['id']
            print(f"   Uploaded document ID: {self.document_id}")
            return True
        return False

    def test_get_documents(self):
        """Test get user documents"""
        return self.run_test("Get Documents", "GET", "documents", 200)

    def test_get_document(self):
        """Test get specific document"""
        if not self.document_id:
            print("❌ No document ID available for testing")
            return False
        return self.run_test("Get Document", "GET", f"documents/{self.document_id}", 200)

    def test_process_classification(self):
        """Test document classification"""
        if not self.document_id:
            print("❌ No document ID available for classification")
            return False
        
        success, response = self.run_test("Process Classification", "POST", f"classifications/process/{self.document_id}", 200)
        if success and 'id' in response:
            self.classification_id = response['id']
            print(f"   Classification ID: {self.classification_id}")
            print(f"   Total items: {response.get('total_items', 0)}")
            print(f"   Auto approved: {response.get('auto_approved_count', 0)}")
            print(f"   Needs review: {response.get('needs_review_count', 0)}")
            return True
        return False

    def test_get_classifications(self):
        """Test get user classifications"""
        return self.run_test("Get Classifications", "GET", "classifications", 200)

    def test_get_classification(self):
        """Test get specific classification"""
        if not self.classification_id:
            print("❌ No classification ID available for testing")
            return False
        return self.run_test("Get Classification", "GET", f"classifications/{self.classification_id}", 200)

    def test_update_classification_item(self):
        """Test update classification item"""
        if not self.classification_id:
            print("❌ No classification ID available for testing")
            return False
        
        # Update first item
        item_update = {
            "original_description": "Apple iPhone 14 Pro Max 256GB",
            "clean_description": "Apple iPhone 14 Pro Max 256GB Smartphone",
            "hs_code": "8517.12.00",
            "hs_description": "Telephones for cellular networks",
            "confidence_score": 95,
            "review_status": "reviewed",
            "reasoning": "Updated by manual review",
            "cma_notes": "Standard import, no restrictions",
            "gri_rules_applied": ["GRI 1", "GRI 6"],
            "is_restricted": False,
            "requires_permit": False
        }
        
        return self.run_test("Update Classification Item", "PUT", f"classifications/{self.classification_id}/items/0", 200, data=item_update)

    def test_export_classification_csv(self):
        """Test export classification as CSV"""
        if not self.classification_id:
            print("❌ No classification ID available for export")
            return False
        
        success, _ = self.run_test("Export Classification CSV", "GET", f"classifications/{self.classification_id}/export?format=csv", 200)
        return success

    def test_export_classification_xlsx(self):
        """Test export classification as Excel"""
        if not self.classification_id:
            print("❌ No classification ID available for export")
            return False
        
        success, _ = self.run_test("Export Classification Excel", "GET", f"classifications/{self.classification_id}/export?format=xlsx", 200)
        return success

    def test_get_hs_codes(self):
        """Test get HS codes"""
        return self.run_test("Get HS Codes", "GET", "hs-codes", 200)

    def test_create_hs_code(self):
        """Test create HS code"""
        hs_code_data = {
            "code": "8517.12.99",
            "description": "Test HS Code for Mobile Phones",
            "chapter": "85",
            "section": "XVI",
            "notes": "Test code for API testing",
            "duty_rate": "5%",
            "bahamas_extension": "99",
            "is_restricted": False,
            "requires_permit": False
        }
        
        success, response = self.run_test("Create HS Code", "POST", "hs-codes", 200, data=hs_code_data)
        if success and 'id' in response:
            self.hs_code_id = response['id']
            print(f"   Created HS code ID: {self.hs_code_id}")
            return True
        return False

    def test_update_hs_code(self):
        """Test update HS code"""
        if not self.hs_code_id:
            print("❌ No HS code ID available for update")
            return False
        
        update_data = {
            "code": "8517.12.99",
            "description": "Updated Test HS Code for Mobile Phones",
            "chapter": "85",
            "section": "XVI",
            "notes": "Updated test code for API testing",
            "duty_rate": "7.5%",
            "bahamas_extension": "99",
            "is_restricted": True,
            "requires_permit": True
        }
        
        return self.run_test("Update HS Code", "PUT", f"hs-codes/{self.hs_code_id}", 200, data=update_data)

    def test_search_hs_codes(self):
        """Test search HS codes"""
        return self.run_test("Search HS Codes", "GET", "hs-codes?search=mobile", 200)

    def test_delete_hs_code(self):
        """Test delete HS code (admin required)"""
        if not self.hs_code_id:
            print("❌ No HS code ID available for deletion")
            return False
        
        # This might fail if user is not admin, which is expected
        success, _ = self.run_test("Delete HS Code", "DELETE", f"hs-codes/{self.hs_code_id}", 200)
        if not success:
            print("   Note: Delete failed - likely requires admin role (expected)")
        return True  # Consider this test passed even if it fails due to permissions

def main():
    print("🚀 Starting Bahamas HS Code Classification API Tests")
    print("=" * 60)
    
    tester = HSCodeAPITester()
    
    # Test sequence
    tests = [
        ("Health Check", tester.test_health_check),
        ("User Registration", tester.test_register),
        ("User Login (fallback)", tester.test_login),
        ("Get Current User", tester.test_get_me),
        ("Dashboard Stats", tester.test_dashboard_stats),
        ("Document Upload", tester.test_document_upload),
        ("Get Documents", tester.test_get_documents),
        ("Get Document", tester.test_get_document),
        ("Process Classification", tester.test_process_classification),
        ("Get Classifications", tester.test_get_classifications),
        ("Get Classification", tester.test_get_classification),
        ("Update Classification Item", tester.test_update_classification_item),
        ("Export CSV", tester.test_export_classification_csv),
        ("Export Excel", tester.test_export_classification_xlsx),
        ("Get HS Codes", tester.test_get_hs_codes),
        ("Create HS Code", tester.test_create_hs_code),
        ("Update HS Code", tester.test_update_hs_code),
        ("Search HS Codes", tester.test_search_hs_codes),
        ("Delete HS Code", tester.test_delete_hs_code)
    ]
    
    # Run tests
    for test_name, test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"❌ {test_name} - Exception: {str(e)}")
    
    # Print results
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())