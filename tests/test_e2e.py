"""
End-to-End Tests for LocalMind

These tests verify the complete user flow from request to response,
including web interface interactions, API calls, and model responses.
"""

import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from src.web.server import WebServer
from src.utils.config import ConfigManager
from src.core.model_loader import ModelLoader
from src.backends.base import ModelResponse


@pytest.fixture
def config_manager():
    """Create a test config manager."""
    return ConfigManager()


@pytest.fixture
def web_server(config_manager):
    """Create a test web server."""
    server = WebServer(config_manager, host="127.0.0.1", port=5002)
    return server


@pytest.fixture
def client(web_server):
    """Create a test client."""
    web_server.app.config['TESTING'] = True
    return web_server.app.test_client()


@pytest.fixture
def mock_model_response():
    """Create a mock model response."""
    return ModelResponse(
        text="This is a test response",
        metadata={
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15
        }
    )


class TestE2EWebInterface:
    """End-to-end tests for web interface"""
    
    def test_homepage_loads(self, client):
        """Test that the homepage loads successfully."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'LocalMind' in response.data or b'localmind' in response.data.lower()
    
    def test_status_endpoint(self, client):
        """Test the status API endpoint."""
        response = client.get('/api/status')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'status' in data
    
    def test_models_list_endpoint(self, client):
        """Test the models list API endpoint."""
        response = client.get('/api/models')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'status' in data
        if data['status'] == 'ok':
            assert 'models' in data
    
    @patch('src.web.server.ModelLoader')
    def test_chat_endpoint_complete_flow(self, mock_loader_class, client, mock_model_response):
        """Test complete chat flow from request to response."""
        # Mock the model loader
        mock_loader = Mock()
        mock_loader.generate.return_value = mock_model_response
        mock_loader.list_available_models.return_value = {'ollama': ['llama3']}
        mock_loader_class.return_value = mock_loader
        
        # Create a new server with mocked loader
        config_manager = ConfigManager()
        server = WebServer(config_manager, host="127.0.0.1", port=5003)
        server.model_loader = mock_loader
        server.app.config['TESTING'] = True
        test_client = server.app.test_client()
        
        # Send chat request
        response = test_client.post('/api/chat', json={
            'prompt': 'Hello, how are you?',
            'model': 'llama3',
            'temperature': 0.7
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'ok'
        assert 'response' in data['data']
        assert 'This is a test response' in data['data']['response']
        
        # Verify model loader was called
        mock_loader.generate.assert_called_once()
    
    def test_model_comparison_flow(self, client):
        """Test model comparison end-to-end flow."""
        with patch('src.web.server.ModelLoader') as mock_loader_class:
            mock_loader = Mock()
            mock_response = ModelResponse(
                text="Comparison response",
                metadata={"prompt_tokens": 5, "completion_tokens": 3}
            )
            mock_loader.generate.return_value = mock_response
            mock_loader.list_available_models.return_value = {
                'ollama': ['llama3', 'mistral']
            }
            mock_loader_class.return_value = mock_loader
            
            config_manager = ConfigManager()
            server = WebServer(config_manager, host="127.0.0.1", port=5004)
            server.model_loader = mock_loader
            server.app.config['TESTING'] = True
            test_client = server.app.test_client()
            
            # Send comparison request
            response = test_client.post('/api/chat/compare', json={
                'prompt': 'Compare these models',
                'models': ['llama3', 'mistral'],
                'temperature': 0.7
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'ok'
            assert 'results' in data['data']
            assert len(data['data']['results']) == 2
    
    def test_ensemble_flow(self, client):
        """Test ensemble response end-to-end flow."""
        with patch('src.web.server.ModelLoader') as mock_loader_class:
            mock_loader = Mock()
            mock_response = ModelResponse(
                text="Ensemble response",
                metadata={"prompt_tokens": 5, "completion_tokens": 3}
            )
            mock_loader.generate.return_value = mock_response
            mock_loader.list_available_models.return_value = {
                'ollama': ['llama3', 'mistral']
            }
            mock_loader_class.return_value = mock_loader
            
            config_manager = ConfigManager()
            server = WebServer(config_manager, host="127.0.0.1", port=5005)
            server.model_loader = mock_loader
            server.app.config['TESTING'] = True
            test_client = server.app.test_client()
            
            # Send ensemble request
            response = test_client.post('/api/chat/ensemble', json={
                'prompt': 'Generate ensemble response',
                'models': ['llama3', 'mistral'],
                'method': 'majority_vote',
                'temperature': 0.7
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'ok'
            assert 'response' in data['data']
            assert 'method' in data['data']
    
    def test_model_routing_flow(self, client):
        """Test model routing end-to-end flow."""
        with patch('src.web.server.ModelLoader') as mock_loader_class:
            mock_loader = Mock()
            mock_loader.list_available_models.return_value = {
                'ollama': ['llama3', 'codellama'],
                'openai': ['gpt-3.5-turbo']
            }
            mock_loader_class.return_value = mock_loader
            
            config_manager = ConfigManager()
            server = WebServer(config_manager, host="127.0.0.1", port=5006)
            server.model_loader = mock_loader
            server.app.config['TESTING'] = True
            test_client = server.app.test_client()
            
            # Test code task routing
            response = test_client.post('/api/chat/route', json={
                'prompt': 'Write a Python function to calculate factorial'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'ok'
            assert 'recommended_model' in data['data']
            assert 'detected_task' in data['data']
            assert data['data']['detected_task'] == 'code'
    
    def test_auto_model_selection_flow(self, client):
        """Test automatic model selection flow."""
        with patch('src.web.server.ModelLoader') as mock_loader_class:
            mock_loader = Mock()
            mock_loader.list_available_models.return_value = {
                'ollama': ['llama3', 'mistral'],
                'openai': ['gpt-3.5-turbo']
            }
            mock_loader_class.return_value = mock_loader
            
            config_manager = ConfigManager()
            server = WebServer(config_manager, host="127.0.0.1", port=5007)
            server.model_loader = mock_loader
            server.app.config['TESTING'] = True
            test_client = server.app.test_client()
            
            # Test auto-select
            response = test_client.get('/api/models/auto-select')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'ok'
            assert 'selected_model' in data['data']
            assert data['data']['selected_model'] is not None


class TestE2EConversationFlow:
    """End-to-end tests for conversation management"""
    
    def test_create_and_load_conversation(self, client):
        """Test creating and loading a conversation."""
        with patch('src.web.server.ModelLoader') as mock_loader_class:
            mock_loader = Mock()
            mock_loader.list_available_models.return_value = {'ollama': ['llama3']}
            mock_loader_class.return_value = mock_loader
            
            config_manager = ConfigManager()
            server = WebServer(config_manager, host="127.0.0.1", port=5008)
            server.model_loader = mock_loader
            server.app.config['TESTING'] = True
            test_client = server.app.test_client()
            
            # Create conversation
            response = test_client.post('/api/conversations', json={
                'model': 'llama3',
                'title': 'Test Conversation'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'ok'
            conv_id = data['data']['conversation_id']
            
            # Load conversation
            response = test_client.get(f'/api/conversations/{conv_id}')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'ok'
            assert data['data']['conversation']['model'] == 'llama3'
    
    def test_conversation_with_context(self, client):
        """Test conversation with context management."""
        with patch('src.web.server.ModelLoader') as mock_loader_class:
            mock_loader = Mock()
            mock_response = ModelResponse(
                text="Context-aware response",
                metadata={"prompt_tokens": 10, "completion_tokens": 5}
            )
            mock_loader.generate.return_value = mock_response
            mock_loader.list_available_models.return_value = {'ollama': ['llama3']}
            mock_loader_class.return_value = mock_loader
            
            config_manager = ConfigManager()
            server = WebServer(config_manager, host="127.0.0.1", port=5009)
            server.model_loader = mock_loader
            server.app.config['TESTING'] = True
            test_client = server.app.test_client()
            
            # First message
            response = test_client.post('/api/chat', json={
                'prompt': 'My name is Alice',
                'model': 'llama3'
            })
            assert response.status_code == 200
            data = json.loads(response.data)
            conv_id = data['data']['conversation_id']
            
            # Second message with context
            response = test_client.post('/api/chat', json={
                'prompt': 'What is my name?',
                'model': 'llama3',
                'conversation_id': conv_id
            })
            assert response.status_code == 200
            # Context should be maintained
            assert mock_loader.generate.call_count == 2


class TestE2EResourceManagement:
    """End-to-end tests for resource management features"""
    
    def test_usage_statistics_flow(self, client):
        """Test usage statistics tracking flow."""
        config_manager = ConfigManager()
        server = WebServer(config_manager, host="127.0.0.1", port=5010)
        server.app.config['TESTING'] = True
        test_client = server.app.test_client()
        
        # Get usage statistics
        response = test_client.get('/api/usage/statistics')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'ok'
        assert 'data' in data
    
    def test_resource_monitoring_flow(self, client):
        """Test resource monitoring flow."""
        config_manager = ConfigManager()
        server = WebServer(config_manager, host="127.0.0.1", port=5011)
        server.app.config['TESTING'] = True
        test_client = server.app.test_client()
        
        # Get resource usage
        response = test_client.get('/api/resources')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'ok'
        assert 'cpu' in data['data'] or 'memory' in data['data']
    
    def test_cleanup_flow(self, client):
        """Test resource cleanup flow."""
        config_manager = ConfigManager()
        server = WebServer(config_manager, host="127.0.0.1", port=5012)
        server.app.config['TESTING'] = True
        test_client = server.app.test_client()
        
        # Get cleanup stats
        response = test_client.get('/api/cleanup/stats')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'ok'


class TestE2EErrorHandling:
    """End-to-end tests for error handling"""
    
    def test_invalid_model_error(self, client):
        """Test error handling for invalid model."""
        with patch('src.web.server.ModelLoader') as mock_loader_class:
            mock_loader = Mock()
            mock_loader.generate.side_effect = ValueError("Model not found")
            mock_loader.list_available_models.return_value = {'ollama': ['llama3']}
            mock_loader_class.return_value = mock_loader
            
            config_manager = ConfigManager()
            server = WebServer(config_manager, host="127.0.0.1", port=5013)
            server.model_loader = mock_loader
            server.app.config['TESTING'] = True
            test_client = server.app.test_client()
            
            response = test_client.post('/api/chat', json={
                'prompt': 'Test',
                'model': 'invalid-model'
            })
            
            # Should handle error gracefully
            assert response.status_code in [200, 400, 500]
            data = json.loads(response.data)
            # Either success with error message or proper error response
            assert 'status' in data
    
    def test_missing_prompt_error(self, client):
        """Test error handling for missing prompt."""
        config_manager = ConfigManager()
        server = WebServer(config_manager, host="127.0.0.1", port=5014)
        server.app.config['TESTING'] = True
        test_client = server.app.test_client()
        
        response = test_client.post('/api/chat', json={
            'model': 'llama3'
        })
        
        assert response.status_code in [400, 422]
        data = json.loads(response.data)
        assert data['status'] == 'error' or 'error' in data


class TestE2EIntegration:
    """End-to-end integration tests"""
    
    def test_full_user_journey(self, client):
        """Test a complete user journey from start to finish."""
        with patch('src.web.server.ModelLoader') as mock_loader_class:
            mock_loader = Mock()
            mock_response = ModelResponse(
                text="Hello! I'm here to help.",
                metadata={"prompt_tokens": 5, "completion_tokens": 8}
            )
            mock_loader.generate.return_value = mock_response
            mock_loader.list_available_models.return_value = {
                'ollama': ['llama3'],
                'openai': ['gpt-3.5-turbo']
            }
            mock_loader_class.return_value = mock_loader
            
            config_manager = ConfigManager()
            server = WebServer(config_manager, host="127.0.0.1", port=5015)
            server.model_loader = mock_loader
            server.app.config['TESTING'] = True
            test_client = server.app.test_client()
            
            # 1. Check status
            response = test_client.get('/api/status')
            assert response.status_code == 200
            
            # 2. List models
            response = test_client.get('/api/models')
            assert response.status_code == 200
            
            # 3. Auto-select model
            response = test_client.get('/api/models/auto-select')
            assert response.status_code == 200
            selected_model = json.loads(response.data)['data']['selected_model']
            
            # 4. Route to best model for task
            response = test_client.post('/api/chat/route', json={
                'prompt': 'Write a Python function'
            })
            assert response.status_code == 200
            
            # 5. Send chat message
            response = test_client.post('/api/chat', json={
                'prompt': 'Hello!',
                'model': selected_model
            })
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'ok'
            assert 'response' in data['data']
            
            # 6. Get usage statistics
            response = test_client.get('/api/usage/statistics')
            assert response.status_code == 200
            
            # 7. Get resource usage
            response = test_client.get('/api/resources')
            assert response.status_code == 200

