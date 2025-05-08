from playwright.async_api import Page
import asyncio
import random
from typing import Dict, Any, List, Optional, Tuple
from app.Services.Utils.RandomizationUtil import RandomizationUtil

class EngagementService:
    """
    Service for handling engagement with Instagram content including:
    liking posts, following users, and preparing for commenting.
    """
    
    def __init__(self, page: Page):
        """
        Initialize the engagement service.
        
        Args:
            page: Playwright page instance
        """
        self.page = page
        self.randomizer = RandomizationUtil()
        self.daily_follow_limit = 30  # Safe limit to avoid triggering Instagram limits
        self.daily_like_limit = 100
        self.daily_follows = 0
        self.daily_likes = 0
    
    def reset_daily_counts(self):
        """Reset daily action counters."""
        self.daily_follows = 0
        self.daily_likes = 0
    
    async def like_post(self, post_selector: Optional[str] = None) -> bool:
        """
        Likes the current post or a specific post.
        
        Args:
            post_selector: Optional selector for a specific post
            
        Returns:
            Boolean indicating success
        """
        if self.daily_likes >= self.daily_like_limit:
            print("Daily like limit reached")
            return False
            
        try:
            # If we're not already viewing a post, click on it
            if post_selector:
                await self.page.click(post_selector)
                await self.randomizer.human_delay(1.5, 3)
            
            # Check if the post is already liked
            already_liked = await self.page.evaluate("""() => {
                const likeButtons = document.querySelectorAll('svg[aria-label="Like"], svg[aria-label="Unlike"]');
                for (const button of likeButtons) {
                    if (button.getAttribute('aria-label') === 'Unlike') {
                        return true;
                    }
                }
                return false;
            }""")
            
            if already_liked:
                print("Post already liked")
                # If post_selector was provided, close the post
                if post_selector:
                    await self.page.keyboard.press('Escape')
                    await asyncio.sleep(1)
                return True
            
            # Find and click the like button
            await self.page.click('svg[aria-label="Like"]')
            
            # Wait a bit for the like to register
            await self.randomizer.human_delay(1, 2)
            
            # Verify the post was liked
            like_successful = await self.page.evaluate("""() => {
                const unlikeButton = document.querySelector('svg[aria-label="Unlike"]');
                return !!unlikeButton;
            }""")
            
            # If post_selector was provided, close the post
            if post_selector:
                await self.page.keyboard.press('Escape')
                await asyncio.sleep(1)
            
            if like_successful:
                self.daily_likes += 1
                
            return like_successful
            
        except Exception as e:
            print(f"Error liking post: {e}")
            # Try to close any open modals
            try:
                await self.page.keyboard.press('Escape')
            except:
                pass
            return False
    
    async def follow_user(self, username: Optional[str] = None) -> bool:
        """
        Follows the current user profile or a specific user.
        
        Args:
            username: Optional specific username to follow
            
        Returns:
            Boolean indicating success
        """
        if self.daily_follows >= self.daily_follow_limit:
            print("Daily follow limit reached")
            return False
            
        try:
            # If username provided, navigate to their profile
            if username:
                await self.page.goto(f"https://www.instagram.com/{username}/")
                await self.randomizer.human_delay(2, 3)
            
            # Check if we're already following
            already_following = await self.page.evaluate("""() => {
                const followButtons = document.querySelectorAll('button');
                for (const button of followButtons) {
                    if (button.textContent === 'Following' || button.textContent === 'Requested') {
                        return true;
                    }
                }
                return false;
            }""")
            
            if already_following:
                print(f"Already following {'this user' if not username else username}")
                return True
            
            # Find and click the follow button
            button_found = False
            follow_buttons = await self.page.query_selector_all('button')
            
            for button in follow_buttons:
                button_text = await button.text_content()
                if button_text.strip() == 'Follow':
                    await button.click()
                    button_found = True
                    break
            
            if not button_found:
                print("Follow button not found")
                return False
                
            # Wait for follow to register
            await self.randomizer.human_delay(1, 2)
            
            # Verify follow was successful
            follow_successful = await self.page.evaluate("""() => {
                const followButtons = document.querySelectorAll('button');
                for (const button of followButtons) {
                    if (button.textContent === 'Following' || button.textContent === 'Requested') {
                        return true;
                    }
                }
                return false;
            }""")
            
            if follow_successful:
                self.daily_follows += 1
                print(f"Successfully followed {'this user' if not username else username}")
            
            return follow_successful
            
        except Exception as e:
            print(f"Error following user: {e}")
            return False
    
    async def unfollow_user(self, username: Optional[str] = None) -> bool:
        """
        Unfollows a user (rarely used but included for completeness).
        
        Args:
            username: Optional specific username to unfollow
            
        Returns:
            Boolean indicating success
        """
        try:
            # If username provided, navigate to their profile
            if username:
                await self.page.goto(f"https://www.instagram.com/{username}/")
                await self.randomizer.human_delay(2, 3)
            
            # Click on Following button
            following_found = False
            buttons = await self.page.query_selector_all('button')
            
            for button in buttons:
                button_text = await button.text_content()
                if button_text.strip() == 'Following':
                    await button.click()
                    following_found = True
                    break
            
            if not following_found:
                print(f"Not following {'this user' if not username else username}")
                return False
                
            # Wait for unfollow confirmation dialog
            await self.randomizer.human_delay(1, 2)
            
            # Click Unfollow in confirmation dialog
            unfollow_button = await self.page.query_selector('button:has-text("Unfollow")')
            if unfollow_button:
                await unfollow_button.click()
                await self.randomizer.human_delay(1.5, 2.5)
                return True
            else:
                print("Unfollow confirmation button not found")
                return False
            
        except Exception as e:
            print(f"Error unfollowing user: {e}")
            return False
    
    async def engage_with_user_content(self, 
                                    username: str, 
                                    like_probability: float = 0.3,
                                    follow_probability: float = 0.1,
                                    max_posts_to_like: int = 3) -> Dict[str, Any]:
        """
        Engages with a user's content in a human-like way.
        
        Args:
            username: Username to engage with
            like_probability: Probability of liking each post viewed
            follow_probability: Probability of following the user
            max_posts_to_like: Maximum number of posts to like
            
        Returns:
            Dictionary with engagement results
        """
        engagement_results = {
            "username": username,
            "posts_liked": 0,
            "followed": False,
            "error": None
        }
        
        try:
            # Check if we're already on this profile
            current_url = self.page.url
            current_username = current_url.strip('/').split('/')[-1].split('?')[0]
            
            # Only navigate if we're not already on this profile
            if current_username.lower() != username.lower():
                # Navigate to user profile
                await self.page.goto(f"https://www.instagram.com/{username}/")
                await self.randomizer.human_delay(2, 4)
            else:
                print(f"Already on {username}'s profile, continuing engagement")
            
            # Check if profile is private
            is_private = await self.page.evaluate("""() => {
                return !!document.querySelector('h2:contains("This Account is Private")');
            }""")
            
            if is_private:
                engagement_results["error"] = "Private account"
                return engagement_results
            
            # Decide whether to follow based on probability
            if self.randomizer.should_perform_action(follow_probability):
                engagement_results["followed"] = await self.follow_user()
            
            # Find posts
            posts = await self.page.query_selector_all('article a')
            
            if not posts or len(posts) == 0:
                engagement_results["error"] = "No posts found"
                return engagement_results
                
            # Determine how many posts to like (weighted toward fewer)
            posts_to_engage = min(len(posts), self.randomizer.get_engagement_count(1, max_posts_to_like))
            
            # Shuffle posts to randomize selection
            random_posts = random.sample(posts, min(len(posts), posts_to_engage))
            
            for post in random_posts:
                # Click on the post
                await post.click()
                await self.randomizer.human_delay(1.5, 3.5)
                
                # View the post for a random amount of time
                view_time = random.uniform(3, 10)
                await asyncio.sleep(view_time)
                
                # Like based on probability
                if self.randomizer.should_perform_action(like_probability):
                    like_success = await self.like_post()
                    if like_success:
                        engagement_results["posts_liked"] += 1
                
                # Close the post
                await self.page.keyboard.press('Escape')
                await self.randomizer.human_delay(1, 2)
            
            return engagement_results
            
        except Exception as e:
            print(f"Error engaging with {username}: {e}")
            engagement_results["error"] = str(e)
            return engagement_results
    
    async def prepare_for_comment(self, post_selector: Optional[str] = None) -> bool:
        """
        Opens comment field for a post (actual commenting will be implemented with AI).
        
        Args:
            post_selector: Optional selector for a specific post
            
        Returns:
            Boolean indicating if comment field was successfully opened
        """
        try:
            # If not already viewing a post, click on it
            if post_selector:
                await self.page.click(post_selector)
                await self.randomizer.human_delay(1.5, 3)
            
            # Click the comment button
            await self.page.click('svg[aria-label="Comment"]')
            await self.randomizer.human_delay(1, 2)
            
            # Check if comment field is focused
            is_comment_field_focused = await self.page.evaluate("""() => {
                const commentField = document.querySelector('textarea[aria-label="Add a comment…"]');
                return document.activeElement === commentField;
            }""")
            
            return is_comment_field_focused
            
        except Exception as e:
            print(f"Error preparing for comment: {e}")
            return False
    
    async def check_engagement_limits(self) -> Dict[str, Any]:
        """
        Checks current engagement limits and stats.
        
        Returns:
            Dictionary with engagement stats
        """
        return {
            "follows_today": self.daily_follows,
            "likes_today": self.daily_likes,
            "follow_limit": self.daily_follow_limit,
            "like_limit": self.daily_like_limit,
            "follow_limit_reached": self.daily_follows >= self.daily_follow_limit,
            "like_limit_reached": self.daily_likes >= self.daily_like_limit
        }
    
    def set_engagement_limits(self, follow_limit: int = None, like_limit: int = None) -> None:
        """
        Sets custom engagement limits.
        
        Args:
            follow_limit: Custom follow limit
            like_limit: Custom like limit
        """
        if follow_limit is not None:
            self.daily_follow_limit = max(1, follow_limit)
        
        if like_limit is not None:
            self.daily_like_limit = max(1, like_limit)
                                                         