import random
import asyncio
import numpy as np
from typing import Tuple, List, Optional

class RandomizationUtil:
    """
    Utility class that provides human-like randomization for various actions
    such as timing delays, mouse movements, and behavior patterns.
    """
    
    @staticmethod
    async def human_delay(min_seconds: float = 1.0, max_seconds: float = 3.0, 
                          distribution: str = "normal") -> None:
        """
        Creates a human-like delay following different probability distributions.
        
        Args:
            min_seconds: Minimum delay in seconds
            max_seconds: Maximum delay in seconds
            distribution: Type of distribution ("normal", "uniform", "exponential")
        """
        if distribution == "normal":
            # Normal distribution centered between min and max
            mean = (min_seconds + max_seconds) / 2
            std_dev = (max_seconds - min_seconds) / 6  # ~99.7% within min-max
            delay = np.random.normal(mean, std_dev)
            # Clamp to ensure within bounds
            delay = max(min_seconds, min(max_seconds, delay))
        elif distribution == "exponential":
            # Exponential distribution (quicker actions with occasional longer pauses)
            scale = (max_seconds - min_seconds) / 3
            delay = min_seconds + np.random.exponential(scale)
            delay = min(delay, max_seconds)  # Cap at max
        else:  # uniform
            delay = random.uniform(min_seconds, max_seconds)
            
        await asyncio.sleep(delay)
        return delay
    
    @staticmethod
    async def typing_delay(text: str, wpm: float = 80.0, 
                          variance: float = 0.3) -> None:
        """
        Simulates human typing speed with variance and occasional pauses.
        
        Args:
            text: The text being "typed"
            wpm: Words per minute (average typing speed)
            variance: Variance factor for speed fluctuation
        """
        # Average word length in English is ~5 characters
        chars_per_minute = wpm * 5
        base_delay = 60.0 / chars_per_minute  # seconds per character
        
        for i in range(len(text)):
            # Add random variance to typing speed
            char_delay = base_delay * random.uniform(1 - variance, 1 + variance)
            
            # Occasional longer pause after punctuation
            if i > 0 and text[i-1] in ".,:;?!":
                char_delay *= random.uniform(2.0, 4.0)
                
            # Occasional pause to "think"
            if random.random() < 0.02:  # 2% chance of a thinking pause
                char_delay += random.uniform(1.0, 3.0)
                
            await asyncio.sleep(char_delay)
    
    @staticmethod
    def should_perform_action(probability: float) -> bool:
        """
        Determines if an action should be performed based on probability.
        
        Args:
            probability: Float between 0 and 1 representing probability
        
        Returns:
            Boolean indicating whether the action should be performed
        """
        return random.random() < probability
    
    @staticmethod
    def get_engagement_count(min_count: int = 1, max_count: int = 5) -> int:
        """
        Returns a random number with higher probability toward minimum values.
        
        Args:
            min_count: Minimum value
            max_count: Maximum value
            
        Returns:
            Integer count following a human-like distribution
        """
        # Using exponential distribution to favor lower values
        lambda_param = 1.5
        
        # Generate exponential distribution and scale to our range
        value = np.random.exponential(1/lambda_param)
        value = min(value, 3/lambda_param)  # Cap extreme values
        
        # Scale to range
        scaled_value = min_count + value * (max_count - min_count) / (3/lambda_param)
        return int(scaled_value)
    
    @staticmethod
    def select_weighted_choice(options: List[str], weights: Optional[List[float]] = None) -> str:
        """
        Selects an option based on weighted probabilities.
        
        Args:
            options: List of options to choose from
            weights: List of weights corresponding to options
            
        Returns:
            Selected option
        """
        if weights is None:
            return random.choice(options)
        return random.choices(options, weights=weights, k=1)[0]
    
    @staticmethod
    def get_scroll_parameters() -> Tuple[int, float]:
        """
        Generates human-like scroll parameters.
        
        Returns:
            Tuple of (scroll_distance, scroll_duration)
        """
        # Humans typically scroll in varied distances
        scroll_categories = ["small", "medium", "large"]
        scroll_weights = [0.3, 0.5, 0.2]
        
        scroll_type = RandomizationUtil.select_weighted_choice(scroll_categories, scroll_weights)
        
        if scroll_type == "small":
            distance = random.randint(300, 600)
            duration = random.uniform(0.3, 0.7)
        elif scroll_type == "medium":
            distance = random.randint(600, 1200)
            duration = random.uniform(0.5, 1.0)
        else:  # large
            distance = random.randint(1200, 2400)
            duration = random.uniform(0.7, 1.5)
            
        return distance, duration