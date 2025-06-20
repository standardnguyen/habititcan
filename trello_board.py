"""
Trello Board Monitor - Extension to monitor entire boards

This extends the existing TrelloListMonitor to support board-wide monitoring.
"""

import requests
import time
import json
from typing import Dict, List, Set, Tuple, Optional
import os
from dotenv import load_dotenv
import random


class TrelloBoardMonitor:
    """
    A class to monitor entire Trello boards for changes across all lists.
    
    This class provides functionality to:
    - Monitor all cards across all lists on a board
    - Track which list each card belongs to
    - Compare card states between different time points
    - Retrieve detailed card information including custom fields
    """
    
    def __init__(self, board_id: Optional[str] = None):
        """
        Initialize the Trello Board Monitor.
        
        Automatically loads credentials from .env file using:
        - TRELLO_API_KEY
        - TRELLO_API_TOKEN  
        - TRELLO_BOARD_ID (if board_id not provided)
        
        Args:
            board_id (Optional[str]): The ID of the Trello board to monitor.
                                     If not provided, will use TRELLO_BOARD_ID from .env
        """
        # Load environment variables from .env file
        load_dotenv()
        
        self.api_key = os.getenv("TRELLO_API_KEY")
        self.token = os.getenv("TRELLO_API_TOKEN")
        self.board_id = board_id or os.getenv("TRELLO_BOARD_ID")
        
        if not self.api_key:
            raise ValueError("TRELLO_API_KEY not found in environment variables")
        if not self.token:
            raise ValueError("TRELLO_API_TOKEN not found in environment variables")
        if not self.board_id:
            raise ValueError("TRELLO_BOARD_ID not provided and not found in environment variables")
            
        self.base_url = "https://api.trello.com/1"
        
        # Cache board lists for reference
        self.lists = self.get_lists()
        
        # Get alter info (if applicable to your board)
        try:
            self.alter_custom_field_id, self.alters = self.get_alter_info()
        except:
            self.alter_custom_field_id, self.alters = None, {}

    def get_lists(self) -> Dict[str, Dict]:
        """
        Fetch all lists from the board.
        
        Returns:
            Dict[str, Dict]: Dictionary with list IDs as keys and list data as values
        """
        url = f"{self.base_url}/boards/{self.board_id}/lists"
        params = {
            'key': self.api_key,
            'token': self.token,
            'fields': 'id,name,pos,closed'
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        lists = response.json()
        return {list_item['id']: list_item for list_item in lists}

    def get_alter_info(self) -> Tuple[Optional[str], Dict]:
        """Get alter custom field info (same as original class)"""
        print("fetching alter information...")
        custom_fields = self.get_custom_fields()

        alters = {}
        alter_custom_field_id = None
        
        for custom_field_id in custom_fields:
            custom_field = custom_fields[custom_field_id]
            if custom_field['name'] == 'Alter':
                alter_custom_field_id = custom_field_id
                print(f"Custom Field: {custom_field['name']} (ID: {custom_field['id']})")

                for option in custom_field['options']:
                    print(option['id'], option['value']['text'])
                    alters[option['value']['text']] = option['id']
                break
        
        return alter_custom_field_id, alters
    
    def get_random_alter(self) -> str:
        """Get a random alter from the alters dictionary."""
        if not self.alters:
            raise ValueError("No alters available")
        return random.choice(list(self.alters.keys()))

    def get_custom_fields(self) -> Dict[str, Dict]:
        """
        Fetch all custom fields for the board.
        
        Returns:
            Dict[str, Dict]: Dictionary with custom field IDs as keys and field definitions as values
        """
        cf_url = f"{self.base_url}/boards/{self.board_id}/customFields"
        cf_params = {
            'key': self.api_key,
            'token': self.token
        }
        
        cf_response = requests.get(cf_url, params=cf_params)
        cf_response.raise_for_status()
        
        return {cf['id']: cf for cf in cf_response.json()}

    def get_cards(self) -> Dict[str, Dict]:
        """
        Fetch all cards from all lists on the board.
        
        Returns:
            Dict[str, Dict]: Dictionary with card IDs as keys and card data as values
                            Each card includes 'list_id' and 'list_name' fields
        """
        url = f"{self.base_url}/boards/{self.board_id}/cards"
        params = {
            'key': self.api_key,
            'token': self.token,
            'fields': 'id,name,desc,due,dateLastActivity,pos,closed,idList'
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        cards = response.json()
        
        # Enhance cards with list information
        enhanced_cards = {}
        for card in cards:
            card_id = card['id']
            list_id = card['idList']
            list_name = self.lists.get(list_id, {}).get('name', 'Unknown List')
            
            card['list_id'] = list_id
            card['list_name'] = list_name
            enhanced_cards[card_id] = card
            
        return enhanced_cards

    def compare_cards(self, old_cards: Dict, new_cards: Dict) -> Dict:
        """
        Compare two card states and return differences, including list movements.
        
        Args:
            old_cards (Dict): Previous card state
            new_cards (Dict): Current card state
            
        Returns:
            Dict: Dictionary containing 'added', 'removed', 'modified', and 'moved' cards
        """
        old_ids = set(old_cards.keys())
        new_ids = set(new_cards.keys())
        
        added = new_ids - old_ids
        removed = old_ids - new_ids
        common = old_ids & new_ids
        
        # Check for modifications and movements in common cards
        modified = []
        moved = []
        
        for card_id in common:
            old_card = old_cards[card_id]
            new_card = new_cards[card_id]
            
            # Check if card moved between lists
            if old_card['idList'] != new_card['idList']:
                moved.append({
                    'id': card_id,
                    'name': new_card['name'],
                    'from_list': old_card['list_name'],
                    'to_list': new_card['list_name'],
                    'old_card': old_card,
                    'new_card': new_card
                })
            
            # Compare relevant fields (excluding dateLastActivity and list changes)
            old_relevant = {k: v for k, v in old_card.items() 
                           if k not in ['dateLastActivity', 'idList', 'list_id', 'list_name']}
            new_relevant = {k: v for k, v in new_card.items() 
                           if k not in ['dateLastActivity', 'idList', 'list_id', 'list_name']}
            
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
            'modified': modified,
            'moved': moved
        }

    def _get_field_changes(self, old_card: Dict, new_card: Dict) -> Dict:
        """Get specific field changes between two cards."""
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
        Pretty print the differences between card states, including list movements.
        
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
                print(f"  + {card['name']} in '{card['list_name']}' (ID: {card['id']})")
        
        if diff['removed']:
            print(f"\n🗑️  REMOVED ({len(diff['removed'])} cards):")
            for card in diff['removed']:
                print(f"  - {card['name']} from '{card['list_name']}' (ID: {card['id']})")
        
        if diff['moved']:
            print(f"\n🔄 MOVED ({len(diff['moved'])} cards):")
            for move in diff['moved']:
                print(f"  → {move['name']}: '{move['from_list']}' → '{move['to_list']}'")
        
        if diff['modified']:
            print(f"\n✏️  MODIFIED ({len(diff['modified'])} cards):")
            for mod in diff['modified']:
                print(f"  ~ {mod['new']['name']} in '{mod['new']['list_name']}' (ID: {mod['id']})")
                for field, change in mod['changes'].items():
                    print(f"    {field}: '{change['old']}' → '{change['new']}'")

    def monitor(self, interval: float = 1.0, max_iterations: Optional[int] = None, 
                callback: Optional[callable] = None, verbose: bool = True):
        """
        Monitor the entire board for changes.
        
        Args:
            interval (float): Time between checks in seconds
            max_iterations (Optional[int]): Maximum number of iterations (None for infinite)
            callback (Optional[callable]): Function to call when changes are detected
            verbose (bool): Whether to print status information
        """
        if verbose:
            print(f"Starting board monitor for board {self.board_id}")
            print(f"Monitoring {len(self.lists)} lists")
            print(f"Checking every {interval} seconds...")
            print("Press Ctrl+C to stop\n")
        
        # Get initial state
        try:
            previous_cards = self.get_cards()
            if verbose:
                print(f"Initial state: {len(previous_cards)} cards across {len(self.lists)} lists")
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
        (Same implementation as original TrelloListMonitor)
        """
        # Get card details
        card_url = f"{self.base_url}/cards/{card_id}"
        card_params = {
            'key': self.api_key,
            'token': self.token,
            'fields': 'id,name,desc,customFieldItems,shortUrl,idList',
            'customFieldItems': 'true'
        }
        
        card_response = requests.get(card_url, params=card_params)
        card_response.raise_for_status()
        card_data = card_response.json()
        
        card_frontend_url = card_data.get('shortUrl', '')
        
        # Get custom field definitions (we already have the board_id)
        custom_fields_url = f"{self.base_url}/boards/{self.board_id}/customFields"
        cf_params = {
            'key': self.api_key,
            'token': self.token
        }
        
        cf_response = requests.get(custom_fields_url, params=cf_params)
        cf_response.raise_for_status()
        custom_field_definitions = cf_response.json()
        
        # Create mapping of custom field IDs to definitions
        cf_def_map = {cf['id']: cf for cf in custom_field_definitions}
        
        # Process custom field values (same logic as original)
        custom_fields = {}
        for cf_item in card_data.get('customFieldItems', []):
            cf_id = cf_item['idCustomField']
            cf_def = cf_def_map.get(cf_id)
            
            if cf_def:
                field_name = cf_def['name']
                field_type = cf_def['type']
                
                value = None
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
                        value = cf_item['value']
                
                custom_fields[field_name] = {
                    'value': value,
                    'type': field_type,
                    'id': cf_id
                }

        # Extract common fields
        story_points = 0.1
        if 'Story Points' in custom_fields:
            sp_value = custom_fields['Story Points']['value']
            if sp_value is not None:
                try:
                    story_points = float(sp_value)
                except (ValueError, TypeError):
                    story_points = 0.1

        alter = None
        alter_custom_field_id = None
        if 'Alter' in custom_fields:
            alter_value = custom_fields['Alter']['value']
            if alter_value is not None:
                try:
                    alter = float(alter_value)
                except (ValueError, TypeError):
                    alter = None
            alter_custom_field_id = custom_fields['Alter']['id']

        # Add list information
        list_id = card_data.get('idList')
        list_name = self.lists.get(list_id, {}).get('name', 'Unknown List')

        return {
            'id': card_data['id'],
            'title': card_data['name'],
            'description': card_data.get('desc', ''),
            'custom_fields': custom_fields,
            'story_points': story_points,
            'alter': alter,
            'alter_custom_field_id': alter_custom_field_id,
            'frontend_url': card_frontend_url,
            'list_id': list_id,
            'list_name': list_name
        }

    def get_cards_by_list(self) -> Dict[str, List[Dict]]:
        """
        Get all cards organized by list.
        
        Returns:
            Dict[str, List[Dict]]: Dictionary with list names as keys and lists of cards as values
        """
        all_cards = self.get_cards()
        cards_by_list = {}
        
        for card in all_cards.values():
            list_name = card['list_name']
            if list_name not in cards_by_list:
                cards_by_list[list_name] = []
            cards_by_list[list_name].append(card)
        
        return cards_by_list

    def set_custom_field(self, card_id: str, custom_field_id: str, value, field_type: str = None) -> bool:
        """Set custom field value (same as original implementation)"""
        url = f"{self.base_url}/cards/{card_id}/customField/{custom_field_id}/item"
        params = {
            'key': self.api_key,
            'token': self.token
        }
        headers = {
            'Content-Type': 'application/json'
        }

        if field_type is None:
            if isinstance(value, bool):
                field_type = 'checkbox'
            elif isinstance(value, (int, float)):
                field_type = 'number'
            elif isinstance(value, str):
                field_type = 'text'

        if field_type == 'text':
            body = {"value": {"text": str(value)}}
        elif field_type == 'number':
            body = {"value": {"number": str(value)}}
        elif field_type == 'date':
            body = {"value": {"date": str(value)}}
        elif field_type == 'checkbox':
            body = {"value": {"checked": "true" if value else "false"}}
        elif field_type == 'list':
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
            return False

    def delete_card(self, card_id: str) -> bool:
        """Delete a card by its ID (same as original implementation)"""
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
