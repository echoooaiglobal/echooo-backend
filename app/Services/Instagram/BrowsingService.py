from playwright.async_api import Page
import asyncio
import random
from typing import Dict, Any
from app.Services.Utils.RandomizationUtil import RandomizationUtil
from config.settings import settings
from urllib.parse import urlparse

class BrowsingService:
    """
    Service for simulating human-like browsing behavior on Instagram
    including scrolling, viewing posts, and navigating profiles.
    """
    
    def __init__(self, page: Page):
        """
        Initialize the browsing service.
        
        Args:
            page: Playwright page instance
        """
        self.page = page
        self.randomizer = RandomizationUtil()
    
    async def navigate_to_profile(self, username: str) -> bool:
        """
        Navigate to a user's Instagram profile
        
        Args:
            username: Instagram username to navigate to
            
        Returns:
            Boolean indicating success
        """

        def normalize_url(url: str) -> str:
            return urlparse(url).path.rstrip('/')
        try:
            profile_url = f"{settings.INSTAGRAM_URL}/{username}/"
            current_url = self.page.url
            
            # Only navigate if we're not already on the profile
            if normalize_url(current_url) != normalize_url(profile_url):
                # await self.page.goto(profile_url, wait_until='networkidle')
                await self.page.goto(profile_url, wait_until='domcontentloaded')
                await self.randomizer.human_delay(2, 4)
                    
            return True
            
        except Exception as e:
            print(f"⚠️ Error navigating to profile {username}: {e}")
            return False
    
    async def scroll_feed(self, min_scrolls: int = 3, max_scrolls: int = 8, 
                         read_captions: bool = True) -> None:
        """
        Simulates scrolling through Instagram feed in a human-like way.
        
        Args:
            min_scrolls: Minimum number of scroll actions
            max_scrolls: Maximum number of scroll actions
            read_captions: Whether to pause on posts to "read" captions
        """
        num_scrolls = random.randint(min_scrolls, max_scrolls)
        
        for _ in range(num_scrolls):
            # Get random scroll parameters
            scroll_distance, scroll_duration = self.randomizer.get_scroll_parameters()
            
            # Execute scroll with smooth motion
            await self.page.evaluate(
                f"window.scrollBy({{top: {scroll_distance}, left: 0, behavior: 'smooth'}});"
            )
            
            # Wait for content to load
            await asyncio.sleep(scroll_duration)
            
            # Sometimes pause to "read" content
            if read_captions and random.random() < 0.6:
                read_time = random.uniform(2, 8)  # 2-8 seconds to read
                await asyncio.sleep(read_time)
    
    async def view_stories(self, max_stories: int = 5) -> bool:
        """
        Views Instagram stories if available.
        
        Args:
            max_stories: Maximum number of stories to view
            
        Returns:
            Boolean indicating whether stories were viewed
        """
        try:
            # Check if stories are available
            stories_available = await self.page.evaluate("""() => {
                const storyElements = document.querySelectorAll('div[role="button"][tabindex="0"]');
                for (const el of storyElements) {
                    if (el.innerHTML.includes('story')) {
                        return true;
                    }
                }
                return false;
            }""")
            
            if not stories_available:
                return False
                
            # Click on story
            await self.page.click('div[role="button"][tabindex="0"]')
            await self.randomizer.human_delay(1.5, 3)
            
            # Watch a random number of stories
            stories_to_watch = random.randint(1, max_stories)
            for _ in range(stories_to_watch):
                # Random viewing time for each story (3-8 seconds)
                view_time = random.uniform(3, 8)
                await asyncio.sleep(view_time)
                
                # 80% chance to continue to next story, otherwise exit
                if random.random() < 0.8:
                    # Click to next story
                    await self.page.click('button[aria-label="Next"]')
                    await self.randomizer.human_delay(0.5, 1.5)
                else:
                    # Exit stories
                    await self.page.click('button[aria-label="Close"]')
                    await self.randomizer.human_delay(1, 2)
                    break
                    
            return True
            
        except Exception as e:
            print(f"Error viewing stories: {e}")
            return False

    async def browse_profile(self, username: str, behavior_pattern: Dict[str, Any]) -> Dict[str, Any]:
        """
        Browses an Instagram profile in a human-like way.

        Args:
            username: Instagram username to browse
            behavior_pattern: Dictionary containing behavior parameters

        Returns:
            Dictionary with browsing results and profile information
        """
        try:

            await self.navigate_to_profile(username)

            profile_data = await self._extract_profile_data()
            print(f'profile_data: {profile_data}')

            # If profile is private, skip story, scroll, and post interaction
            if profile_data.get("is_public", True) is False:
                return {
                    "username": username,
                    "profile_data": profile_data,
                    "browsed": True,
                    "browse_time": 0
                }

            print(f'processing story 1')
            if profile_data.get("has_story", False) and self.randomizer.should_perform_action(
                    behavior_pattern.get("view_stories_probability", 0.5)):
                print(f'processing story 2')
                await self.view_stories(max_stories=3)

            time_range = behavior_pattern.get("avg_time_per_profile", [20, 60])
            browse_time = random.uniform(time_range[0], time_range[1])
            total_browse_time = min(browse_time, 30)
            print(f'total_browse_time: {total_browse_time}')
            start_time = asyncio.get_event_loop().time()
            elapsed_time = 0

            while elapsed_time < total_browse_time:
                await self.scroll_profile()  # Scroll
                await self.randomizer.human_delay(1, 3)  # Pause between scrolls
                print(f'processing post 1')
                if self.randomizer.should_perform_action(behavior_pattern.get("open_post_probability", 0.3)):
                    print(f'processing post 2')
                    await self.view_random_post()
                    await self.randomizer.human_delay(1, 2)  # Small pause after viewing post

                elapsed_time = asyncio.get_event_loop().time() - start_time

            return {
                "username": username,
                "profile_data": profile_data,
                "browsed": True,
                "browse_time": elapsed_time
            }

        except Exception as e:
            print(f"Error browsing profile {username}: {e}")
            return {
                "username": username,
                "browsed": False,
                "error": str(e)
            }


    
    async def _extract_profile_data(self) -> Dict[str, Any]:
        try:
            is_private = await self.page.locator("text=This account is private").is_visible()
            can_dm = await self.page.locator("xpath=//div[@role='button' and contains(., 'Message')]").is_visible()
            has_story = await self.page.locator(
                "xpath=//div[@role='button' and .//img[contains(@alt, 'profile picture')]]"
            ).is_visible()

            # Highlights detection
            highlight_locators = [
                "._acaz",
                "xpath=//img[contains(@alt, 'highlight story picture')]",
                "xpath=//div[contains(@aria-label, 'Story Highlights')]"
            ]
            has_highlights = False
            for locator in highlight_locators:
                if await self.page.locator(locator).count() > 0:
                    has_highlights = True
                    break

            # Extract post and following counts using known class structure
            def parse_number(text):
                text = text.replace(",", "").lower()
                if 'k' in text:
                    return int(float(text.replace('k', '')) * 1_000)
                elif 'm' in text:
                    return int(float(text.replace('m', '')) * 1_000_000)
                return int(text) if text.isdigit() else 0

            post_count, following_count = 0, 0

            post_span = await self.page.locator(
                "xpath=//span[contains(., 'posts')]/span/span"
            ).first.inner_text()
            post_count = parse_number(post_span)

            following_span = await self.page.locator(
                "xpath=//span[contains(., 'following')]/span/span"
            ).first.inner_text()
            following_count = parse_number(following_span)

            # Followers: still fetched from title for accuracy
            follower_count = 0
            followers_button = self.page.locator("xpath=//li//button[.//span[contains(text(), 'followers')]]")
            if await followers_button.count() > 0:
                try:
                    number_text = await followers_button.locator("span[title]").first.inner_text()
                    if number_text:
                        follower_count = parse_number(number_text)
                    else:
                        # fallback: get visible text (e.g., "11.1K")
                        follower_count_text = await followers_button.locator("span").nth(1).inner_text()
                        follower_count = parse_number(follower_count_text)
                except Exception:
                    pass 

            is_verified = await self.page.locator("span[aria-label='Verified']").is_visible()

            return {
                "is_public": not is_private,
                "can_dm": can_dm,
                "has_story": has_story,
                "has_highlights": has_highlights,
                "posts_available": post_count > 0,
                "post_count": post_count,
                "follower_count": follower_count,
                "following_count": following_count,
                "is_verified": is_verified
            }

        except Exception as e:
            print(f"⚠️ Error extracting profile data: {e}")
            return {
                "error": str(e),
                "is_public": True,
                "can_dm": False,
                "has_story": False,
                "has_highlights": False,
                "post_count": 0,
                "posts_available": True,
                "follower_count": 0,
                "following_count": 0,
                "is_verified": False
            }


    
    async def scroll_profile(self) -> None:
        """
        Scrolls through an Instagram profile in a human-like way.
        """
        # Get random scroll parameters
        scroll_distance, scroll_duration = self.randomizer.get_scroll_parameters()
        
        # Execute scroll with smooth motion
        await self.page.evaluate(
            f"window.scrollBy({{top: {scroll_distance}, left: 0, behavior: 'smooth'}});"
        )
        
        # Wait for content to load with slight randomization
        await asyncio.sleep(scroll_duration * random.uniform(0.8, 1.2))
    
    async def view_random_post(self) -> None:
        """
        Opens and views a random post from the current page.
        """
        try:
            # Find all posts on the page
            posts = await self.page.query_selector_all('article a')
            
            if not posts or len(posts) == 0:
                return
            
            # Select a random post
            random_post = random.choice(posts)
            
            # Click on the post
            await random_post.click()
            await self.randomizer.human_delay(2, 4)
            
            # View the post for a random amount of time (5-15 seconds)
            view_time = random.uniform(5, 15)
            await asyncio.sleep(view_time)
            
            # 30% chance to view comments
            if random.random() < 0.3:
                # Scroll down to see comments
                await self.page.evaluate(
                    "window.scrollBy({top: 300, left: 0, behavior: 'smooth'});"
                )
                await asyncio.sleep(random.uniform(3, 7))
            
            # Close the post
            try:
                # Try to find a close button
                close_button = await self.page.query_selector('svg[aria-label="Close"]')
                if close_button:
                    await close_button.click()
                else:
                    # Press escape key
                    await self.page.keyboard.press('Escape')
            except:
                # Fall back to escape key
                await self.page.keyboard.press('Escape')
            
            await self.randomizer.human_delay(1, 2)
            
        except Exception as e:
            print(f"Error viewing random post: {e}")
            # Try to close any open modals by pressing escape
            await self.page.keyboard.press('Escape')
    
    async def navigate_to_explore(self) -> bool:
        """
        Navigates to the Instagram Explore page.
        
        Returns:
            Boolean indicating success
        """
        try:
            # Click on Explore icon
            await self.page.click('a[href="/explore/"]')
            await self.randomizer.human_delay(2, 4)
            
            # Verify we're on the explore page
            current_url = self.page.url
            return "explore" in current_url
            
        except Exception as e:
            print(f"Error navigating to explore: {e}")
            return False
    
    async def return_to_home_feed(self) -> bool:
        """
        Navigates back to the Instagram home feed.
        
        Returns:
            Boolean indicating success
        """
        try:
            # Click on home icon
            await self.page.click('a[href="/"]')
            await self.randomizer.human_delay(1, 2)
            
            # Verify we're on the home feed
            current_url = self.page.url
            return current_url == "https://www.instagram.com/" or current_url == "https://www.instagram.com"
            
        except Exception as e:
            print(f"Error returning to home feed: {e}")
            return False