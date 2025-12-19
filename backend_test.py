import requests
import sys
import json
from datetime import datetime

class YouTubeCommentPickerTester:
    def __init__(self, base_url="https://random-comment-win.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=30):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"Response keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Non-dict response'}")
                except:
                    print("Response: Non-JSON or empty")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"Error detail: {error_detail}")
                except:
                    print(f"Error text: {response.text}")

            self.test_results.append({
                'name': name,
                'success': success,
                'status_code': response.status_code,
                'expected_status': expected_status
            })

            return success, response.json() if success and response.text else {}

        except requests.exceptions.Timeout:
            print(f"❌ Failed - Request timeout after {timeout}s")
            self.test_results.append({
                'name': name,
                'success': False,
                'error': 'Timeout'
            })
            return False, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.test_results.append({
                'name': name,
                'success': False,
                'error': str(e)
            })
            return False, {}

    def test_fetch_comments_valid_video(self):
        """Test fetching comments from a valid YouTube video"""
        # Using a popular video that should have comments
        test_video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll - popular video
        
        success, response = self.run_test(
            "Fetch Comments - Valid Video",
            "POST",
            "api/youtube/fetch-comments",
            200,
            data={"video_url": test_video_url},
            timeout=60  # YouTube API can be slow
        )
        
        if success:
            # Validate response structure
            required_keys = ['video_info', 'comments', 'total_comments']
            if all(key in response for key in required_keys):
                print(f"✅ Response structure valid")
                print(f"Video title: {response['video_info'].get('title', 'N/A')}")
                print(f"Comments fetched: {response['total_comments']}")
                return response
            else:
                print(f"❌ Missing required keys in response")
                return None
        return None

    def test_fetch_comments_invalid_url(self):
        """Test fetching comments with invalid URL"""
        success, response = self.run_test(
            "Fetch Comments - Invalid URL",
            "POST",
            "api/youtube/fetch-comments",
            400,
            data={"video_url": "invalid-url"}
        )
        return success

    def test_fetch_comments_nonexistent_video(self):
        """Test fetching comments from non-existent video"""
        success, response = self.run_test(
            "Fetch Comments - Non-existent Video",
            "POST",
            "api/youtube/fetch-comments",
            404,
            data={"video_url": "https://www.youtube.com/watch?v=nonexistent123"}
        )
        return success

    def test_pick_winners_basic(self, comments_data):
        """Test basic winner picking functionality"""
        if not comments_data or not comments_data.get('comments'):
            print("⚠️ Skipping winner tests - no comments data available")
            return False

        success, response = self.run_test(
            "Pick Winners - Basic",
            "POST",
            "api/youtube/pick-winners",
            200,
            data={
                "comments": comments_data['comments'][:10],  # Use first 10 comments
                "exclude_duplicates": True,
                "winner_count": 1
            }
        )
        
        if success:
            required_keys = ['winners', 'total_eligible', 'total_filtered']
            if all(key in response for key in required_keys):
                print(f"✅ Winner selection structure valid")
                print(f"Winners selected: {len(response['winners'])}")
                print(f"Total eligible: {response['total_eligible']}")
                return response
            else:
                print(f"❌ Missing required keys in winner response")
        return None

    def test_pick_winners_multiple(self, comments_data):
        """Test picking multiple winners"""
        if not comments_data or not comments_data.get('comments'):
            print("⚠️ Skipping multiple winners test - no comments data available")
            return False

        success, response = self.run_test(
            "Pick Winners - Multiple",
            "POST",
            "api/youtube/pick-winners",
            200,
            data={
                "comments": comments_data['comments'][:20],  # Use first 20 comments
                "exclude_duplicates": True,
                "winner_count": 3
            }
        )
        
        if success and response.get('winners'):
            if len(response['winners']) == 3:
                print(f"✅ Multiple winners selected correctly")
                return True
            else:
                print(f"❌ Expected 3 winners, got {len(response['winners'])}")
        return False

    def test_pick_winners_with_keyword_filter(self, comments_data):
        """Test winner picking with keyword filter"""
        if not comments_data or not comments_data.get('comments'):
            print("⚠️ Skipping keyword filter test - no comments data available")
            return False

        success, response = self.run_test(
            "Pick Winners - Keyword Filter",
            "POST",
            "api/youtube/pick-winners",
            200,
            data={
                "comments": comments_data['comments'],
                "exclude_duplicates": True,
                "keyword_filter": "good,great,awesome,love",  # Common positive words
                "winner_count": 1
            }
        )
        
        if success:
            print(f"✅ Keyword filter applied successfully")
            print(f"Eligible comments with keywords: {response.get('total_eligible', 0)}")
            return True
        return False

    def test_pick_winners_no_eligible_comments(self, comments_data):
        """Test winner picking when no comments match criteria"""
        if not comments_data or not comments_data.get('comments'):
            print("⚠️ Skipping no eligible comments test - no comments data available")
            return False

        success, response = self.run_test(
            "Pick Winners - No Eligible Comments",
            "POST",
            "api/youtube/pick-winners",
            400,  # Should return error when no eligible comments
            data={
                "comments": comments_data['comments'][:5],
                "exclude_duplicates": True,
                "keyword_filter": "veryrarewordthatwontmatch12345",  # Very unlikely to match
                "winner_count": 1
            }
        )
        return success

    def test_pick_winners_exclude_duplicates(self, comments_data):
        """Test duplicate exclusion functionality"""
        if not comments_data or not comments_data.get('comments'):
            print("⚠️ Skipping duplicate exclusion test - no comments data available")
            return False

        # Create test data with duplicate authors
        test_comments = comments_data['comments'][:5]
        if len(test_comments) >= 2:
            # Make second comment have same author as first
            test_comments[1]['author'] = test_comments[0]['author']

        success_with_duplicates, response_with = self.run_test(
            "Pick Winners - With Duplicates",
            "POST",
            "api/youtube/pick-winners",
            200,
            data={
                "comments": test_comments,
                "exclude_duplicates": False,
                "winner_count": 5
            }
        )

        success_without_duplicates, response_without = self.run_test(
            "Pick Winners - Exclude Duplicates",
            "POST",
            "api/youtube/pick-winners",
            200,
            data={
                "comments": test_comments,
                "exclude_duplicates": True,
                "winner_count": 5
            }
        )

        if success_with_duplicates and success_without_duplicates:
            eligible_with = response_with.get('total_eligible', 0)
            eligible_without = response_without.get('total_eligible', 0)
            print(f"Eligible with duplicates: {eligible_with}")
            print(f"Eligible without duplicates: {eligible_without}")
            
            if eligible_without <= eligible_with:
                print(f"✅ Duplicate exclusion working correctly")
                return True
            else:
                print(f"❌ Duplicate exclusion not working properly")
        
        return False

def main():
    print("🚀 Starting YouTube Comment Picker API Tests")
    print("=" * 60)
    
    tester = YouTubeCommentPickerTester()
    
    # Test 1: Fetch comments from valid video
    print("\n📹 Testing Comment Fetching...")
    comments_data = tester.test_fetch_comments_valid_video()
    
    # Test 2: Invalid URL handling
    tester.test_fetch_comments_invalid_url()
    
    # Test 3: Non-existent video handling
    tester.test_fetch_comments_nonexistent_video()
    
    # Test 4-8: Winner picking tests (only if we have comments)
    if comments_data:
        print("\n🏆 Testing Winner Picking...")
        winner_data = tester.test_pick_winners_basic(comments_data)
        tester.test_pick_winners_multiple(comments_data)
        tester.test_pick_winners_with_keyword_filter(comments_data)
        tester.test_pick_winners_no_eligible_comments(comments_data)
        tester.test_pick_winners_exclude_duplicates(comments_data)
    else:
        print("\n⚠️ Skipping winner picking tests - no valid comments data")
    
    # Print final results
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        failed_tests = [test for test in tester.test_results if not test['success']]
        print(f"Failed tests: {[test['name'] for test in failed_tests]}")
        return 1

if __name__ == "__main__":
    sys.exit(main())