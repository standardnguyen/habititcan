import requests
import json
from typing import Optional, Dict, Any

class StackClient:
    """
    A wrapper class for interacting with the Stack Server
    """
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        """
        Initialize the Stack Client
        
        Args:
            base_url: The base URL of the stack server (default: http://localhost:5000)
        """
        self.base_url = base_url.rstrip('/')
        self.stack_endpoint = f"{self.base_url}/stack"
        self.status_endpoint = f"{self.base_url}/stack/status"
        
        # Valid difficulty levels
        self.valid_levels = ['trivial', 'hard', 'easy', 'medium']
    
    def _send_post(self, level: str) -> Dict[Any, Any]:
        """
        Internal method to send POST request
        
        Args:
            level: The difficulty level to add to stack
            
        Returns:
            JSON response from server
            
        Raises:
            requests.RequestException: If request fails
            ValueError: If level is invalid
        """
        if level not in self.valid_levels:
            raise ValueError(f"Invalid level '{level}'. Must be one of: {self.valid_levels}")
        
        try:
            response = requests.post(
                self.stack_endpoint,
                json={'level': level},
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.ConnectionError:
            raise requests.RequestException(f"Could not connect to server at {self.base_url}")
        except requests.exceptions.Timeout:
            raise requests.RequestException("Request timed out")
        except requests.exceptions.RequestException as e:
            raise requests.RequestException(f"Request failed: {str(e)}")
    
    def add_trivial(self) -> Dict[Any, Any]:
        """Add 'trivial' to the stack"""
        return self._send_post('trivial')
    
    def add_easy(self) -> Dict[Any, Any]:
        """Add 'easy' to the stack"""
        return self._send_post('easy')
    
    def add_medium(self) -> Dict[Any, Any]:
        """Add 'medium' to the stack"""
        return self._send_post('medium')
    
    def add_hard(self) -> Dict[Any, Any]:
        """Add 'hard' to the stack"""
        return self._send_post('hard')
    
    def add_level(self, level: str) -> Dict[Any, Any]:
        """
        Add any valid level to the stack
        
        Args:
            level: The difficulty level ('trivial', 'easy', 'medium', 'hard')
            
        Returns:
            JSON response from server
        """
        return self._send_post(level)
    
    def get_and_clear_stack(self) -> Dict[Any, Any]:
        """
        Get the entire stack and clear it
        
        Returns:
            JSON response containing the stack contents
        """
        try:
            response = requests.get(self.stack_endpoint, timeout=10)
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.ConnectionError:
            raise requests.RequestException(f"Could not connect to server at {self.base_url}")
        except requests.exceptions.RequestException as e:
            raise requests.RequestException(f"Request failed: {str(e)}")
    
    def get_status(self) -> Dict[Any, Any]:
        """
        Get current stack status without clearing it
        
        Returns:
            JSON response containing current stack state
        """
        try:
            response = requests.get(self.status_endpoint, timeout=10)
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.ConnectionError:
            raise requests.RequestException(f"Could not connect to server at {self.base_url}")
        except requests.exceptions.RequestException as e:
            raise requests.RequestException(f"Request failed: {str(e)}")
    
    def is_server_running(self) -> bool:
        """
        Check if the server is running and accessible
        
        Returns:
            True if server is accessible, False otherwise
        """
        try:
            response = requests.get(self.status_endpoint, timeout=5)
            return response.status_code == 200
        except:
            return False

# Example usage and testing
if __name__ == "__main__":
    # Create client instance
    client = StackClient()
    
    # Check if server is running
    if not client.is_server_running():
        print("❌ Server is not running! Please start the stack server first.")
        exit(1)
    
    print("✅ Server is running!")
    print("\n--- Testing Stack Client ---")
    
    try:
        # Add some items to the stack
        print("\n📝 Adding items to stack:")
        
        result = client.add_easy()
        print(f"Added easy: {result['message']}")
        
        result = client.add_hard()
        print(f"Added hard: {result['message']}")
        
        result = client.add_trivial()
        print(f"Added trivial: {result['message']}")
        
        result = client.add_level('medium')
        print(f"Added medium: {result['message']}")
        
        # Check current status
        print("\n📊 Current stack status:")
        status = client.get_status()
        print(f"Stack: {status['current_stack']}")
        print(f"Size: {status['stack_size']}")
        
        # Get and clear the stack
        print("\n🗑️ Getting and clearing stack:")
        result = client.get_and_clear_stack()
        print(f"Retrieved stack: {result['stack']}")
        print(f"Stack size was: {result['stack_size']}")
        
        # Verify it's cleared
        print("\n✅ Verifying stack is cleared:")
        status = client.get_status()
        print(f"Current stack: {status['current_stack']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")