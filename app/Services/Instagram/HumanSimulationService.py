from playwright.async_api import Page
import asyncio
import random
import time
from typing import Dict, Any, List, Optional, Tuple
from app.Services.Utils.RandomizationUtil import RandomizationUtil
from app.Services.Utils.BehaviorPatternUtil import BehaviorPatternUtil
from app.Services.Instagram.BrowsingService import BrowsingService
from app.Services.Instagram.EngagementService import EngagementService
from app.Services.Instagram.FeedInteractionService import FeedInteractionService
from app.Services.Instagram.HighlightMessagingService import HighlightMessagingService
from app.Services.Instagram.StoryMessagingService import StoryMessagingService
from app.Services.Instagram.DMService import DMService
from app.Services.Instagram.ProfileAnalysisService import ProfileAnalysisService
from config.settings import INSTAGRAM_URL

class HumanSimulationService:
    """
    Orchestrates various services to create realistic human-like behavior on Instagram.
    This service coordinates the sequence of actions to mimic natural user behavior.
    """
    
    def __init__(self, page: Page, behavior_type: str = "casual_browser"):
        """
        Initialize the human simulation service.
        
        Args:
            page: Playwright page instance
            behavior_type: Type of behavior pattern to use
        """
        self.page = page
        self.randomizer = RandomizationUtil()
        self.behavior_util = BehaviorPatternUtil()
        self.behavior_pattern = self.behavior_util.get_pattern(behavior_type)
        
        # Initialize component services
        self.browsing_service = BrowsingService(page)
        self.engagement_service = EngagementService(page)
        self.feed_service = FeedInteractionService(page)
        self.dm_service = DMService(page)
        self.profile_analysis = ProfileAnalysisService(page)
        
        # Popular hashtags by category for random browsing
        self.popular_hashtags = {
            "general": ["love", "instagood", "photooftheday", "fashion", "beautiful"],
            "travel": ["travel", "adventure", "wanderlust", "travelgram", "vacation"],
            "food": ["food", "foodporn", "yummy", "instafood", "delicious"],
            "fitness": ["fitness", "gym", "workout", "fitnessmotivation", "health"],
            "art": ["art", "artist", "artwork", "creative", "design"]
        }
        
        # Track actions for this session
        self.session_actions = {
            "start_time": time.time(),
            "feeds_browsed": 0,
            "profiles_visited": 0,
            "posts_viewed": 0,
            "posts_liked": 0,
            "users_followed": 0,
            "messages_sent": 0,
            "stories_viewed": 0,
            "hashtags_browsed": 0,
            "comments_posted": 0,
            "notifications_checked": 0,
            "searches_performed": 0,
            "reels_watched": 0
        }

    async def browse_hashtag(self, hashtag: str, duration_minutes: int = 2) -> Dict[str, Any]:
        """
        Browses posts under a specific hashtag.
        
        Args:
            hashtag: Hashtag to browse (without the # symbol)
            duration_minutes: Duration to spend browsing the hashtag
            
        Returns:
            Dictionary with hashtag browsing results
        """
        try:
            print(f"Browsing #{hashtag} hashtag...")
            hashtag_url = f"https://www.instagram.com/explore/tags/{hashtag}/"
            
            results = {
                "hashtag": hashtag,
                "duration_minutes": duration_minutes,
                "posts_viewed": 0,
                "posts_liked": 0,
                "profiles_visited": 0
            }
            
            # Navigate to hashtag page
            await self.page.goto(hashtag_url)
            await asyncio.sleep(random.uniform(2, 4))
            
            end_time = time.time() + (duration_minutes * 60)
            
            # Scroll and interact with hashtag posts
            while time.time() < end_time:
                # Scroll down
                await self.page.evaluate("window.scrollBy(0, Math.floor(Math.random() * 300) + 200);")
                await asyncio.sleep(random.uniform(1, 3))
                
                # 25% chance to like a post
                if random.random() < 0.25:
                    # Find and click a random post
                    posts = await self.page.query_selector_all("article a")
                    if posts and len(posts) > 0:
                        random_post = random.choice(posts)
                        await random_post.click()
                        await asyncio.sleep(random.uniform(2, 4))
                        
                        results["posts_viewed"] += 1
                        self.session_actions["posts_viewed"] += 1
                        
                        # Maybe like the post
                        if random.random() < 0.4:
                            like_button = await self.page.query_selector("svg[aria-label='Like']")
                            if like_button:
                                await like_button.click()
                                results["posts_liked"] += 1
                                self.session_actions["posts_liked"] += 1
                        
                        # 10% chance to view profile
                        if random.random() < 0.1:
                            profile_link = await self.page.query_selector("header a")
                            if profile_link:
                                username = await profile_link.get_attribute("href")
                                if username:
                                    username = username.strip("/").split("/")[-1]
                                    # Store current state to return later
                                    await profile_link.click()
                                    await asyncio.sleep(random.uniform(2, 4))
                                    
                                    results["profiles_visited"] += 1
                                    self.session_actions["profiles_visited"] += 1
                                    
                                    # Return to post
                                    await self.page.go_back()
                                    await asyncio.sleep(random.uniform(1, 2))
                        
                        # Close the post
                        close_button = await self.page.query_selector("svg[aria-label='Close']")
                        if close_button:
                            await close_button.click()
                            await asyncio.sleep(random.uniform(1, 2))
            
            print(f"Finished browsing #{hashtag}")
            self.session_actions["hashtags_browsed"] += 1
            
            return results
            
        except Exception as e:
            print(f"Error browsing hashtag #{hashtag}: {e}")
            return {
                "hashtag": hashtag,
                "error": str(e),
                "posts_viewed": 0,
                "posts_liked": 0,
                "profiles_visited": 0
            }
    
    async def simulate_natural_session(self, 
                                      target_usernames: List[str] = None, 
                                      session_duration_minutes: int = 30) -> Dict[str, Any]:
        """
        Simulates a natural Instagram session with various actions.
        
        Args:
            target_usernames: List of usernames to specifically interact with
            session_duration_minutes: Total session duration in minutes
            
        Returns:
            Dictionary with session results
        """
        session_end_time = time.time() + (session_duration_minutes * 60)
        target_usernames = target_usernames or []
        
        try:
            # Start with browsing the home feed
            await self._simulate_feed_browsing()
            
            # While we have time, alternate between different activities
            while time.time() < session_end_time:
                remaining_time = session_end_time - time.time()
                
                # Choose a random action based on remaining time
                if target_usernames and remaining_time > 60:
                    # Process a target username if we have any
                    if len(target_usernames) > 0:
                        username = target_usernames.pop(0)
                        await self._interact_with_target_user(username)
                else:
                    # Choose a random action
                    action = self._choose_next_action(remaining_time)
                    await self._perform_action(action)
                    
                    # Add some unpredictability to the session
                    if self.randomizer.should_perform_action(0.1):  # 10% chance
                        await self._simulate_user_distraction()
                
                # Log progress
                elapsed_minutes = (time.time() - self.session_actions["start_time"]) / 60
                print(f"Session in progress: {elapsed_minutes:.1f} minutes elapsed")
            
            # Calculate session statistics
            self.session_actions["duration_minutes"] = (time.time() - self.session_actions["start_time"]) / 60
            
            return self.session_actions
            
        except Exception as e:
            print(f"Error in natural session: {e}")
            self.session_actions["error"] = str(e)
            self.session_actions["duration_minutes"] = (time.time() - self.session_actions["start_time"]) / 60
            return self.session_actions
    
    async def _interact_with_target_user(self, username: str) -> None:
        """
        Interacts with a specific target user in a natural way.
        
        Args:
            username: Target username to interact with
        """
        try:
            # Clean up the username - remove any unexpected parameters or slashes
            username = username.split('?')[0].strip('/')
            
            if not username:  # Skip if username is empty
                print("Empty username, skipping...")
                return
                
            print(f"🔹 Interacting with target user: {username}")
            
            # Check if we're already on this profile
            current_url = self.page.url
            current_username = current_url.strip('/').split('/')[-1].split('?')[0]
            
            # Only navigate if we're not already on this profile
            if current_username.lower() != username.lower():
                # Navigate directly to the profile and wait for it to load
                await self.browsing_service.navigate_to_profile(username)
                
                # Wait for profile to load completely
                try:
                    # Wait for either the feed of posts or the private account indicator
                    await self.page.wait_for_selector("article, div[role='tablist'], h2", timeout=10000)
                    # Additional delay to ensure everything is loaded
                    await self.randomizer.human_delay(2, 4)
                except Exception as e:
                    print(f"Timeout waiting for profile to load: {e}")
            else:
                print(f"Already on {username}'s profile, continuing interaction")
            
            # Browse the profile naturally
            profile_data = await self.browsing_service.browse_profile(username, self.behavior_pattern)
            self.session_actions["profiles_visited"] += 1
            
            if profile_data.get("browsed", False):
                # Adjust behavior based on profile characteristics
                follower_count = profile_data.get("profile_data", {}).get("follower_count", 0)
                adjusted_pattern = self.behavior_util.adjust_for_account_size(
                    self.behavior_pattern, 
                    int(follower_count) if follower_count else 0
                )
                
                # View some posts if available
                posts_available = profile_data.get("profile_data", {}).get("posts_available", 0)
                if posts_available > 0:
                    # Open at least one post to view
                    await self._view_random_post()
                    
                    # Decide if we should engage further
                    if self.randomizer.should_perform_action(adjusted_pattern.get("like_probability", 0.3)):
                        # Engage with some posts
                        engagement_results = await self.engagement_service.engage_with_user_content(
                            username,
                            like_probability=adjusted_pattern.get("like_probability", 0.3),
                            follow_probability=adjusted_pattern.get("follow_probability", 0.1),
                            max_posts_to_like=adjusted_pattern.get("max_posts_per_profile", 2)
                        )
                        
                        # Update session stats
                        self.session_actions["posts_liked"] += engagement_results.get("posts_liked", 0)
                        if engagement_results.get("followed", False):
                            self.session_actions["users_followed"] += 1
            
            # Add some delay before next action
            await self.randomizer.human_delay(3, 8)
            
        except Exception as e:
            print(f"Error interacting with target user {username}: {e}")

    async def _view_random_post(self) -> None:
        """
        Opens and views a random post on the current profile.
        """
        try:
            # Find all post elements
            post_selectors = await self.page.query_selector_all("article a")
            
            if post_selectors and len(post_selectors) > 0:
                # Choose a random post
                random_post = random.choice(post_selectors)
                
                # Click on the post to open it
                await random_post.click()
                
                # Wait for post to open
                await self.page.wait_for_selector("time", timeout=5000)
                await self.randomizer.human_delay(1, 3)
                
                # Scroll through comments
                for _ in range(random.randint(2, 5)):
                    await self.page.evaluate("window.scrollBy(0, 300)")
                    await self.randomizer.human_delay(1, 3)
                
                # View post for a random amount of time
                view_time = random.randint(5, 15)
                print(f"Viewing post for {view_time} seconds")
                await asyncio.sleep(view_time)
                
                # Go back to profile
                await self.page.go_back()
                await self.randomizer.human_delay(1, 3)
                
                self.session_actions["posts_viewed"] += 1
        except Exception as e:
            print(f"Error viewing random post: {e}")
    
    def _choose_next_action(self, remaining_seconds: float) -> str:
        """
        Chooses the next action based on remaining time and behavior pattern.
        
        Args:
            remaining_seconds: Remaining session time in seconds
            
        Returns:
            Action name to perform
        """
        # Define actions with weights based on behavior pattern
        actions_with_weights = {
            "casual_browser": {
                "browse_feed": 0.35,        # Casual users spend most time on feed
                "browse_explore": 0.20,     # Moderate explore usage
                "random_profile": 0.10,     # Some profile browsing
                "discover_similar": 0.05,   # Occasionally discover similar accounts
                "check_notifications": 0.05,# Sometimes check notifications
                "watch_reels": 0.10,        # Sometimes watch reels
                "browse_hashtag": 0.10,     # Browse trending hashtags
                "search_content": 0.05      # Search for content occasionally
            },
            "power_user": {
                "browse_feed": 0.15,        # Less feed browsing for power users
                "browse_explore": 0.20,     # More explore content
                "random_profile": 0.15,     # Regular profile browsing
                "discover_similar": 0.15,   # More discovery of similar profiles
                "check_notifications": 0.10,# More frequent notification checks
                "watch_reels": 0.10,        # More reels watching
                "browse_hashtag": 0.10,     # Browse hashtags
                "search_content": 0.05      # Search for specific content
            },
            "content_creator": {
                "browse_feed": 0.10,        # Less feed browsing
                "browse_explore": 0.25,     # Heavy explore for inspiration
                "random_profile": 0.15,     # More profile analysis
                "discover_similar": 0.15,   # More discovery for research
                "check_notifications": 0.05,# Some notification checking
                "watch_reels": 0.10,        # Reels are important for content creators
                "browse_hashtag": 0.15,     # More hashtag research
                "search_content": 0.05      # Research content in their niche
            },
            "business_account": {
                "browse_feed": 0.10,        # Less personal feed browsing
                "browse_explore": 0.15,     # Less explore browsing
                "random_profile": 0.20,     # More profile analysis
                "discover_similar": 0.20,   # More competitor/industry research
                "check_notifications": 0.10,# Regular engagement checking
                "watch_reels": 0.05,        # Minimal reels usage
                "browse_hashtag": 0.15,     # Research trending hashtags in industry
                "search_content": 0.05      # Research industry topics
            }
        }
        
        # Get weights for the current behavior pattern or default to casual_browser
        pattern = self.behavior_pattern.get("type", "casual_browser")
        weights = actions_with_weights.get(pattern, actions_with_weights["casual_browser"])
        
        # Adjust weights based on remaining time
        if remaining_seconds < 120:  # Less than 2 minutes
            # Favor shorter actions when little time remains
            weights["browse_feed"] *= 1.5
            weights["browse_explore"] *= 1.5
            weights["random_profile"] *= 0.5
            weights["discover_similar"] *= 0.3
            weights["watch_reels"] *= 0.5
            weights["check_notifications"] *= 1.2
            weights["browse_hashtag"] *= 0.4
            weights["search_content"] *= 0.5
        elif remaining_seconds < 300:  # Less than 5 minutes
            # Slightly adjust for medium time
            weights["random_profile"] *= 1.2
            weights["discover_similar"] *= 0.8
        
        # Account for session history to avoid repetitive behavior
        last_actions = self.session_actions.get("last_actions", [])
        if last_actions and len(last_actions) >= 2:
            # If same action performed twice in a row, reduce its weight
            if last_actions[-1] == last_actions[-2]:
                if last_actions[-1] in weights:
                    weights[last_actions[-1]] *= 0.5
        
        # Normalize weights after adjustments
        total_weight = sum(weights.values())
        normalized_weights = {k: v/total_weight for k, v in weights.items()}
        
        # Choose action based on weighted probabilities
        actions = list(normalized_weights.keys())
        action_weights = [normalized_weights[action] for action in actions]
        
        selected_action = random.choices(actions, weights=action_weights, k=1)[0]
        
        # Track action history (keep last 3 actions)
        if "last_actions" not in self.session_actions:
            self.session_actions["last_actions"] = []
        
        self.session_actions["last_actions"].append(selected_action)
        if len(self.session_actions["last_actions"]) > 3:
            self.session_actions["last_actions"].pop(0)
        
        return selected_action
    
    async def _perform_action(self, action: str) -> None:
        """
        Performs a specific action.
        
        Args:
            action: Name of action to perform
        """
        if action == "browse_feed":
            await self._simulate_feed_browsing()
        elif action == "browse_explore":
            await self._simulate_explore_browsing()
        elif action == "random_profile":
            await self._simulate_random_profile_visit()
        elif action == "discover_similar":
            await self._simulate_discovering_similar_profiles()
        elif action == "check_notifications":
            await self._simulate_checking_notifications()
        elif action == "watch_reels":
            await self._simulate_watching_reels()
        elif action == "browse_hashtag":
            await self._simulate_hashtag_browsing()
        elif action == "search_content":
            await self._simulate_search_behavior()
    
    async def _simulate_feed_browsing(self) -> None:
        """Simulates browsing the home feed."""
        print("🔹 Browsing home feed")
        feed_results = await self.feed_service.browse_home_feed(
            duration_seconds=random.randint(60, 180),
            like_probability=self.behavior_pattern.get("like_probability", 0.2),
            browse_profile_probability=0.15
        )
        
        # Update session stats
        self.session_actions["feeds_browsed"] += 1
        self.session_actions["posts_viewed"] += feed_results.get("posts_viewed", 0)
        self.session_actions["posts_liked"] += feed_results.get("posts_liked", 0)
        self.session_actions["profiles_visited"] += feed_results.get("profiles_visited", 0)
    
    async def _simulate_explore_browsing(self) -> None:
        """Simulates browsing the explore/discover feed."""
        print("🔹 Browsing explore feed")
        explore_results = await self.feed_service.explore_discover_feed(
            duration_seconds=random.randint(90, 210),
            like_probability=self.behavior_pattern.get("like_probability", 0.15)
        )
        
        # Update session stats
        self.session_actions["feeds_browsed"] += 1
        self.session_actions["posts_viewed"] += explore_results.get("posts_viewed", 0)
        self.session_actions["posts_liked"] += explore_results.get("posts_liked", 0)
        self.session_actions["profiles_visited"] += explore_results.get("profiles_visited", 0)
    
    async def _simulate_random_profile_visit(self) -> None:
        """Simulates visiting a random profile from explore page."""
        try:
            print("🔹 Visiting random profile from explore")
            
            # Navigate to explore
            await self.browsing_service.navigate_to_explore()
            await self.randomizer.human_delay(2, 4)
            
            # Scroll to see more content
            for _ in range(random.randint(3, 6)):
                await self.page.evaluate("window.scrollBy(0, 500)")
                await self.randomizer.human_delay(1, 2)
            
            # Improved method to find profiles
            usernames = await self.page.evaluate("""() => {
                // Better selector targeting username elements
                const usernameSelectorOptions = [
                    'span._aap6._aap7._aap8', // Username in post headers
                    'a._ab8w._ab94._ab99._ab9h._ab9m._ab9o span', // Username in comments
                    'a[href^="/"][role="link"]:not([href*="/p/"]):not([href*="/explore/"]):not([href="/"])' // Direct profile links
                ];
                
                let foundUsernames = [];
                
                // Try different selectors
                for (const selector of usernameSelectorOptions) {
                    try {
                        const elements = document.querySelectorAll(selector);
                        for (const el of elements) {
                            let username;
                            
                            if (el.tagName === 'A') {
                                // For <a> tags, extract username from href
                                const href = el.getAttribute('href');
                                if (href && href.startsWith('/') && href.length > 1) {
                                    username = href.replace(/^\/|\/$/g, '').split('?')[0];
                                }
                            } else {
                                // For text elements, use the text content
                                username = el.textContent.trim();
                            }
                            
                            // Validate username
                            if (username && 
                                username.length > 2 && 
                                !username.includes(' ') &&
                                !username.includes('/') &&
                                !['explore', 'p', 'reels', 'stories', 'direct'].includes(username)) {
                                foundUsernames.push(username);
                            }
                        }
                    } catch (e) {
                        console.error("Error with selector:", selector, e);
                    }
                }
                
                // Extract usernames from post headers as a fallback
                if (foundUsernames.length < 2) {
                    try {
                        const postHeaders = document.querySelectorAll('article header');
                        for (const header of postHeaders) {
                            const links = header.querySelectorAll('a[role="link"]');
                            for (const link of links) {
                                const href = link.getAttribute('href');
                                if (href && href.startsWith('/') && href.length > 1 && !href.includes('/p/')) {
                                    const username = href.replace(/^\/|\/$/g, '').split('?')[0];
                                    if (username && username.length > 2) {
                                        foundUsernames.push(username);
                                    }
                                }
                            }
                        }
                    } catch (e) {
                        console.error("Error extracting from post headers:", e);
                    }
                }
                
                // Remove duplicates and limit results
                return [...new Set(foundUsernames)].slice(0, 10);
            }""")
            
            print(f"Found usernames: {usernames}")
            
            if usernames and len(usernames) > 0:
                valid_usernames = [u for u in usernames if u and len(u) > 0 and not u.startswith('echooo.ai')]
                
                if valid_usernames:
                    # Choose a random username that's not our target account
                    random_username = random.choice(valid_usernames)
                    print(f"Selected random username: {random_username}")
                    
                    # Browse the random profile
                    await self._interact_with_target_user(random_username)
                else:
                    print("No valid usernames found on explore page")
                    # Alternative: Use Instagram search to find a random account
                    await self._find_random_account_via_search()
            else:
                print("No usernames found on explore page")
                # Fallback to search
                await self._find_random_account_via_search()
            
            # Return to feed
            await self.browsing_service.return_to_home_feed()
            
        except Exception as e:
            print(f"Error in random profile visit: {e}")
            # Try to return to feed if there was an error
            await self.browsing_service.return_to_home_feed()

    async def _find_random_account_via_search(self) -> None:
        """
        Fallback method to find a random account via search.
        Uses common search terms to find profiles.
        """
        try:
            # Random search terms
            search_terms = ["travel", "food", "fitness", "art", "photography", "music", "fashion", "design"]
            search_term = random.choice(search_terms)
            
            print(f"Searching for random accounts using term: {search_term}")
            
            # Click the search icon
            await self.page.click('svg[aria-label="Search"]')
            await self.randomizer.human_delay(1, 2)
            
            # Enter search term
            search_input = await self.page.query_selector('input[placeholder="Search"]')
            if search_input:
                await search_input.fill(search_term)
                await self.randomizer.human_delay(1, 2)
                
                # Wait for search results to load
                await self.page.wait_for_selector('a[role="link"]', timeout=5000)
                await self.randomizer.human_delay(2, 3)
                
                # Get profile links from search results
                usernames = await self.page.evaluate("""(searchTerm) => {
                    const profileLinks = Array.from(document.querySelectorAll('a[role="link"]'))
                        .filter(link => {
                            const href = link.getAttribute('href');
                            return href && 
                                href.startsWith('/') && 
                                !href.includes('/explore/') &&
                                !href.includes('/p/') &&
                                href.length > 1;
                        });
                    
                    return profileLinks.map(link => {
                        return link.getAttribute('href').replace(/^\/|\/$/g, '').split('?')[0];
                    }).filter(username => 
                        username && 
                        username.length > 2 && 
                        !username.includes('explore') &&
                        !username.includes('stories') &&
                        !username.includes('direct') &&
                        !username.includes('echooo.ai')
                    );
                }""", search_term)
                
                if usernames and len(usernames) > 0:
                    random_username = random.choice(usernames)
                    print(f"Found account via search: {random_username}")
                    
                    # Browse the random profile
                    await self._interact_with_target_user(random_username)
                else:
                    print("No accounts found via search")
            
            self.session_actions["searches_performed"] += 1
            
        except Exception as e:
            print(f"Error finding account via search: {e}")
    
    async def _simulate_discovering_similar_profiles(self) -> None:
        """Simulates discovering and exploring similar profiles."""
        try:
            print("🔹 Discovering similar profiles")
            
            # First find a suitable base profile from explore
            await self.browsing_service.navigate_to_explore()
            await self.randomizer.human_delay(2, 4)
            
            # Find a base profile
            base_usernames = await self.page.evaluate("""() => {
                const usernameElements = document.querySelectorAll('a[role="link"]');
                const usernames = [];
                
                for (const el of usernameElements) {
                    const href = el.getAttribute('href');
                    if (href && href.startsWith('/') && !href.includes('/p/') && !href.includes('/explore/')) {
                        usernames.push(href.replace('/', '').replace('/', ''));
                    }
                    
                    if (usernames.length >= 3) break;
                }
                
                return [...new Set(usernames)]; // Remove duplicates
            }""")
            
            if base_usernames and len(base_usernames) > 0:
                base_username = random.choice(base_usernames)
                
                # Find similar profiles
                similar_profiles = await self.feed_service.discover_similar_profiles(
                    base_username, count=random.randint(1, 2)
                )
                
                # Visit similar profiles
                for username in similar_profiles:
                    await self._interact_with_target_user(username)
            
            # Return to feed
            await self.browsing_service.return_to_home_feed()
            
        except Exception as e:
            print(f"Error discovering similar profiles: {e}")
    
    async def _simulate_user_distraction(self) -> None:
        """
        Simulates a user getting distracted during their session.
        This creates more realistic usage patterns.
        """
        print("🔹 User distraction simulation")
        
        # Choose a distraction type
        distraction_type = random.choice(["pause", "idle", "return_to_feed", "scroll_idle"])
        
        if distraction_type == "pause":
            # Simulate user pausing for a moment (maybe checking phone, etc)
            pause_time = random.uniform(5, 20)
            print(f"User paused for {pause_time:.1f} seconds")
            await asyncio.sleep(pause_time)
            
        elif distraction_type == "idle":
            # Simulate user leaving the app idle for a bit
            idle_time = random.uniform(10, 30)
            print(f"User idle for {idle_time:.1f} seconds")
            await asyncio.sleep(idle_time)
            
        elif distraction_type == "return_to_feed":
            # Simulate user suddenly going back to feed
            print("User abruptly returned to feed")
            await self.browsing_service.return_to_home_feed()
            await self.randomizer.human_delay(1, 3)
            
        elif distraction_type == "scroll_idle":
            # Simulate user idly scrolling without much interaction
            scroll_count = random.randint(3, 8)
            print(f"User idly scrolling {scroll_count} times")
            
            for _ in range(scroll_count):
                await self.page.evaluate("window.scrollBy(0, 300)")
                await asyncio.sleep(random.uniform(1, 3))

    async def _simulate_checking_notifications(self) -> None:
        """Simulates checking notifications."""
        try:
            print("🔹 Checking notifications")
            
            # Click on notifications icon
            notification_button = await self.page.query_selector('svg[aria-label="Notifications"]')
            if notification_button:
                await notification_button.click()
                await self.randomizer.human_delay(2, 4)
                
                # Scroll through notifications
                scroll_count = random.randint(1, 5)
                for _ in range(scroll_count):
                    await self.page.evaluate("window.scrollBy(0, 300)")
                    await self.randomizer.human_delay(1, 3)
                
                # 30% chance to click on a notification
                if random.random() < 0.3:
                    notifications = await self.page.query_selector_all('div[role="button"]')
                    if notifications and len(notifications) > 0:
                        # Click a random notification
                        random_notification = random.choice(notifications)
                        await random_notification.click()
                        await self.randomizer.human_delay(3, 7)
                        
                        # Go back to feed
                        await self.browsing_service.return_to_home_feed()
                else:
                    # Return to feed by clicking home icon
                    home_button = await self.page.query_selector('svg[aria-label="Home"]')
                    if home_button:
                        await home_button.click()
                        
                self.session_actions["notifications_checked"] += 1
                
        except Exception as e:
            print(f"Error checking notifications: {e}")
            # Try to return to feed if there was an error
            await self.browsing_service.return_to_home_feed()

    async def _simulate_watching_reels(self) -> None:
        """Simulates watching reels."""
        try:
            print("🔹 Watching reels")
            
            # Navigate to reels
            reels_button = await self.page.query_selector('svg[aria-label="Reels"]')
            if reels_button:
                await reels_button.click()
                await self.randomizer.human_delay(3, 5)
                
                # Watch a random number of reels
                reels_count = random.randint(2, 6)
                for i in range(reels_count):
                    print(f"Watching reel {i+1}/{reels_count}")
                    
                    # Watch the reel for a random duration
                    watch_time = random.uniform(5, 20)
                    await asyncio.sleep(watch_time)
                    
                    # 20% chance to like a reel
                    if random.random() < 0.2:
                        like_button = await self.page.query_selector('svg[aria-label="Like"]')
                        if like_button:
                            await like_button.click()
                            await self.randomizer.human_delay(1, 2)
                            self.session_actions["posts_liked"] += 1
                    
                    # 5% chance to check a profile
                    if random.random() < 0.05:
                        profile_link = await self.page.query_selector('a[role="link"]')
                        if profile_link:
                            await profile_link.click()
                            await self.randomizer.human_delay(3, 6)
                            self.session_actions["profiles_visited"] += 1
                            
                            # Go back to reels
                            await self.page.go_back()
                            await self.randomizer.human_delay(1, 2)
                    
                    # Swipe to next reel
                    if i < reels_count - 1:
                        await self.page.evaluate("window.scrollBy(0, window.innerHeight)")
                        await self.randomizer.human_delay(1, 3)
                
                # Return to feed
                await self.browsing_service.return_to_home_feed()
                
                self.session_actions["reels_watched"] += reels_count
                
        except Exception as e:
            print(f"Error watching reels: {e}")
            # Try to return to feed if there was an error
            await self.browsing_service.return_to_home_feed()

    async def _simulate_hashtag_browsing(self) -> None:
        """Simulates browsing random hashtags."""
        try:
            print("🔹 Browsing hashtags")
            
            # Select a random category and hashtag
            category = random.choice(list(self.popular_hashtags.keys()))
            hashtag = random.choice(self.popular_hashtags[category])
            
            print(f"Selected category: {category}, hashtag: #{hashtag}")
            
            # Browse the hashtag
            browse_results = await self.browse_hashtag(
                hashtag=hashtag,
                duration_minutes=random.uniform(1, 3)
            )
            
            # Update session metrics
            self.session_actions["posts_viewed"] += browse_results.get("posts_viewed", 0)
            self.session_actions["posts_liked"] += browse_results.get("posts_liked", 0)
            self.session_actions["profiles_visited"] += browse_results.get("profiles_visited", 0)
            
            # Return to feed
            await self.browsing_service.return_to_home_feed()
            
        except Exception as e:
            print(f"Error browsing hashtags: {e}")
            # Try to return to feed if there was an error
            await self.browsing_service.return_to_home_feed()

    async def _simulate_search_behavior(self) -> None:
        """Simulates search behavior for content, hashtags, or users."""
        try:
            print("🔹 Simulating search behavior")
            
            # Click the search icon
            search_icon = await self.page.query_selector('svg[aria-label="Search"]')
            if search_icon:
                await search_icon.click()
                await self.randomizer.human_delay(1, 3)
                
                # Determine what to search for
                search_type = random.choice(["user", "hashtag", "location"])
                
                if search_type == "user":
                    # Popular usernames to search for
                    popular_users = ["natgeo", "instagram", "nike", "nasa", "travel"]
                    search_term = random.choice(popular_users)
                elif search_type == "hashtag":
                    # Popular hashtags to search for
                    category = random.choice(list(self.popular_hashtags.keys()))
                    search_term = self.popular_hashtags[category][0]
                else:  # location
                    # Popular locations to search for
                    locations = ["new york", "los angeles", "paris", "london", "tokyo"]
                    search_term = random.choice(locations)
                
                print(f"Searching for {search_type}: {search_term}")
                
                # Type the search term
                search_input = await self.page.query_selector('input[placeholder="Search"]')
                if search_input:
                    # Type slowly like a human
                    for char in search_term:
                        await search_input.type(char)
                        await asyncio.sleep(random.uniform(0.1, 0.3))
                    
                    await self.randomizer.human_delay(1, 3)
                    
                    # Wait for search results and click on one
                    await self.page.wait_for_selector('a[role="link"]', timeout=5000)
                    await self.randomizer.human_delay(1, 2)
                    
                    # Click on a search result
                    search_results = await self.page.query_selector_all('a[role="link"]')
                    if search_results and len(search_results) > 0:
                        # Choose a random result from the first few
                        max_index = min(3, len(search_results) - 1)
                        result_index = random.randint(0, max_index)
                        await search_results[result_index].click()
                        await self.randomizer.human_delay(2, 4)
                        
                        # Browse the content for a bit
                        await asyncio.sleep(random.uniform(5, 15))
                        
                        # If it's a profile, maybe view some content
                        current_url = self.page.url
                        if "/p/" not in current_url and "/explore/tags/" not in current_url:
                            # Likely a profile page, maybe view a post
                            if random.random() < 0.5:
                                await self._view_random_post()
                    
                    self.session_actions["searches_performed"] += 1
            
            # Return to feed
            await self.browsing_service.return_to_home_feed()
            
        except Exception as e:
            print(f"Error during search behavior: {e}")
            # Try to return to feed if there was an error
            await self.browsing_service.return_to_home_feed()

    async def send_message_with_natural_behavior(self, 
                                          username: str, 
                                          message: str, 
                                          pre_engagement_time: int = 120,
                                          messaging_method: str = "auto") -> Dict[str, Any]:
        """
        Sends a message to a user after some natural browsing behavior.
        
        Args:
            username: Target username to message
            message: Message to send
            pre_engagement_time: Time to spend browsing before sending message (in seconds)
            messaging_method: Method to use for messaging ('dm', 'story', 'highlight', or 'auto')
            
        Returns:
            Dictionary with results
        """
        try:
            print(f"🔹 Natural messaging simulation for: {username}")
            result = {
                "username": username,
                "status": False,
                "sent_via": None,
                "error_code": None,
                "error_reason": None
            }
            
            # First interact naturally with the profile
            # Using ProfileAnalysisService instead of browsing_service for reliable profile data
            profile_analysis = ProfileAnalysisService(self.page)
            
            # Navigate to profile and analyze it
            await self.navigate_to_user_profile(username)
            profile_data = await profile_analysis.check_profile(username)
            self.session_actions["profiles_visited"] += 1
            
            if not profile_data.get("is_public", False):
                result["error_code"] = "PRIVATE_PROFILE"
                result["error_reason"] = "User profile is private"
                return result
                
            # Adjust behavior based on profile characteristics
            is_public = profile_data.get("is_public", False)
            can_dm = profile_data.get("can_dm", False)
            has_story = profile_data.get("has_story", False)
            has_highlights = profile_data.get("has_highlights", False)
            
            # Simulate pre-engagement natural behavior
            engagement_time = random.randint(int(pre_engagement_time * 0.7), int(pre_engagement_time * 1.3))
            
            # Engage with some posts before messaging
            if is_public and engagement_time > 30:
                # Engage with some posts
                engagement_results = await self.engagement_service.engage_with_user_content(
                    username,
                    like_probability=self.behavior_pattern.get("like_probability", 0.4),
                    follow_probability=self.behavior_pattern.get("follow_probability", 0.05),
                    max_posts_to_like=self.behavior_pattern.get("max_posts_per_profile", 1)
                )
                
                # Update session stats
                self.session_actions["posts_liked"] += engagement_results.get("posts_liked", 0)
                if engagement_results.get("followed", False):
                    self.session_actions["users_followed"] += 1
            
            # Now try to send the message using the appropriate method
            # In auto mode, prioritize highlight > story > dm as per requirements
            if messaging_method == "auto":
                if has_highlights:
                    messaging_method = "highlight"
                elif has_story:
                    messaging_method = "story"
                elif can_dm:
                    messaging_method = "dm"
                else:
                    result["error_code"] = "NO_MESSAGING_OPTION"
                    result["error_reason"] = "No available messaging options for this user"
                    return result
            
            # Try sending via chosen method, with cascading fallbacks
            if messaging_method == "highlight":
                highlight_service = HighlightMessagingService(self.page)
                status, error_code, error_reason = await highlight_service.reply_to_highlight(message)
                
                if status:
                    result["status"] = True
                    result["sent_via"] = "Highlight"
                    self.session_actions["messages_sent"] += 1
                    return result
                elif has_story:  # Fallback to story if highlight fails
                    messaging_method = "story"
                elif can_dm:  # Fallback to DM if no story
                    messaging_method = "dm"
                else:
                    result["error_code"] = error_code
                    result["error_reason"] = error_reason
                    return result
            
            if messaging_method == "story":
                story_service = StoryMessagingService(self.page)
                status, error_code, error_reason = await story_service.reply_to_story(message)
                
                if status:
                    result["status"] = True
                    result["sent_via"] = "Story"
                    self.session_actions["messages_sent"] += 1
                    return result
                elif can_dm:  # Fallback to DM if story fails
                    messaging_method = "dm"
                else:
                    result["error_code"] = error_code
                    result["error_reason"] = error_reason
                    return result
            
            if messaging_method == "dm":
                from app.Services.Instagram.DMService import DMService
                dm_service = DMService(self.page)
                status, error_code, error_reason = await dm_service.send_message(message)
                
                if status:
                    result["status"] = True
                    result["sent_via"] = "DM"
                    self.session_actions["messages_sent"] += 1
                    return result
                else:
                    result["error_code"] = error_code
                    result["error_reason"] = error_reason
                    return result
            
            # Random delay after sending message
            await self.randomizer.human_delay(3, 8)
            
            return result
            
        except Exception as e:
            print(f"Error in natural messaging for {username}: {e}")
            return {
                "username": username,
                "status": False,
                "sent_via": None,
                "error_code": "EXCEPTION",
                "error_reason": str(e)
            }
        
    async def navigate_to_user_profile(self, username: str) -> bool:
        """
        Navigate to a user's Instagram profile
        
        Args:
            username: Instagram username to navigate to
            
        Returns:
            Boolean indicating success
        """
        try:
            profile_url = f"{INSTAGRAM_URL}/{username}/"
            current_url = self.page.url
            
            # Only navigate if we're not already on the profile
            if not (current_url.startswith(profile_url) or current_url.startswith(profile_url.rstrip('/'))):
                await self.page.goto(profile_url)
                await self.randomizer.human_delay(2, 4)
                    
            return True
            
        except Exception as e:
            print(f"⚠️ Error navigating to profile {username}: {e}")
            return False