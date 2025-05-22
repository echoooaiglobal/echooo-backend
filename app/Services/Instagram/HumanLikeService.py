from fastapi import APIRouter, Depends
from sqlalchemy import desc
from sqlalchemy.orm import Session
from app.Services.Instagram.LoginService import LoginService
from app.Services.Instagram.DMService import DMService
from app.Services.Instagram.ProfileAnalysisService import ProfileAnalysisService
from app.Services.Instagram.StoryMessagingService import StoryMessagingService
from app.Services.Instagram.HighlightMessagingService import HighlightMessagingService
from config.settings import settings
from config.database import SessionLocal
from app.Models.Influencer import Influencer
import random
import asyncio
import datetime

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class HumanLikeService:
    def __init__(self, page):
        self.page = page
        
    async def natural_scrolling(self, min_scrolls=2, max_scrolls=8):
        """Scroll a page like a human would"""
        scrolls = random.randint(min_scrolls, max_scrolls)
        for _ in range(scrolls):
            # Scroll down with variable speed
            await self.page.evaluate(f"window.scrollBy(0, {random.randint(300, 800)})")
            # Random pause while scrolling
            await asyncio.sleep(random.uniform(0.5, 3))
            
    async def random_explore(self):
        """Visit explore page and interact with random content"""
        await self.page.goto(f"{settings.INSTAGRAM_URL}/explore/")
        await asyncio.sleep(random.uniform(3, 7))
        await self.natural_scrolling()
        
        # Maybe click a random post (30% chance)
        if random.random() < 0.3:
            posts = await self.page.query_selector_all("article a")
            if posts:
                random_post = random.choice(posts)
                await random_post.click()
                await asyncio.sleep(random.uniform(5, 15))
                await self.page.go_back()
                
    async def browse_feed(self):
        """Browse home feed naturally"""
        await self.page.goto(settings.INSTAGRAM_URL)
        await asyncio.sleep(random.uniform(3, 8))
        await self.natural_scrolling(3, 12)
        
        # Maybe like a post (20% chance)
        if random.random() < 0.2:
            like_buttons = await self.page.query_selector_all('[aria-label="Like"]')
            if like_buttons:
                await random.choice(like_buttons).click()
                await asyncio.sleep(random.uniform(1, 3))
                
    async def view_profile_naturally(self, username):
        """View a profile in a human-like manner"""
        await self.page.goto(f"{settings.INSTAGRAM_URL}/{username}/")
        await asyncio.sleep(random.uniform(3, 7))
        
        # Look at profile info
        await asyncio.sleep(random.uniform(2, 5))
        
        # Maybe view a post
        posts = await self.page.query_selector_all("article a")
        if posts and random.random() < 0.7:  # 70% chance
            random_post = random.choice(posts)
            await random_post.click()
            await asyncio.sleep(random.uniform(4, 12))
            await self.page.go_back()
            await asyncio.sleep(random.uniform(1, 3))
            
        # Scroll through their posts
        await self.natural_scrolling(2, 6)
        
        # Maybe check their reels tab (40% chance)
        if random.random() < 0.4:
            reels_tab = await self.page.query_selector("a[href*='reels']")
            if reels_tab:
                await reels_tab.click()
                await asyncio.sleep(random.uniform(2, 6))
                await self.natural_scrolling(1, 4)
                
        # Maybe follow (5% chance, very low to avoid spammy behavior)
        if random.random() < 0.05:
            follow_button = await self.page.query_selector("button:has-text('Follow')")
            if follow_button:
                await follow_button.click()
                await asyncio.sleep(random.uniform(1, 3))

@router.post("/send-messages")
async def send_messages(db: Session = Depends(get_db)):
    influencers = db.query(Influencer)\
        .filter(Influencer.client_id == 3)\
        .filter(Influencer.message_status == False)\
        .filter(Influencer.error_code == None)\
        .order_by(desc(Influencer.id))\
        .all()
        
    if not influencers:
        return {"message": "No influencers found to send messages."}
    
    async with LoginService() as login_service:
        page = await login_service.login()
        human_service = HumanLikeService(page)
        
        # Start with browsing feed to mimic normal login behavior
        await human_service.browse_feed()
        
        # Maybe explore before starting actual work (40% chance)
        if random.random() < 0.4:
            await human_service.random_explore()
        
        MESSAGE = """Hi, I hope you're doing well!\n\nWe're excited to offer you a paid collaboration"""
        results = []
        
        for idx, influencer in enumerate(influencers):
            username = influencer.username
            print(f"🔹 Visiting profile: {username}")
            
            # View profile naturally instead of direct navigation
            await human_service.view_profile_naturally(username)
            await asyncio.sleep(random.uniform(2, 5))
            
            # Check if the page contains "Profile isn't available"
            profile_unavailable = await page.evaluate("document.body.innerText.includes('Profile isn\\'t available')")

            if profile_unavailable:
                status, error_code, error_reason = False, "PROFILE_NOT_FOUND", "Instagram profile does not exist or is restricted"
                sent_via = None
                sent_at = None
            else:
                profile_service = ProfileAnalysisService(page)
                dm_service = DMService(page)
                story_service = StoryMessagingService(page)

                profile = await profile_service.check_profile(username)
                highlight_service = HighlightMessagingService(page)
                
                if profile["is_public"]:
                    if profile["has_story"]:
                        status, error_code, error_reason = await story_service.reply_to_story(MESSAGE)

                        if not status and error_code in ["REPLY_BOX_NOT_FOUND", "403", "TIMEOUT_ERROR", "UNKNOWN_ERROR"]:
                            # Try sending via highlight only if highlights are available
                            if profile["has_highlights"]:
                                status, error_code, error_reason = await highlight_service.reply_to_highlight(MESSAGE)
                                sent_via = "Highlight" if status else None
                            else:
                                sent_via = None
                        else:
                            sent_via = "Story" if status else None

                        sent_at = datetime.datetime.now().isoformat() if status else None

                    elif profile["has_highlights"]:
                        status, error_code, error_reason = await highlight_service.reply_to_highlight(MESSAGE)
                        sent_via = "Highlight" if status else None
                        sent_at = datetime.datetime.now().isoformat() if status else None

                    else:
                        status = False
                        error_code = "MESSAGING_FAILED"
                        error_reason = "No available messaging method (story, highlight)"
                        sent_via = None
                        sent_at = None
                else: 
                    status = False
                    error_code = "PRIVATE_PROFILE"
                    error_reason = "User profile is private."
                    sent_via = None
                    sent_at = None

            influencer.message_status = status
            influencer.sent_via = sent_via
            influencer.error_code = error_code
            influencer.error_reason = error_reason
            influencer.message_sent_at = sent_at
            
            db.add(influencer)
            results.append({"username": username, "status": status, "sent_via": sent_via, "error_code": error_code, "error_reason": error_reason})
            db.commit()
            
            # Insert "distraction" activities between influencer visits (30% chance)
            if random.random() < 0.3 and idx < len(influencers) - 1:
                distraction_action = random.choice(["feed", "explore", "none"])
                if distraction_action == "feed":
                    await human_service.browse_feed()
                elif distraction_action == "explore":
                    await human_service.random_explore()
            
            # More natural variable delays between profile visits
            delay = random.uniform(60, 180)  # Between 1-3 minutes
            print(f"Sleeping for {delay:.2f} seconds...")
            await asyncio.sleep(delay)
  
        # End session with a natural feed browsing
        await human_service.browse_feed()
        
        return {"results": results}