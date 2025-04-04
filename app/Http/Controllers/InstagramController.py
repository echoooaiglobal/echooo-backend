from fastapi import APIRouter, Depends
from sqlalchemy import desc
from sqlalchemy.orm import Session
from app.Services.Instagram.LoginService import LoginService
from app.Services.Instagram.ProfileAnalysisService import ProfileAnalysisService
from app.Services.Instagram.DMService import DMService
from app.Services.Instagram.StoryMessagingService import StoryMessagingService
from config.settings import INSTAGRAM_URL
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

@router.post("/send-messages")
async def send_messages(db: Session = Depends(get_db)):
    # influencers = db.query(Influencer).filter(Influencer.message_status == False).all()
    influencers = db.query(Influencer)\
        .filter(Influencer.client_id == 1)\
        .filter(Influencer.message_status == False)\
        .filter(Influencer.error_code == 'STORY_NOT_FOUND')\
        .order_by(desc(Influencer.id))\
        .all()
    
    if not influencers:
        return {"message": "No influencers found to send messages."}
    
    async with LoginService() as login_service:
        page = await login_service.login()

        MESSAGE = """Hello,\n\nI’m Sarah from Echooo.AI, an Influencer Management Platform working with brands like Nestlé, Packages Group, Sutas Dairy, HerBeauty, Moyuum, and Fasset across Pakistan and the MENA region.\n\nNestlé is looking for influencers to help create awareness about child malnutrition in Pakistan through a paid collaboration. The scope includes:\n\n\u2022  1 Instagram Reel or YouTube Video (platform based on preference)\n\u2022  3–4 Instagram Stories or 1–2 YouTube Shorts\n\u2022  Cross-posting on all your social media handles\n\nPayment: Processed within 30–45 days after content goes live (15% platform fee applies).\n\nIf interested, please share your charges, availability, and social media URLs.\n\nLooking forward to your response!\n\nBest,\nSarah\nEchooo.AI"""

        results = []
        # print(f"influencers:", influencers)
        for influencer in influencers:
            username = influencer.username
            print(f"🔹 Visiting profile: {username}")
            await page.goto(f"{INSTAGRAM_URL}/{username}/")
            await asyncio.sleep(5)

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

                if profile["has_story"]:
                    status, error_code, error_reason = await story_service.reply_to_story(MESSAGE)
                    sent_via = "Story" if status else None
                    sent_at = datetime.datetime.now().isoformat() if status else None
                else:
                    status, error_code, error_reason = False, "STORY_NOT_FOUND", "No active story"
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
            delay = random.uniform(90, 200)
            print(f"Sleeping for {delay:.2f} seconds...")
            await asyncio.sleep(delay)
  
        return {"results": results}