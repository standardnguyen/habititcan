"""
Trello List Monitor Library

A Python library for monitoring changes in Trello lists and retrieving card details.
"""

import requests
import time
import json
from typing import Dict, List, Set, Tuple, Optional
import os
from dotenv import load_dotenv
import random


class TrelloListMonitor:
    """
    A class to monitor Trello lists for changes and retrieve card details.
    
    This class provides functionality to:
    - Monitor a Trello list for added, removed, or modified cards
    - Compare card states between different time points
    - Retrieve detailed card information including custom fields
    """
    
    def __init__(self, list_id: Optional[str] = None):
        """
        Initialize the Trello List Monitor.
        
        Automatically loads credentials from .env file using:
        - TRELLO_API_KEY
        - TRELLO_API_TOKEN  
        - TRELLO_LIST_ID (if list_id not provided)
        
        Args:
            list_id (Optional[str]): The ID of the Trello list to monitor.
                                   If not provided, will use TRELLO_LIST_ID from .env
        """
        # Load environment variables from .env file
        load_dotenv()
        
        self.api_key = os.getenv("TRELLO_API_KEY")
        self.token = os.getenv("TRELLO_API_TOKEN")
        self.list_id = list_id or os.getenv("TRELLO_LIST_ID")
        
        if not self.api_key:
            raise ValueError("TRELLO_API_KEY not found in environment variables")
        if not self.token:
            raise ValueError("TRELLO_API_TOKEN not found in environment variables")
        if not self.list_id:
            raise ValueError("TRELLO_LIST_ID not provided and not found in environment variables")
            
        self.base_url = "https://api.trello.com/1"

        # we want to get the custom field for 'Alter' and the dictionary of alters
        self.alter_custom_field_id, self.alters = self.get_alter_info()


    def get_alter_info(self) -> Tuple[float, str]:
        print("fetching alter information...")
        custom_fields = self.get_custom_fields()

        alters = {}

        alter_custom_field_id = None
        for custom_field_id in custom_fields:
            custom_field = custom_fields[custom_field_id]
            # print(f"Custom Field: {custom_field['name']} (ID: {custom_field['id']})")
            if custom_field['name'] == 'Alter':
                alter_custom_field_id = custom_field_id
                print(f"Custom Field: {custom_field['name']} (ID: {custom_field['id']})")

                for option in custom_field['options']:
                    print(option['id'], option['value']['text'])
                    alters[option['value']['text']] = option['id']
                break
        
        # we want to return the custom field id for 'Alter' and the dictionary of alters
        return alter_custom_field_id, alters
    
    # we want a function to randomly select an alter from the alters dictionary
    def get_random_alter(self) -> str:
        """
        Get a random alter from the alters dictionary.
        
        Returns:
            str: A random alter name
        """
        if not self.alters:
            raise ValueError("No alters available")
        return random.choice(list(self.alters.keys()))


    def get_custom_fields(self) -> Dict[str, Dict]:
        """
        Fetch all custom fields for the board containing the monitored list.
        
        Returns:
            Dict[str, Dict]: Dictionary with custom field IDs as keys and field definitions as values
            
        Raises:
            requests.RequestException: If the API request fails
        """
        # Get board ID from the list
        board_url = f"{self.base_url}/lists/{self.list_id}/board"
        params = {
            'key': self.api_key,
            'token': self.token,
            'fields': 'id'
        }
        
        response = requests.get(board_url, params=params)
        response.raise_for_status()
        
        board_id = response.json()['id']
        
        # Fetch custom fields for the board
        cf_url = f"{self.base_url}/boards/{board_id}/customFields"
        cf_params = {
            'key': self.api_key,
            'token': self.token
        }
        
        cf_response = requests.get(cf_url, params=cf_params)
        cf_response.raise_for_status()
        
        return {cf['id']: cf for cf in cf_response.json()}
    
    def get_custom_field_items_for_card(self, card_id: str) -> Dict[str, Dict]:
        """
        Fetch all custom field items for a specific card.
        
        Args:
            card_id (str): The ID of the card to get custom fields for
            
        Returns:
            Dict[str, Dict]: Dictionary of custom field items
            
        Raises:
            requests.RequestException: If the API request fails
        """
        url = f"{self.base_url}/cards/{card_id}/customFieldItems"
        params = {
            'key': self.api_key,
            'token': self.token
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        items = response.json()
        return {item['idCustomField']: item for item in items}
        
    def get_cards(self) -> Dict[str, Dict]:
        """
        Fetch all cards from the specified list.
        
        Returns:
            Dict[str, Dict]: Dictionary with card IDs as keys and card data as values
            
        Raises:
            requests.RequestException: If the API request fails
        """
        url = f"{self.base_url}/lists/{self.list_id}/cards"
        params = {
            'key': self.api_key,
            'token': self.token,
            'fields': 'id,name,desc,due,dateLastActivity,pos,closed'
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        cards = response.json()
        return {card['id']: card for card in cards}
    
    def compare_cards(self, old_cards: Dict, new_cards: Dict) -> Dict:
        """
        Compare two card states and return differences.
        
        Args:
            old_cards (Dict): Previous card state
            new_cards (Dict): Current card state
            
        Returns:
            Dict: Dictionary containing 'added', 'removed', and 'modified' cards
        """
        old_ids = set(old_cards.keys())
        new_ids = set(new_cards.keys())
        
        added = new_ids - old_ids
        removed = old_ids - new_ids
        common = old_ids & new_ids
        
        # Check for modifications in common cards
        modified = []
        for card_id in common:
            old_card = old_cards[card_id]
            new_card = new_cards[card_id]
            
            # Compare relevant fields (excluding dateLastActivity)
            old_relevant = {k: v for k, v in old_card.items() if k != 'dateLastActivity'}
            new_relevant = {k: v for k, v in new_card.items() if k != 'dateLastActivity'}
            
            if old_relevant != new_relevant:
                modified.append({
                    'id': card_id,
                    'old': old_card,
                    'new': new_card,
                    'changes': self._get_field_changes(old_card, new_card)
                })
        
        return {
            'added': [new_cards[card_id] for card_id in added],
            'removed': [old_cards[card_id] for card_id in removed],
            'modified': modified
        }
    
    def _get_field_changes(self, old_card: Dict, new_card: Dict) -> Dict:
        """
        Get specific field changes between two cards.
        
        Args:
            old_card (Dict): Previous card state
            new_card (Dict): Current card state
            
        Returns:
            Dict: Dictionary of changed fields with old and new values
        """
        changes = {}
        for field in ['name', 'desc', 'due', 'pos', 'closed']:
            if old_card.get(field) != new_card.get(field):
                changes[field] = {
                    'old': old_card.get(field),
                    'new': new_card.get(field)
                }
        return changes
    
    def print_diff(self, diff: Dict, verbose: bool = True):
        """
        Pretty print the differences between card states.
        
        Args:
            diff (Dict): Differences returned by compare_cards()
            verbose (bool): Whether to print detailed information
        """
        if not any(diff.values()):
            if verbose:
                print("No changes detected")
            return
            
        if diff['added']:
            print(f"\n📝 ADDED ({len(diff['added'])} cards):")
            for card in diff['added']:
                print(f"  + {card['name']} (ID: {card['id']})")
        
        if diff['removed']:
            print(f"\n🗑️  REMOVED ({len(diff['removed'])} cards):")
            for card in diff['removed']:
                print(f"  - {card['name']} (ID: {card['id']})")
        
        if diff['modified']:
            print(f"\n✏️  MODIFIED ({len(diff['modified'])} cards):")
            for mod in diff['modified']:
                print(f"  ~ {mod['new']['name']} (ID: {mod['id']})")
                for field, change in mod['changes'].items():
                    print(f"    {field}: '{change['old']}' → '{change['new']}'")
    
    def monitor(self, interval: float = 1.0, max_iterations: Optional[int] = None, 
                callback: Optional[callable] = None, verbose: bool = True):
        """
        Monitor the list for changes.
        
        Args:
            interval (float): Time between checks in seconds
            max_iterations (Optional[int]): Maximum number of iterations (None for infinite)
            callback (Optional[callable]): Function to call when changes are detected
            verbose (bool): Whether to print status information
            
        The callback function, if provided, will be called with the diff dictionary
        whenever changes are detected.
        """
        if verbose:
            print(f"Starting monitor for list {self.list_id}")
            print(f"Checking every {interval} seconds...")
            print("Press Ctrl+C to stop\n")
        
        # Get initial state
        try:
            previous_cards = self.get_cards()
            if verbose:
                print(f"Initial state: {len(previous_cards)} cards")
        except requests.RequestException as e:
            print(f"Error fetching initial state: {e}")
            return
        
        iteration = 0
        try:
            while max_iterations is None or iteration < max_iterations:
                time.sleep(interval)
                iteration += 1
                
                try:
                    current_cards = self.get_cards()
                    diff = self.compare_cards(previous_cards, current_cards)
                    
                    if verbose:
                        print(".", end='')  # Print a dot for each iteration
                    
                    # Check if there are any changes
                    has_changes = any(diff.values())
                    
                    if has_changes:
                        if verbose:
                            self.print_diff(diff)
                        
                        # Call callback if provided
                        if callback:
                            callback(diff)
                    
                    previous_cards = current_cards
                    
                except requests.RequestException as e:
                    if verbose:
                        print(f"Error fetching cards: {e}")
                    
        except KeyboardInterrupt:
            if verbose:
                print("\nMonitoring stopped by user")

    def get_card_details(self, card_id: str) -> Dict:
        """
        Get detailed card information including custom fields.
        
        Args:
            card_id (str): The ID of the card to retrieve
            
        Returns:
            Dict: Card details including title, description, and custom fields
            
        Raises:
            requests.RequestException: If the API request fails
        """
        # Get card details
        card_url = f"{self.base_url}/cards/{card_id}"
        card_params = {
            'key': self.api_key,
            'token': self.token,
            'fields': 'id,name,desc,customFieldItems,shortUrl',
            'customFieldItems': 'true'
        }
        
        card_response = requests.get(card_url, params=card_params)
        card_response.raise_for_status()
        card_data = card_response.json()
        
        # Get board ID from the card
        card_board_url = f"{self.base_url}/cards/{card_id}/board"
        board_params = {
            'key': self.api_key,
            'token': self.token,
            'fields': 'id'
        }
        
        board_response = requests.get(card_board_url, params=board_params)
        board_response.raise_for_status()
        board_id = board_response.json()['id']
        card_frontend_url = card_data.get('shortUrl', '')
        
        # Get custom field definitions
        custom_fields_url = f"{self.base_url}/boards/{board_id}/customFields"
        cf_params = {
            'key': self.api_key,
            'token': self.token
        }
        
        cf_response = requests.get(custom_fields_url, params=cf_params)
        cf_response.raise_for_status()
        custom_field_definitions = cf_response.json()
        
        # Create mapping of custom field IDs to definitions
        cf_def_map = {cf['id']: cf for cf in custom_field_definitions}
        
        # Process custom field values
        custom_fields = {}
        for cf_item in card_data.get('customFieldItems', []):
            cf_id = cf_item['idCustomField']
            cf_def = cf_def_map.get(cf_id)
            
            if cf_def:
                field_name = cf_def['name']
                field_type = cf_def['type']
                # print(f"Processing custom field ID: {cf_id}, Name: {field_name}, Type: {field_type}")

                
                # Extract value based on field type
                value = None
                # print(f"Processing custom field: {field_name} (ID: {cf_id}, Type: {field_type}), {cf_item}")
                if 'value' in cf_item:
                    if field_type == 'text':
                        value = cf_item['value'].get('text')
                    elif field_type == 'number':
                        value = cf_item['value'].get('number')
                    elif field_type == 'date':
                        value = cf_item['value'].get('date')
                    elif field_type == 'checkbox':
                        value = cf_item['value'].get('checked')
                    elif field_type == 'list':
                        # For dropdown lists, get the selected option
                        value = cf_item['value']#.get('option')
                        # if option_id and 'options' in cf_def:
                        #     option = next((opt for opt in cf_def['options'] 
                        #                  if opt['id'] == option_id), None)
                        #     value = option['value']['text'] if option else option_id
                
                custom_fields[field_name] = {
                    'value': value,
                    'type': field_type,
                    'id': cf_id
                }

        story_points = 0.1  # default value
        if 'Story Points' in custom_fields:
            sp_value = custom_fields['Story Points']['value']
            if sp_value is not None:
                try:
                    story_points = float(sp_value)
                except (ValueError, TypeError):
                    story_points = 0.1  # fallback to default if conversion fails

        alter = None
        alter_custom_field_id = None
        if 'Alter' in custom_fields:
            sp_value = custom_fields['Alter']['value']
            if sp_value is not None:
                try:
                    alter = float(sp_value)
                except (ValueError, TypeError):
                    alter = None  # fallback to default if conversion fails
            alter_custom_field_id = custom_fields['Alter']['id']

        return {
            'id': card_data['id'],
            'title': card_data['name'],
            'description': card_data.get('desc', ''),
            'custom_fields': custom_fields,
            'story_points': story_points,
            'alter': alter,
            'alter_custom_field_id': alter_custom_field_id,
            'frontend_url': card_frontend_url
        }

    def get_single_diff(self, wait_time: float = 1.0) -> Dict:
        """
        Get a single snapshot comparison after waiting.
        
        Args:
            wait_time (float): Time to wait between snapshots
            
        Returns:
            Dict: Differences between the two snapshots
        """
        cards1 = self.get_cards()
        time.sleep(wait_time)
        cards2 = self.get_cards()
        return self.compare_cards(cards1, cards2)

    def set_custom_field(self, card_id: str, custom_field_id: str, value, field_type: str = None) -> bool:
        """
        Set or update a custom field value on a card.

        Args:
            card_id (str): The ID of the card to update
            custom_field_id (str): The ID of the custom field to update
            value: The value to set (type depends on field_type)
            field_type (str): Type of field ('text', 'number', 'date', 'checkbox', 'list')
                            If None, will attempt to auto-detect

        Returns:
            bool: True if successful, False otherwise

        Raises:
            requests.RequestException: If the API request fails
        """
        # FIXED: Use "cards" instead of "card" in URL
        url = f"{self.base_url}/cards/{card_id}/customField/{custom_field_id}/item"
        params = {
            'key': self.api_key,
            'token': self.token
        }
        headers = {
            'Content-Type': 'application/json'
        }

        # Auto-detect field type if not provided
        if field_type is None:
            if isinstance(value, bool):
                field_type = 'checkbox'
            elif isinstance(value, (int, float)):
                field_type = 'number'
            elif isinstance(value, str):
                # Could be text or date, default to text
                field_type = 'text'

        # FIXED: Structure the value based on field type, all values must be strings
        if field_type == 'text':
            body = {"value": {"text": str(value)}}
        elif field_type == 'number':
            # FIXED: Numbers must be sent as strings
            body = {"value": {"number": str(value)}}
        elif field_type == 'date':
            body = {"value": {"date": str(value)}}  # Should be ISO format string
        elif field_type == 'checkbox':
            # FIXED: Trello expects "true" or "false" as strings
            body = {"value": {"checked": "true" if value else "false"}}
        elif field_type == 'list':
            # For dropdown lists, value should be the option ID
            body = {"idValue": str(value)}
        else:
            raise ValueError(f"Unsupported field type: {field_type}")

        try:
            response = requests.put(url, params=params, headers=headers, data=json.dumps(body))
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            print(f"Error setting custom field: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response status: {e.response.status_code}")
                print(f"Response body: {e.response.text}")
            return Falses
        
    def delete_card(self, card_id: str) -> bool:
        """
        Delete a card by its ID.

        Args:
            card_id (str): The ID of the card to delete

        Returns:
            bool: True if deletion was successful, False otherwise

        Raises:
            requests.RequestException: If the API request fails
        """
        url = f"{self.base_url}/cards/{card_id}"
        params = {
            'key': self.api_key,
            'token': self.token
        }

        try:
            response = requests.delete(url, params=params)
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            print(f"Error deleting card: {e}")
            return False
        
# Convenience functions for common use cases
def monitor_list(list_id: Optional[str] = None, interval: float = 1.0, 
                max_iterations: Optional[int] = None):
    """
    Convenience function to quickly start monitoring a list.
    
    Args:
        list_id (Optional[str]): List ID to monitor (uses .env if not provided)
        interval (float): Check interval in seconds
        max_iterations (Optional[int]): Max iterations (None for infinite)
    """
    monitor = TrelloListMonitor(list_id)
    monitor.monitor(interval=interval, max_iterations=max_iterations)
