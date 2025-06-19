import os
import requests
from typing import Optional, Dict, Any
from dotenv import load_dotenv


class IFTTTNotifier:
    """
    A library for sending notifications via IFTTT webhooks.
    
    Usage:
        # Using environment variable
        notifier = IFTTTNotifier()
        
        # Using explicit webhook URL
        notifier = IFTTTNotifier(webhook_url="your_webhook_url_here")
        
        # Send notification
        notifier.send_notification(
            title="Alert!",
            message="Something happened",
            url="https://example.com",
            image_url="https://example.com/image.jpg"
        )
    """
    
    def __init__(self, webhook_url: Optional[str] = None, load_env: bool = True):
        """
        Initialize the IFTTT notifier.
        
        Args:
            webhook_url: IFTTT webhook URL. If None, will try to load from environment.
            load_env: Whether to load environment variables from .env file.
        """
        if load_env:
            load_dotenv()
            
        self.webhook_url = webhook_url or os.getenv('IFTTT_WEBHOOK_URL')
        self.default_image_url = os.getenv('TRELLO_RICH_IMAGE_URL')

        if not self.webhook_url:
            raise ValueError(
                "IFTTT_WEBHOOK_URL must be provided either as parameter or "
                "environment variable."
            )
    
    def send_notification(
        self, 
        title: str,
        message: str,
        url: Optional[str] = None,
        image_url: Optional[str] = None,
        custom_data: Optional[Dict[str, Any]] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Send a notification via IFTTT webhook.
        
        Args:
            title: Notification title
            message: Notification message
            url: Optional URL to include
            image_url: Optional image URL
            custom_data: Additional custom data to send
            timeout: Request timeout in seconds
            
        Returns:
            Dict containing success status and response details
        """
        # Build the data payload
        data = {
            "title": title,
            "message": message
        }
        
        # Add optional fields
        if url:
            data["link_url"] = url
        if image_url:
            data["image_url"] = image_url
        else:
            # Use default image URL if not provided
            if self.default_image_url:
                data["image_url"] = self.default_image_url
        if custom_data:
            data.update(custom_data)
        
        try:
            response = requests.post(
                self.webhook_url, 
                json=data, 
                timeout=timeout
            )
            
            success = response.status_code == 200
            
            return {
                "success": success,
                "status_code": response.status_code,
                "response_text": response.text,
                "data_sent": data
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "data_sent": data
            }
    
    def send_simple_notification(self, title: str, message: str) -> bool:
        """
        Send a simple notification with just title and message.
        
        Args:
            title: Notification title
            message: Notification message
            
        Returns:
            True if successful, False otherwise
        """
        result = self.send_notification(title, message)
        return result["success"]


# Convenience functions for quick usage
def send_notification(
    title: str,
    message: str,
    url: Optional[str] = None,
    image_url: Optional[str] = None,
    webhook_url: Optional[str] = None,
    custom_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Quick function to send a notification without creating a class instance.
    
    Args:
        title: Notification title
        message: Notification message
        url: Optional URL to include
        image_url: Optional image URL
        webhook_url: IFTTT webhook URL (uses env var if None)
        custom_data: Additional custom data to send
        
    Returns:
        Dict containing success status and response details
    """
    notifier = IFTTTNotifier(webhook_url=webhook_url)
    return notifier.send_notification(
        title=title,
        message=message,
        url=url,
        image_url=image_url,
        custom_data=custom_data
    )


def send_simple_notification(title: str, message: str, webhook_url: Optional[str] = None) -> bool:
    """
    Quick function to send a simple notification.
    
    Args:
        title: Notification title
        message: Notification message
        webhook_url: IFTTT webhook URL (uses env var if None)
        
    Returns:
        True if successful, False otherwise
    """
    notifier = IFTTTNotifier(webhook_url=webhook_url)
    return notifier.send_simple_notification(title, message)


# Example usage
if __name__ == "__main__":
    # Example 1: Using the class
    try:
        notifier = IFTTTNotifier()
        
        result = notifier.send_notification(
            title="Test Notification",
            message="This is a test message from the library",
            url="https://example.com",
            image_url="https://example.com/image.jpg"
        )
        
        if result["success"]:
            print("✅ Notification sent successfully!")
        else:
            print(f"❌ Failed to send notification: {result}")
            
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
    
    # Example 2: Using convenience function
    success = send_simple_notification(
        title="Quick Alert",
        message="This was sent using the convenience function"
    )
    
    if success:
        print("✅ Quick notification sent!")
    else:
        print("❌ Quick notification failed!")