#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
import time

class BrainPathAPITester:
    def __init__(self, base_url="https://smart-study-85.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.session_id = None
        
        # Test data
        self.test_email = f"test_{datetime.now().strftime('%H%M%S')}@brainpath.com"
        self.test_password = "TestPass123!"
        self.test_topic = "Photosynthesis"

    def log(self, message, status="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {status}: {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        self.log(f"Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=30)

            success = response.status_code == expected_status
            
            if success:
                self.tests_passed += 1
                self.log(f"✅ {name} - Status: {response.status_code}", "PASS")
                try:
                    return True, response.json()
                except:
                    return True, response.text
            else:
                self.log(f"❌ {name} - Expected {expected_status}, got {response.status_code}", "FAIL")
                try:
                    error_detail = response.json()
                    self.log(f"   Error details: {error_detail}", "ERROR")
                except:
                    self.log(f"   Response: {response.text[:200]}", "ERROR")
                return False, {}

        except requests.exceptions.Timeout:
            self.log(f"❌ {name} - Request timeout", "FAIL")
            return False, {}
        except Exception as e:
            self.log(f"❌ {name} - Error: {str(e)}", "FAIL")
            return False, {}

    def test_signup(self):
        """Test user signup"""
        success, response = self.run_test(
            "User Signup",
            "POST",
            "auth/signup",
            200,
            data={
                "email": self.test_email,
                "password": self.test_password,
                "education_level": "school",
                "sub_level": "high_school",
                "board": "cbse"
            }
        )
        
        if success and 'token' in response:
            self.token = response['token']
            self.user_id = response['user']['id']
            self.log(f"   Token obtained: {self.token[:20]}...", "INFO")
            return True
        return False

    def test_login(self):
        """Test user login"""
        success, response = self.run_test(
            "User Login",
            "POST",
            "auth/login",
            200,
            data={
                "email": self.test_email,
                "password": self.test_password
            }
        )
        
        if success and 'token' in response:
            self.token = response['token']
            self.user_id = response['user']['id']
            return True
        return False

    def test_generate_content_passage(self):
        """Test content generation for passage technique"""
        success, response = self.run_test(
            "Generate Passage Content",
            "POST",
            "learning/generate-content",
            200,
            data={
                "topic": self.test_topic,
                "technique": "passage"
            }
        )
        
        if success and response.get('type') == 'passage':
            self.log(f"   Generated passage length: {len(response.get('content', ''))}", "INFO")
            return True, response
        return False, {}

    def test_generate_content_video(self):
        """Test content generation for video technique"""
        success, response = self.run_test(
            "Generate Video Content",
            "POST",
            "learning/generate-content",
            200,
            data={
                "topic": self.test_topic,
                "technique": "video"
            }
        )
        
        if success and response.get('type') == 'video':
            video_data = response.get('content', {})
            self.log(f"   Video ID: {video_data.get('videoId', 'N/A')}", "INFO")
            return True, response
        return False, {}

    def test_generate_content_flowchart(self):
        """Test content generation for flowchart technique"""
        success, response = self.run_test(
            "Generate Flowchart Content",
            "POST",
            "learning/generate-content",
            200,
            data={
                "topic": self.test_topic,
                "technique": "flowchart"
            }
        )
        
        if success and response.get('type') == 'flowchart':
            self.log(f"   Flowchart length: {len(response.get('content', ''))}", "INFO")
            return True, response
        return False, {}

    def test_generate_questions(self, content):
        """Test question generation"""
        success, response = self.run_test(
            "Generate Questions",
            "POST",
            "learning/generate-questions",
            200,
            data={
                "topic": self.test_topic,
                "content": content[:1000],  # Limit content length
                "technique": "passage",
                "difficulty": 1
            }
        )
        
        if success and 'questions' in response:
            questions = response['questions']
            self.log(f"   Generated {len(questions)} questions", "INFO")
            return True, questions
        return False, []

    def test_create_session(self, content, questions):
        """Test learning session creation"""
        success, response = self.run_test(
            "Create Learning Session",
            "POST",
            "learning/create-session",
            200,
            data={
                "topic": self.test_topic,
                "technique": "passage",
                "content": content,
                "questions": questions
            }
        )
        
        if success and 'session_id' in response:
            self.session_id = response['session_id']
            self.log(f"   Session ID: {self.session_id}", "INFO")
            return True
        return False

    def test_get_session(self):
        """Test getting session details"""
        if not self.session_id:
            self.log("No session ID available for testing", "SKIP")
            return False
            
        success, response = self.run_test(
            "Get Learning Session",
            "GET",
            f"learning/session/{self.session_id}",
            200
        )
        
        if success and response.get('id') == self.session_id:
            return True
        return False

    def test_evaluate_answer(self, questions):
        """Test answer evaluation"""
        if not self.session_id or not questions:
            self.log("No session or questions available for testing", "SKIP")
            return False
            
        # Test with first question
        question = questions[0]
        test_answer = "A) Test answer" if question.get('type') == 'mcq' else "This is a test answer for evaluation."
        
        success, response = self.run_test(
            "Evaluate Answer",
            "POST",
            "learning/evaluate-answer",
            200,
            data={
                "session_id": self.session_id,
                "question_id": question['id'],
                "answer": test_answer,
                "time_taken": 25.5
            }
        )
        
        if success and 'is_correct' in response:
            self.log(f"   Answer evaluation: {'Correct' if response['is_correct'] else 'Incorrect'}", "INFO")
            return True
        return False

    def test_get_progress(self):
        """Test progress retrieval"""
        success, response = self.run_test(
            "Get User Progress",
            "GET",
            "progress",
            200
        )
        
        if success and 'accuracy' in response:
            self.log(f"   Accuracy: {response.get('accuracy', 0)}%", "INFO")
            return True
        return False

    def test_get_analytics(self):
        """Test analytics dashboard"""
        success, response = self.run_test(
            "Get Analytics Dashboard",
            "GET",
            "analytics/dashboard",
            200
        )
        
        if success and 'technique_performance' in response:
            self.log(f"   Techniques tracked: {len(response.get('technique_performance', {}))}", "INFO")
            return True
        return False

    def test_invalid_auth(self):
        """Test invalid authentication"""
        # Save current token
        original_token = self.token
        self.token = "invalid_token_12345"
        
        success, response = self.run_test(
            "Invalid Auth Test",
            "GET",
            "progress",
            401  # Expecting unauthorized
        )
        
        # Restore original token
        self.token = original_token
        return success

def main():
    """Main test execution"""
    print("=" * 60)
    print("🧠 BrainPath API Testing Suite")
    print("=" * 60)
    
    tester = BrainPathAPITester()
    
    # Test sequence
    test_results = {}
    
    # 1. Authentication Tests
    tester.log("Starting Authentication Tests", "TEST")
    test_results['signup'] = tester.test_signup()
    
    if not test_results['signup']:
        tester.log("Signup failed, trying login with existing user", "WARN")
        test_results['login'] = tester.test_login()
        if not test_results['login']:
            tester.log("Both signup and login failed, stopping tests", "FAIL")
            return 1
    
    # 2. Content Generation Tests
    tester.log("Starting Content Generation Tests", "TEST")
    test_results['passage'], passage_content = tester.test_generate_content_passage()
    test_results['video'], video_content = tester.test_generate_content_video()
    test_results['flowchart'], flowchart_content = tester.test_generate_content_flowchart()
    
    # 3. Question Generation and Session Tests
    tester.log("Starting Question and Session Tests", "TEST")
    if test_results['passage']:
        content_text = passage_content.get('content', '')
        test_results['questions'], questions = tester.test_generate_questions(content_text)
        
        if test_results['questions']:
            test_results['create_session'] = tester.test_create_session(content_text, questions)
            test_results['get_session'] = tester.test_get_session()
            test_results['evaluate_answer'] = tester.test_evaluate_answer(questions)
    
    # 4. Analytics Tests
    tester.log("Starting Analytics Tests", "TEST")
    test_results['progress'] = tester.test_get_progress()
    test_results['analytics'] = tester.test_get_analytics()
    
    # 5. Security Tests
    tester.log("Starting Security Tests", "TEST")
    test_results['invalid_auth'] = tester.test_invalid_auth()
    
    # Results Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed_tests = []
    failed_tests = []
    
    for test_name, result in test_results.items():
        if result:
            passed_tests.append(test_name)
            print(f"✅ {test_name.replace('_', ' ').title()}")
        else:
            failed_tests.append(test_name)
            print(f"❌ {test_name.replace('_', ' ').title()}")
    
    print(f"\n📈 Overall: {tester.tests_passed}/{tester.tests_run} tests passed")
    print(f"🎯 Success Rate: {(tester.tests_passed/tester.tests_run*100):.1f}%")
    
    if failed_tests:
        print(f"\n⚠️  Failed Tests: {', '.join(failed_tests)}")
    
    # Return appropriate exit code
    return 0 if len(failed_tests) == 0 else 1

if __name__ == "__main__":
    sys.exit(main())