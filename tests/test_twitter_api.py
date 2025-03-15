import pytest
from flask import Flask, current_app
import requests
import json
import time
import websocket
from unittest.mock import patch, MagicMock, call
from cachetools import TTLCache

# You'll need to adjust this import path to match your actual module structure
from twitter_analyzer.api_management.t import TwitterAPI

# Mock the key_manager to avoid external dependencies
@pytest.fixture(autouse=True)
def mock_key_manager():
    with patch("twitter_analyzer.api_management.twitter_api.get_api_key_manager") as mock:
        mock.return_value = None
        yield mock

# Flask app fixture
@pytest.fixture
def app():
    app = Flask(__name__)
    app.config.update({
        "TESTING": True,
        "TWITTER_API_KEY": "test_key",
        "TWITTER_CACHE_SIZE": 100,
        "TWITTER_CACHE_TTL": 60,
        "TWITTER_API_MAX_RETRIES": 3,
        "TWITTER_API_BASE_RETRY_DELAY": 0.01,  # Small for fast tests
        "TWITTER_API_MAX_RETRY_DELAY": 0.05,
        "TWITTER_API_CONNECT_TIMEOUT": 1,
        "TWITTER_API_READ_TIMEOUT": 2,
    })
    
    # Yield app with active app context as per Flask documentation
    with app.app_context():
        yield app

# TwitterAPI fixture initialized with app directly
@pytest.fixture
def twitter_api_with_app(app):
    api = TwitterAPI(app)
    return api

# TwitterAPI fixture initialized with init_app
@pytest.fixture
def twitter_api_init_app(app):
    api = TwitterAPI()
    api.init_app(app)
    return api

# Mocked session fixture
@pytest.fixture
def mock_session():
    with patch("requests.Session") as mock_session_class:
        session = MagicMock()
        mock_session_class.return_value = session
        
        # Configure default mock response
        response = MagicMock()
        response.status_code = 200
        response.headers = {
            "X-Rate-Limit-Limit": "200",
            "X-Rate-Limit-Remaining": "199",
            "X-Rate-Limit-Reset": str(int(time.time()) + 3600)
        }
        response.json.return_value = {"status": "ok", "data": []}
        session.request.return_value = response
        
        yield session

# Tests for initialization patterns
def test_init_with_app(app, mock_session):
    """Test direct initialization with app parameter"""
    api = TwitterAPI(app)
    
    assert api.api_key == "test_key"
    assert isinstance(api.cache, TTLCache)
    assert api.cache.maxsize == 100
    assert api.cache.ttl == 60
    assert api.max_retries == 3
    assert 'twitter_api' in app.extensions
    assert app.extensions['twitter_api'] == api

def test_init_app_pattern(app, mock_session):
    """Test Flask factory pattern with init_app"""
    api = TwitterAPI()
    api.init_app(app)
    
    assert api.api_key == "test_key"
    assert isinstance(api.cache, TTLCache)
    assert api.cache.maxsize == 100
    assert api.cache.ttl == 60
    assert api.max_retries == 3
    assert 'twitter_api' in app.extensions
    assert app.extensions['twitter_api'] == api

def test_access_through_current_app(app, twitter_api_with_app):
    """Test access to extension through current_app"""
    assert 'twitter_api' in current_app.extensions
    assert current_app.extensions['twitter_api'] == twitter_api_with_app

# Test basic API calls
def test_get_user_info(twitter_api_with_app, mock_session):
    """Test a basic API call (get_user_info)"""
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"status": "ok", "user": {"id": "123", "name": "Test User"}}
    response.headers = {"X-Rate-Limit-Remaining": "199"}
    
    mock_session.request.return_value = response
    
    result = twitter_api_with_app.get_user_info("testuser")
    
    mock_session.request.assert_called_once()
    args, kwargs = mock_session.request.call_args
    assert kwargs["method"] == "GET"
    assert kwargs["url"] == "https://api.twitterapi.io/twitter/user/info"
    assert kwargs["params"] == {"userName": "testuser"}
    assert result == {"status": "ok", "user": {"id": "123", "name": "Test User"}}

def test_search_tweets(twitter_api_with_app, mock_session):
    """Test search_tweets functionality"""
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {
        "status": "ok", 
        "tweets": [
            {"id": "1", "text": "Test tweet 1"},
            {"id": "2", "text": "Test tweet 2"}
        ],
        "has_next_page": True,
        "next_cursor": "next_page_token"
    }
    response.headers = {"X-Rate-Limit-Remaining": "199"}
    
    mock_session.request.return_value = response
    
    result = twitter_api_with_app.search_tweets("test query")
    
    mock_session.request.assert_called_once()
    args, kwargs = mock_session.request.call_args
    assert kwargs["method"] == "GET"
    assert kwargs["url"] == "https://api.twitterapi.io/twitter/tweet/advanced_search"
    assert kwargs["params"] == {"query": "test query", "queryType": "Latest", "cursor": ""}
    assert result["has_next_page"] == True
    assert result["next_cursor"] == "next_page_token"
    assert len(result["tweets"]) == 2

# Test error handling
def test_http_error_handling(twitter_api_with_app, mock_session):
    """Test handling of HTTP errors"""
    response = MagicMock()
    response.status_code = 404
    response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
    response.text = '{"error": "Resource not found"}'
    try:
        response.json.return_value = {"error": "Resource not found"}
    except Exception:
        pass  # Handle case where json() might raise an error in real code
    response.headers = {"X-Rate-Limit-Remaining": "199"}
    
    mock_session.request.return_value = response
    
    result = twitter_api_with_app.get_user_info("nonexistent")
    
    assert result["status"] == "error"
    assert "Resource not found" in result["msg"] or result["msg"] == "Resource not found"

def test_retry_logic(twitter_api_with_app, mock_session):
    """Test the retry mechanism for failed requests"""
    # First two responses fail, third succeeds
    response_fail = MagicMock()
    response_fail.status_code = 500
    response_fail.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Server Error")
    response_fail.headers = {"X-Rate-Limit-Remaining": "199"}
    
    response_success = MagicMock()
    response_success.status_code = 200
    response_success.json.return_value = {"status": "ok", "data": "success"}
    response_success.headers = {"X-Rate-Limit-Remaining": "199"}
    
    mock_session.request.side_effect = [response_fail, response_fail, response_success]
    
    # With minimal retry delay for testing
    result = twitter_api_with_app.get_user_info("testuser")
    
    assert mock_session.request.call_count == 3
    assert result == {"status": "ok", "data": "success"}

# Test rate limit handling
def test_rate_limit_handling(twitter_api_with_app, mock_session, mock_key_manager):
    """Test handling of API rate limits"""
    key_manager = MagicMock()
    mock_key_manager.return_value = key_manager
    key_manager.get_next_key.return_value = "new_test_key"
    
    # Response that indicates rate limit reached
    rate_limited_response = MagicMock()
    rate_limited_response.status_code = 429
    rate_limited_response.headers = {
        "X-Rate-Limit-Limit": "100",
        "X-Rate-Limit-Remaining": "0",
        "X-Rate-Limit-Reset": str(int(time.time()) + 60),
        "Retry-After": "1"
    }
    
    # Success response after switching keys
    success_response = MagicMock()
    success_response.status_code = 200
    success_response.json.return_value = {"status": "ok", "data": "success"}
    success_response.headers = {"X-Rate-Limit-Remaining": "99"}
    
    mock_session.request.side_effect = [rate_limited_response, success_response]
    
    result = twitter_api_with_app.get_user_info("testuser")
    
    assert key_manager.get_next_key.called
    assert mock_session.request.call_count == 2
    assert result == {"status": "ok", "data": "success"}
    # Original key should be restored after the request completes
    assert twitter_api_with_app.api_key == "test_key"

# Test caching behavior
def test_caching_mechanism(twitter_api_with_app, mock_session):
    """Test that the cache works correctly"""
    # First response
    first_response = MagicMock()
    first_response.status_code = 200
    first_response.json.return_value = {"status": "ok", "user": {"id": "123", "name": "Test User"}}
    first_response.headers = {"X-Rate-Limit-Remaining": "199"}
    
    # Second response (should not be used due to caching)
    second_response = MagicMock()
    second_response.status_code = 200
    second_response.json.return_value = {"status": "ok", "user": {"id": "123", "name": "Updated User"}}
    second_response.headers = {"X-Rate-Limit-Remaining": "198"}
    
    mock_session.request.side_effect = [first_response, second_response]
    
    # First call should use API
    result1 = twitter_api_with_app.get_user_info("testuser")
    assert result1 == {"status": "ok", "user": {"id": "123", "name": "Test User"}}
    
    # Second call should use cache
    result2 = twitter_api_with_app.get_user_info("testuser")
    assert result2 == {"status": "ok", "user": {"id": "123", "name": "Test User"}}
    
    # Should only have made one request to the API
    assert mock_session.request.call_count == 1
    
    # Test cache clearing
    twitter_api_with_app.clear_cache()
    result3 = twitter_api_with_app.get_user_info("testuser")
    assert result3 == {"status": "ok", "user": {"id": "123", "name": "Updated User"}}
    assert mock_session.request.call_count == 2

def test_cache_pattern_clearing(twitter_api_with_app, mock_session):
    """Test clearing cache by pattern"""
    # Setup cache with multiple entries
    twitter_api_with_app.cache["user_info_user1"] = {"data": "user1_data"}
    twitter_api_with_app.cache["user_info_user2"] = {"data": "user2_data"}
    twitter_api_with_app.cache["tweet_data_123"] = {"data": "tweet_data"}
    
    # Clear only user info cache
    count = twitter_api_with_app.clear_cache_by_pattern("user_info_")
    
    assert count == 2
    assert "user_info_user1" not in twitter_api_with_app.cache
    assert "user_info_user2" not in twitter_api_with_app.cache
    assert "tweet_data_123" in twitter_api_with_app.cache

# Test helper methods
def test_parse_tweet_data(twitter_api_with_app):
    """Test tweet data parsing"""
    tweet_data = {
        "id": "12345",
        "text": "This is a #test tweet with @mention",
        "createdAt": "2023-01-01T12:00:00Z",
        "likeCount": 10,
        "retweetCount": 5,
        "replyCount": 2,
        "quoteCount": 1,
        "viewCount": 100,
        "author": {
            "id": "user123",
            "userName": "testuser",
            "name": "Test User",
            "profilePicture": "http://example.com/pic.jpg",
            "followers": 1000,
            "following": 500,
            "isBlueVerified": True
        },
        "entities": {
            "hashtags": [{"text": "test"}],
            "user_mentions": [{"screen_name": "mention"}],
            "urls": [{"url": "http://t.co/short", "expanded_url": "http://example.com"}]
        }
    }
    
    parsed = twitter_api_with_app.parse_tweet_data(tweet_data)
    
    assert parsed["id"] == "12345"
    assert parsed["text"] == "This is a #test tweet with @mention"
    assert parsed["created_at"] == "2023-01-01T12:00:00Z"
    assert parsed["likes_count"] == 10
    assert parsed["author"]["username"] == "testuser"
    assert parsed["hashtags"] == ["test"]
    assert parsed["mentions"] == ["mention"]
    assert parsed["urls"] == ["http://example.com"]

def test_batch_process_tweets(twitter_api_with_app):
    """Test the batch processing of tweets"""
    tweets = [
        {"id": "1", "text": "Tweet 1", "author": {"userName": "user1"}},
        {"id": "2", "text": "Tweet 2", "author": {"userName": "user2"}},
        {"id": "3", "text": "Tweet 3", "author": {"userName": "user3"}}
    ]
    
    with patch.object(twitter_api_with_app, "parse_tweet_data") as mock_parse:
        mock_parse.side_effect = lambda t: {"id": t["id"], "processed": True}
        
        result = twitter_api_with_app.batch_process_tweets(tweets)
        
        assert len(result) == 3
        assert all(tweet["processed"] for tweet in result)
        assert mock_parse.call_count == 3

# Test websocket integration
def test_websocket_integration(twitter_api_with_app):
    """Test websocket connection creation and management"""
    with patch("websocket.WebSocketApp") as mock_websocket, \
         patch("threading.Thread") as mock_thread:
        
        mock_ws = MagicMock()
        mock_websocket.return_value = mock_ws
        
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        
        callback = MagicMock()
        
        ws = twitter_api_with_app.create_websocket_connection("rule_id_123", callback)
        
        assert mock_websocket.called
        assert "rule_id_123" in twitter_api_with_app.websocket_connections
        assert twitter_api_with_app.websocket_connections["rule_id_123"] == mock_ws
        assert mock_thread.called
        assert mock_thread_instance.start.called
        
        # Test closing the connection
        twitter_api_with_app.close_websocket_connection("rule_id_123")
        assert mock_ws.close.called
        assert "rule_id_123" not in twitter_api_with_app.websocket_connections

# Test Flask context management
def test_app_context_teardown(app, twitter_api_with_app):
    """Test cleanup during application context teardown"""
    with patch.object(twitter_api_with_app, "close_websocket_connection") as mock_close:
        # Create mock websocket connections
        twitter_api_with_app.websocket_connections = {
            "rule1": MagicMock(),
            "rule2": MagicMock()
        }
        
        # Trigger teardown function that should be registered
        app.teardown_appcontext_funcs[0](Exception("Test exception"))
        
        # Check that connections were closed properly
        assert mock_close.call_count == 2
        mock_close.assert_has_calls([call("rule1"), call("rule2")], any_order=True)

# Test pagination utilities
def test_get_all_user_tweets(twitter_api_with_app):
    """Test the retrieval of all tweets with pagination handling"""
    with patch.object(twitter_api_with_app, "get_user_tweets") as mock_get_tweets:
        # Setup mock to return different pages of results
        mock_get_tweets.side_effect = [
            # First page
            {
                "tweets": [{"id": "1", "text": "Tweet 1"}, {"id": "2", "text": "Tweet 2"}],
                "has_next_page": True,
                "next_cursor": "cursor2"
            },
            # Second page
            {
                "tweets": [{"id": "3", "text": "Tweet 3"}, {"id": "4", "text": "Tweet 4"}],
                "has_next_page": True,
                "next_cursor": "cursor3"
            },
            # Third page
            {
                "tweets": [{"id": "5", "text": "Tweet 5"}],
                "has_next_page": False
            }
        ]
        
        # Call method with pagination
        results = twitter_api_with_app.get_all_user_tweets(username="testuser", max_pages=3)
        
        # Verify results
        assert len(results) == 5
        assert results[0]["id"] == "1"
        assert results[4]["id"] == "5"
        
        # Verify proper cursor passing
        assert mock_get_tweets.call_count == 3
        mock_get_tweets.assert_has_calls([
            call(username="testuser", user_id=None, include_replies=False, cursor=""),
            call(username="testuser", user_id=None, include_replies=False, cursor="cursor2"),
            call(username="testuser", user_id=None, include_replies=False, cursor="cursor3")
        ])

# Test streaming - this simulates long-running behavior
def test_stream_tweets_by_query(twitter_api_with_app):
    """Test the streaming mechanism for tweets"""
    with patch.object(twitter_api_with_app, "search_tweets") as mock_search, \
         patch.object(twitter_api_with_app, "parse_tweet_data", side_effect=lambda x: x), \
         patch("time.sleep") as mock_sleep, \
         patch("time.time") as mock_time:
        
        # Setup time to control the loop iterations
        mock_time.side_effect = [0, 30, 61]  # Start, middle, end
        
        # Setup mock search results for two iterations
        mock_search.side_effect = [
            # First call
            {
                "tweets": [
                    {"id": "1", "text": "First tweet"}
                ]
            },
            # Second call - new tweet appears
            {
                "tweets": [
                    {"id": "2", "text": "New tweet"},
                    {"id": "1", "text": "First tweet"}
                ]
            }
        ]
        
        # Setup callback to track tweets received
        callback = MagicMock()
        
        # Run streaming with short interval
        twitter_api_with_app.stream_tweets_by_query(
            "test query", callback, interval=0.001, max_time=60
        )
        
        # Should have called search twice and gotten callbacks for both tweets
        assert mock_search.call_count == 2
        assert callback.call_count == 2
        
        # First we see tweet 1, then tweet 2 in the next poll
        callback.assert_has_calls([
            call({"id": "1", "text": "First tweet"}),
            call({"id": "2", "text": "New tweet"})
        ])