from playwright.async_api import Page
import asyncio
import random
from typing import Dict, Any, List, Optional
from app.Services.Utils.RandomizationUtil import RandomizationUtil
from app.Services.Instagram.BrowsingService import BrowsingService
from app.Services.Instagram.EngagementService import EngagementService

class FeedInteractionService:
    """
    Service for naturally interacting with Instagram feed content,
    exploring suggestions, and simulating organic discovery behavior.
    """
    
    def __init__(self, page: Page):
        """
        Initialize the feed interaction service.
        
        Args:
            page: Playwright page instance
        """
        self.page = page
        self.randomizer = RandomizationUtil()
        self.browsing_service = BrowsingService(page)
        self.engagement_service = EngagementService(page)
    
    async def browse_home_feed(self, 
                              duration_seconds: int = 120,
                              like_probability: float = 0.2,
                              browse_profile_probability: float = 0.15) -> Dict[str, Any]:
        """
        Browses the home feed in a human-like way.
        
        Args:
            duration_seconds: How long to browse the feed
            like_probability: Probability of liking posts
            browse_profile_probability: Probability of visiting a post creator's profile
            
        Returns:
            Dictionary with browsing results
        """
        results = {
            "posts_viewed": 0,
            "posts_liked": 0,
            "profiles_visited": 0,
            "time_spent": 0
        }
        
        try:
            # Navigate to home feed
            await self.page.goto("https://www.instagram.com/")
            await self.randomizer.human_delay(2, 4)
            
            start_time = asyncio.get_event_loop().time()
            current_time = start_time
            
            # Browse until time is up
            while current_time - start_time < duration_seconds:
                # View current post
                results["posts_viewed"] += 1
                
                # Decide whether to like the post
                if self.randomizer.should_perform_action(like_probability):
                    like_success = await self.engagement_service.like_post()
                    if like_success:
                        results["posts_liked"] += 1
                
                # Get username of post creator
                username = await self._get_current_post_username()
                
                # Decide whether to visit the profile
                if username and self.randomizer.should_perform_action(browse_profile_probability):
                    # Remember current position in feed
                    current_position = await self.page.evaluate("window.scrollY")
                    
                    # Visit profile
                    await self.page.click(f'a[href="/{username}/"]')
                    await self.randomizer.human_delay(2, 4)
                    
                    # Browse profile briefly
                    await self.browsing_service.scroll_profile()
                    await self.randomizer.human_delay(3, 8)
                    
                    results["profiles_visited"] += 1
                    
                    # Return to feed
                    await self.browsing_service.return_to_home_feed()
                    await self.randomizer.human_delay(1, 2)
                    
                    # Try to restore position
                    await self.page.evaluate(f"window.scrollTo(0, {current_position})")
                    await self.randomizer.human_delay(1, 2)
                
                # Scroll to next post in feed
                scroll_distance = random.randint(500, 800)
                await self.page.evaluate(f"window.scrollBy({{top: {scroll_distance}, left: 0, behavior: 'smooth'}});")
                
                # Wait realistic time to view content
                view_time = random.uniform(3, 15)
                await asyncio.sleep(view_time)
                
                current_time = asyncio.get_event_loop().time()
            
            results["time_spent"] = current_time - start_time
            return results
            
        except Exception as e:
            print(f"Error browsing home feed: {e}")
            current_time = asyncio.get_event_loop().time()
            results["time_spent"] = current_time - start_time
            results["error"] = str(e)
            return results
    
    async def _get_current_post_username(self) -> Optional[str]:
        """
        Gets the username of the creator of the current post in view.
        
        Returns:
            Username string or None if not found
        """
        try:
            username = await self.page.evaluate("""() => {
                const usernameElements = document.querySelectorAll('a[role="link"]');
                for (const el of usernameElements) {
                    // Username links typically start with "/"
                    const href = el.getAttribute('href');
                    if (href && href.startsWith('/') && !href.includes('/p/') && !href.includes('/explore/')) {
                        return href.replace('/', '').replace('/', '');
                    }
                }
                return null;
            }""")
            
            return username
        except Exception as e:
            print(f"Error getting post username: {e}")
            return None
    
    async def explore_discover_feed(self, 
                                   duration_seconds: int = 180,
                                   like_probability: float = 0.15) -> Dict[str, Any]:
        """
        Explores the discover/explore feed to find new content.
        
        Args:
            duration_seconds: How long to browse explore feed
            like_probability: Probability of liking posts
            
        Returns:
            Dictionary with exploration results
        """
        results = {
            "posts_viewed": 0,
            "posts_liked": 0,
            "profiles_visited": 0,
            "time_spent": 0
        }
        
        try:
            # Navigate to explore page
            await self.browsing_service.navigate_to_explore()
            
            start_time = asyncio.get_event_loop().time()
            current_time = start_time
            
            # Browse until time is up
            while current_time - start_time < duration_seconds:
                # Scroll to see more content
                scroll_distance, scroll_duration = self.randomizer.get_scroll_parameters()
                await self.page.evaluate(f"window.scrollBy({{top: {scroll_distance}, left: 0, behavior: 'smooth'}});")
                await asyncio.sleep(scroll_duration)
                
                # Occasionally open a post
                if random.random() < 0.4:
                    # Find all post thumbnails
                    post_thumbnails = await self.page.query_selector_all('div[role="button"] img')
                    
                    if post_thumbnails and len(post_thumbnails) > 0:
                        # Click on a random post
                        random_post = random.choice(post_thumbnails)
                        await random_post.click()
                        await self.randomizer.human_delay(2, 4)
                        
                        results["posts_viewed"] += 1
                        
                        # View the post for a random time
                        view_time = random.uniform(4, 12)
                        await asyncio.sleep(view_time)
                        
                        # Maybe like the post
                        if self.randomizer.should_perform_action(like_probability):
                            like_success = await self.engagement_service.like_post()
                            if like_success:
                                results["posts_liked"] += 1
                        
                        # 10% chance to visit profile
                        if random.random() < 0.1:
                            # Click on username
                            username_link = await self.page.query_selector('header a')
                            if username_link:
                                await username_link.click()
                                await self.randomizer.human_delay(2, 4)
                                
                                # Brief profile browsing
                                await self.browsing_service.scroll_profile()
                                await self.randomizer.human_delay(3, 8)
                                
                                results["profiles_visited"] += 1
                                
                                # Return to explore
                                await self.page.go_back()
                                await self.randomizer.human_delay(1.5, 3)
                        
                        # Close the post
                        await self.page.keyboard.press('Escape')
                        await self.randomizer.human_delay(1, 2)
                
                current_time = asyncio.get_event_loop().time()
            
            results["time_spent"] = current_time - start_time
            return results
            
        except Exception as e:
            print(f"Error exploring discover feed: {e}")
            current_time = asyncio.get_event_loop().time()
            results["time_spent"] = current_time - start_time
            results["error"] = str(e)
            return results
    
    async def discover_similar_profiles(self, username: str, count: int = 3) -> List[str]:
        """
        Discovers profiles similar to a given username.
        
        Args:
            username: Base username to find similar profiles
            count: Number of similar profiles to find
            
        Returns:
            List of similar usernames
        """
        similar_profiles = []
        
        try:
            # Navigate to profile
            await self.page.goto(f"https://www.instagram.com/{username}/")
            await self.randomizer.human_delay(2, 4)
            
            # Click on followers to see related accounts
            followers_link = await self.page.query_selector('a[href$="/followers/"]')
            if followers_link:
                await followers_link.click()
                await self.randomizer.human_delay(2, 3)
                
                # Extract usernames from followers modal
                usernames = await self.page.evaluate("""() => {
                    const usernameElements = document.querySelectorAll('div[role="dialog"] a');
                    const usernames = [];
                    
                    for (const el of usernameElements) {
                        const href = el.getAttribute('href');
                        if (href && href.startsWith('/') && !href.includes('/p/')) {
                            usernames.push(href.replace('/', '').replace('/', ''));
                        }
                        
                        if (usernames.length >= 10) break;
                    }
                    
                    return usernames;
                }""")
                
                # Close the modal
                await self.page.keyboard.press('Escape')
                await self.randomizer.human_delay(1, 2)
                
                # Select random profiles from the list
                if usernames and len(usernames) > 0:
                    similar_profiles = random.sample(usernames, min(count, len(usernames)))
            
            return similar_profiles
            
        except Exception as e:
            print(f"Error discovering similar profiles: {e}")
            return similar_profiles