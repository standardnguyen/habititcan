"""
Habitica API Library

A Python library for interacting with the Habitica API to score habits, manage tasks, and log story points.
"""

import os
import requests
import time
from typing import Optional, Dict, Any, List, Callable
from dotenv import load_dotenv


class HabiticaAPI:
    """
    A library for interacting with the Habitica API.
    
    Usage:
        # Using environment variables
        habitica = HabiticaAPI()
        
        # Using explicit credentials
        habitica = HabiticaAPI(user_id="your_user_id", api_token="your_token")
        
        # With callback function for press_plus operations
        def my_callback(result, task_id, direction):
            print(f"Callback: {task_id} scored {direction} with result: {result['success']}")
        
        habitica = HabiticaAPI(callback=my_callback)
        
        # Score a doot (callback will be called automatically)
        habitica.press_plus("hard-doot")
        
        # Log story points
        habitica.log_story_points(7)
    """
    
    def __init__(self, user_id: Optional[str] = None, api_token: Optional[str] = None, load_env: bool = True, callback: Optional[Callable[[Dict[str, Any], str, str], None]] = None):
        """
        Initialize the Habitica API client.
        
        Args:
            user_id: Habitica User ID. If None, will try to load from environment.
            api_token: Habitica API Token. If None, will try to load from environment.
            load_env: Whether to load environment variables from .env file.
            callback: Optional callback function for press_plus operations. 
                     Called with (result, task_id, direction) after each press_plus.
        """
        if load_env:
            load_dotenv()
            
        self.user_id = user_id or os.getenv('HABITICA_USER_ID')
        self.api_token = api_token or os.getenv('HABITICA_API_TOKEN')
        self.callback = callback  # Store the callback for press_plus operations
        
        if not self.user_id:
            raise ValueError(
                "HABITICA_USER_ID must be provided either as parameter or "
                "environment variable."
            )
        if not self.api_token:
            raise ValueError(
                "HABITICA_API_TOKEN must be provided either as parameter or "
                "environment variable."
            )
            
        self.base_url = "https://habitica.com/api/v3"
        self.headers = {
            "x-api-user": self.user_id,
            "x-api-key": self.api_token,
            "x-client": f"{self.user_id}-PythonLibrary",
            "Content-Type": "application/json"
        }

    def get_profile(self, delay: float = 3.0) -> Dict[str, Any]:
        """
        Get user's profile information.
        
        Returns:
            Dict containing user profile data
        """
        url = f"{self.base_url}/user"

        if delay > 0:
            time.sleep(delay)

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def score_habit(
        self, 
        task_id: str, 
        direction: str = "up", 
        verbose: bool = True,
        delay: float = 4.0
    ) -> Dict[str, Any]:
        """
        Score a doot (task component) using its task ID.
        
        Args:
            task_id: The task ID/alias of your doot
            direction: "up" for + button, "down" for - button
            verbose: Whether to print scoring results
            delay: Delay in seconds before making the request (for rate limiting)
            
        Returns:
            Dict containing success status and response details
        """
        if direction not in ["up", "down"]:
            raise ValueError("Direction must be 'up' or 'down'")
            
        url = f"{self.base_url}/tasks/{task_id}/score/{direction}"
        
        if delay > 0:
            time.sleep(delay)
            
        try:
            response = requests.post(url, headers=self.headers)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('success'):
                if verbose:
                    self._print_score_result(result, direction, task_id)
                
                final_result = {
                    "success": True,
                    "data": result.get('data', {}),
                    "notifications": result.get('notifications', []),
                    "task_id": task_id,
                    "direction": direction
                }
            else:
                if verbose:
                    print(f"❌ Failed to score doot {task_id}")
                final_result = {
                    "success": False,
                    "task_id": task_id,
                    "direction": direction,
                    "error": "API returned success=False"
                }
                
        except requests.exceptions.RequestException as e:
            if verbose:
                print(f"❌ Error scoring doot {task_id}: {e}")
            final_result = {
                "success": False,
                "task_id": task_id,
                "direction": direction,
                "error": str(e)
            }
        
        # Call the callback function if provided and this is a press_plus operation
        if self.callback and direction == "up":
            try:
                self.callback(final_result, task_id, direction)
            except Exception as e:
                if verbose:
                    print(f"⚠️  Callback error: {e}")
        
        return final_result
    
    def _print_score_result(self, result: Dict, direction: str, task_id: str):
        """Print the results of scoring a doot."""
        symbol = "+" if direction == "up" else "-"
        data = result.get('data', {})
        
        # Show basic scoring result
        delta = data.get('delta', 0)
        print(f"✅ {symbol} {task_id} (Δ: {delta:+.3f})")
        
        # Show current stats
        stats = {
            'HP': data.get('hp', 0),
            'MP': data.get('mp', 0), 
            'XP': data.get('exp', 0),
            'Gold': data.get('gp', 0),
            'Level': data.get('lvl', 0)
        }
        
        stats_str = " | ".join([f"{k}: {v:.1f}" if isinstance(v, float) else f"{k}: {v}" 
                               for k, v in stats.items()])
        print(f"   📊 {stats_str}")
        
        # Handle temporary/special effects
        tmp_data = data.get('_tmp', {})
        
        # Quest progress
        if 'quest' in tmp_data:
            quest_info = tmp_data['quest']
            if 'progressDelta' in quest_info:
                progress = quest_info['progressDelta']
                print(f"   🗡️  Quest progress: +{progress:.2f}")
            if 'collection' in quest_info:
                collection = quest_info['collection']
                print(f"   📦 Quest collection: +{collection}")
        
        # Item drops
        if 'drop' in tmp_data:
            drop_info = tmp_data['drop']
            item_name = drop_info.get('key', 'Unknown')
            item_type = drop_info.get('type', 'Item')
            print(f"   🎁 Item dropped: {item_name} ({item_type})")
            if 'dialog' in drop_info:
                print(f"      💬 {drop_info['dialog']}")
        
        # Show notifications if any
        notifications = result.get('notifications', [])
        if notifications:
            print(f"   🔔 {len(notifications)} notification(s)")
    
    def press_plus(
        self, 
        task_id: str, 
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        Press the + button for a doot (task component).
        Uses the callback function specified during initialization if provided.
        
        Args:
            task_id: The task ID/alias of your doot
            verbose: Whether to print scoring results
            
        Returns:
            Dict containing success status and response details
            
        Note:
            The callback function (if set during initialization) will be called 
            automatically with (result, task_id, direction) after scoring.
        """
        return self.score_habit(task_id, "up", verbose=verbose)
    
    def press_minus(self, task_id: str, verbose: bool = True) -> Dict[str, Any]:
        """
        Press the - button for a doot (task component).
        
        Args:
            task_id: The task ID/alias of your doot
            verbose: Whether to print scoring results
            
        Returns:
            Dict containing success status and response details
        """
        return self.score_habit(task_id, "down", verbose=verbose)
    
    def get_tasks(self, task_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get user's tasks.
        
        Args:
            task_type: Type of tasks to retrieve ('habits', 'dailys', 'todos', 'rewards')
            
        Returns:
            Dict containing tasks data
        """
        url = f"{self.base_url}/tasks/user"
        params = {}
        if task_type:
            params['type'] = task_type
            
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def get_user_stats(self) -> Dict[str, Any]:
        """
        Get user's current stats (HP, XP, Gold, etc.).
        
        Returns:
            Dict containing user stats
        """
        url = f"{self.base_url}/user"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            result = response.json()
            
            if result.get('success'):
                stats = result.get('data', {}).get('stats', {})
                return {
                    "success": True,
                    "stats": stats
                }
            else:
                return {"success": False, "error": "API returned success=False"}
                
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def break_down_difficulty(value: float) -> Dict[str, int]:
        """
        Break down a number into difficulty parts using a greedy algorithm.
        
        Args:
            value: The number to break down (story points)
            
        Returns:
            Dict with counts for each difficulty level
        """
        if value < 0:
            raise ValueError("Value must be non-negative")
        
        # Define difficulty values in descending order for greedy approach
        difficulties = {
            'hard': 2.0,
            'medium': 1.5,
            'easy': 1.0,
            'trivial': 0.1
        }
        
        result = {'hard': 0, 'medium': 0, 'easy': 0, 'trivial': 0}
        remaining = float(value)
        
        # Use greedy algorithm to break down the value
        for difficulty, points in difficulties.items():
            count = int(remaining / points)
            result[difficulty] = count
            remaining = round(remaining - (count * points), 1)
        
        return result
    
    def log_story_points(
        self, 
        story_points: float, 
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        Log story points to Habitica by breaking them down into difficulty levels.
        
        Args:
            story_points: Number of story points to log
            verbose: Whether to print progress
            
        Returns:
            Dict containing results of all doot scoring
        """
        response = self.get_profile()
        data = response['data']

        if not response.get('success'):
            if verbose:
                print(f"❌ Failed to get user profile: {response.get('error', 'Unknown error')}")
            return {"success": False, "error": response.get('error', 'Unknown error')}

        starting_stats = {}
        starting_stats['exp'] = data['stats']['exp']
        starting_stats['gp'] = data['stats']['gp']
        starting_stats['level'] = data['stats']['lvl']

        if verbose:
            print(f"📊 Logging {story_points} story points...")
        
        difficulties = self.break_down_difficulty(story_points)
        results = []
        
        if verbose:
            print(f"   Breakdown: {difficulties}")
        
        for difficulty, count in difficulties.items():
            if count == 0:
                continue
                
            task_id = f"{difficulty}-doot"
            
            for i in range(count):
                if verbose:
                    print(f"   Scoring {difficulty} doot ({i+1}/{count})")
                
                result = self.press_plus(task_id, verbose=verbose)
                results.append(result)
        
        successful_scores = sum(1 for r in results if r.get('success'))
        
        if verbose:
            print(f"✅ Logged {successful_scores}/{len(results)} doots successfully")
        
        # Get final stats after scoring
        response = self.get_profile()
        data = response['data']

        if not response.get('success'):
            if verbose:
                print(f"❌ Failed to get user profile: {response.get('error', 'Unknown error')}")
            return {"success": False, "error": response.get('error', 'Unknown error')}

        ending_stats = {}
        ending_stats['exp'] = data['stats']['exp']
        ending_stats['gp'] = data['stats']['gp']
        ending_stats['level'] = data['stats']['lvl']

        stat_deltas = {
            'exp': ending_stats['exp'] - starting_stats['exp'],
            'gp': ending_stats['gp'] - starting_stats['gp'],
            'level': ending_stats['level'] - starting_stats['level']
        }

        return {
            "success": successful_scores == len(results),
            "story_points": story_points,
            "difficulty_breakdown": difficulties,
            "results": results,
            "successful_scores": successful_scores,
            "stat_deltas": stat_deltas
        }


# Convenience functions for backwards compatibility
def press_plus(
    task_id: str, 
    verbose: bool = True,
    callback: Optional[Callable[[Dict[str, Any], str, str], None]] = None
) -> Dict[str, Any]:
    """
    Convenience function to quickly score a doot positively.
    Requires HABITICA_USER_ID and HABITICA_API_TOKEN environment variables.
    
    Args:
        task_id: The task ID/alias of your doot
        verbose: Whether to print scoring results
        callback: Optional callback function called with (result, task_id, direction)
    """
    habitica = HabiticaAPI(callback=callback)
    return habitica.press_plus(task_id, verbose=verbose)


def press_minus(task_id: str, verbose: bool = True) -> Dict[str, Any]:
    """
    Convenience function to quickly score a doot negatively.
    Requires HABITICA_USER_ID and HABITICA_API_TOKEN environment variables.
    """
    habitica = HabiticaAPI()
    return habitica.press_minus(task_id, verbose=verbose)


def log_story_points(story_points: float, verbose: bool = True) -> Dict[str, Any]:
    """
    Convenience function to quickly log story points.
    Requires HABITICA_USER_ID and HABITICA_API_TOKEN environment variables.
    """
    habitica = HabiticaAPI()
    return habitica.log_story_points(story_points, verbose=verbose)


# Example usage
if __name__ == "__main__":
    # Example callback functions
    def exp_tracker(result, task_id, direction):
        """Track experience gained from scoring doots."""
        if result['success']:
            exp_gained = result['data'].get('delta', 0)
            current_exp = result['data'].get('exp', 0)
            print(f"🎯 {task_id}: +{exp_gained:.2f} XP (Total: {current_exp:.1f})")
        else:
            print(f"❌ Failed to score {task_id}: {result.get('error', 'Unknown error')}")
    
    def achievement_notifier(result, task_id, direction):
        """Notify about special achievements and drops."""
        if result['success']:
            notifications = result.get('notifications', [])
            if notifications:
                print(f"🎉 {len(notifications)} achievements unlocked from {task_id}!")
            
            # Check for item drops
            data = result.get('data', {})
            tmp_data = data.get('_tmp', {})
            if 'drop' in tmp_data:
                item = tmp_data['drop']
                print(f"💎 Item drop from {task_id}: {item.get('key', 'Unknown')}")
    
    def stats_logger(result, task_id, direction):
        """Log detailed stats after scoring."""
        if result['success']:
            data = result['data']
            stats = {
                'HP': data.get('hp', 0),
                'MP': data.get('mp', 0),
                'XP': data.get('exp', 0),
                'Gold': data.get('gp', 0),
                'Level': data.get('lvl', 0)
            }
            print(f"📈 Post-{task_id} stats: {stats}")
    
    def combined_callback(result, task_id, direction):
        """Multiple behaviors in one callback."""
        exp_tracker(result, task_id, direction)
        achievement_notifier(result, task_id, direction)
    
    # Example 1: Initialize with experience tracking callback
    try:
        print("=== Example 1: Experience Tracking Callback ===")
        habitica_exp = HabiticaAPI(callback=exp_tracker)
        result = habitica_exp.press_plus("hard-doot")
        
        # Example 2: Initialize with achievement notifications
        print("\n=== Example 2: Achievement Notifications ===")
        habitica_achievements = HabiticaAPI(callback=achievement_notifier)
        result = habitica_achievements.press_plus("medium-doot")
        
        # Example 3: Initialize with detailed stats logging
        print("\n=== Example 3: Stats Logging ===")
        habitica_stats = HabiticaAPI(callback=stats_logger)
        result = habitica_stats.press_plus("easy-doot")
        
        # Example 4: Combined callback behaviors
        print("\n=== Example 4: Combined Callback Behaviors ===")
        habitica_combined = HabiticaAPI(callback=combined_callback)
        result = habitica_combined.press_plus("trivial-doot")
        
        # Example 5: Multiple press_plus calls with same callback
        print("\n=== Example 5: Multiple Calls with Same Callback ===")
        habitica_multi = HabiticaAPI(callback=exp_tracker)
        for difficulty in ["easy", "medium", "hard"]:
            print(f"Scoring {difficulty} doot...")
            result = habitica_multi.press_plus(f"{difficulty}-doot")
        
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
    
    # Example 6: Using convenience function with callback
    print("\n=== Example 6: Convenience Function with Callback ===")
    success_result = press_plus("easy-doot", callback=exp_tracker)
    
    # Example 7: No callback (backward compatibility)
    print("\n=== Example 7: No Callback (Backward Compatible) ===")
    habitica_normal = HabiticaAPI()
    normal_result = habitica_normal.press_plus("hard-doot")
    print(f"✅ Normal scoring: {normal_result['success']}")