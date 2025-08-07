import random
from typing import Dict, Any, Optional
import json
import os

class BehaviorPatternUtil:
    """
    Utility class for managing human-like behavior patterns for Instagram interactions.
    Provides profiles for different browsing behaviors and engagement patterns.
    """
    
    # Default behavior patterns
    DEFAULT_PATTERNS = {
        "casual_browser": {
            "description": "Casually browses without much engagement",
            "view_stories_probability": 0.4,
            "open_post_probability": 0.3,
            "like_probability": 0.15,
            "follow_probability": 0.05,
            "comment_probability": 0.02,
            "scroll_speed": "medium",
            "avg_time_per_profile": [20, 40],  # seconds
            "max_posts_per_profile": 2
        },
        "engaged_follower": {
            "description": "More engaged with content, moderate following",
            "view_stories_probability": 0.7,
            "open_post_probability": 0.6,
            "like_probability": 0.4,
            "follow_probability": 0.15,
            "comment_probability": 0.08,
            "scroll_speed": "medium-slow",
            "avg_time_per_profile": [40, 90],
            "max_posts_per_profile": 4
        },
        "power_user": {
            "description": "Highly engaged, selective following",
            "view_stories_probability": 0.9,
            "open_post_probability": 0.8,
            "like_probability": 0.6,
            "follow_probability": 0.2,
            "comment_probability": 0.15,
            "scroll_speed": "variable",
            "avg_time_per_profile": [60, 180],
            "max_posts_per_profile": 6
        },
        "business_account": {
            "description": "Professional engagement focused on networking",
            "view_stories_probability": 0.6,
            "open_post_probability": 0.5,
            "like_probability": 0.4,
            "follow_probability": 0.3,
            "comment_probability": 0.1,
            "scroll_speed": "medium-fast",
            "avg_time_per_profile": [30, 60],
            "max_posts_per_profile": 3
        }
    }
    
    def __init__(self, custom_patterns_path: Optional[str] = None):
        """
        Initialize behavior patterns, optionally loading custom patterns.
        
        Args:
            custom_patterns_path: Optional path to JSON file with custom patterns
        """
        self.patterns = self.DEFAULT_PATTERNS.copy()
        
        if custom_patterns_path and os.path.exists(custom_patterns_path):
            try:
                with open(custom_patterns_path, 'r') as f:
                    custom_patterns = json.load(f)
                    self.patterns.update(custom_patterns)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading custom patterns: {e}")
    
    def get_pattern(self, pattern_name: str) -> Dict[str, Any]:
        """
        Get a specific behavior pattern.
        
        Args:
            pattern_name: Name of the pattern to get
            
        Returns:
            Dictionary containing pattern parameters
        """
        return self.patterns.get(pattern_name, self.patterns["casual_browser"])
    
    def get_random_pattern(self, bias: Optional[str] = None) -> Dict[str, Any]:
        """
        Get a random behavior pattern, optionally with bias toward a certain type.
        
        Args:
            bias: Optional bias toward a specific pattern type
            
        Returns:
            Dictionary containing pattern parameters
        """
        patterns = list(self.patterns.keys())
        
        if bias and bias in patterns:
            # 60% chance to return the biased pattern
            if random.random() < 0.6:
                return self.patterns[bias]
            
            # Remove bias from options for random selection
            patterns.remove(bias)
        
        return self.patterns[random.choice(patterns)]
    
    def create_custom_pattern(self, 
                             view_stories_prob: float = None,
                             open_post_prob: float = None,
                             like_prob: float = None,
                             follow_prob: float = None,
                             comment_prob: float = None) -> Dict[str, Any]:
        """
        Create a custom behavior pattern by mixing existing ones.
        
        Args:
            Various probability overrides for specific behaviors
            
        Returns:
            Dictionary containing custom pattern parameters
        """
        # Start with a random base pattern
        base_pattern = random.choice(list(self.patterns.values()))
        custom = base_pattern.copy()
        
        # Override specific probabilities if provided
        if view_stories_prob is not None:
            custom["view_stories_probability"] = view_stories_prob
        if open_post_prob is not None:
            custom["open_post_probability"] = open_post_prob
        if like_prob is not None:
            custom["like_probability"] = like_prob
        if follow_prob is not None:
            custom["follow_probability"] = follow_prob
        if comment_prob is not None:
            custom["comment_probability"] = comment_prob
            
        # Add some randomness to other parameters
        time_min, time_max = custom["avg_time_per_profile"]
        custom["avg_time_per_profile"] = [
            max(10, int(time_min * random.uniform(0.8, 1.2))),
            max(20, int(time_max * random.uniform(0.8, 1.2)))
        ]
        
        custom["max_posts_per_profile"] = max(1, int(custom["max_posts_per_profile"] * random.uniform(0.7, 1.3)))
        
        return custom
    
    @staticmethod
    def adjust_for_account_size(pattern: Dict[str, Any], follower_count: int) -> Dict[str, Any]:
        """
        Adjust behavior pattern based on the target account's size.
        
        Args:
            pattern: Base behavior pattern
            follower_count: Number of followers for the target account
            
        Returns:
            Adjusted pattern
        """
        adjusted = pattern.copy()
        
        # Adjust follow probability based on account size
        if follower_count > 100000:  # 100k+ followers
            # More likely to follow large accounts
            adjusted["follow_probability"] = min(0.95, pattern["follow_probability"] * 1.5)
        elif follower_count > 10000:  # 10k+ followers
            # Somewhat more likely to follow medium accounts
            adjusted["follow_probability"] = min(0.95, pattern["follow_probability"] * 1.25)
        elif follower_count < 1000:  # <1k followers
            # Less likely to follow small accounts
            adjusted["follow_probability"] = max(0.01, pattern["follow_probability"] * 0.75)
            
        # Adjust engagement probabilities
        if follower_count > 50000:  # 50k+ followers
            # More posts to view on large accounts
            adjusted["max_posts_per_profile"] = min(10, pattern["max_posts_per_profile"] + 2)
            # Spend more time on large accounts
            time_min, time_max = pattern["avg_time_per_profile"]
            adjusted["avg_time_per_profile"] = [time_min * 1.3, time_max * 1.3]
            
        return adjusted