from fastapi import APIRouter, Depends
from sqlalchemy import desc
from sqlalchemy.orm import Session
from app.Services.Instagram.LoginService import LoginService
from app.Services.Instagram.DMService import DMService
from app.Services.Instagram.ProfileAnalysisService import ProfileAnalysisService
from app.Services.Instagram.StoryMessagingService import StoryMessagingService
from app.Services.Instagram.HighlightMessagingService import HighlightMessagingService
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
        .filter(Influencer.client_id == 3)\
        .filter(Influencer.message_status == False)\
        .filter(Influencer.error_code == None)\
        .order_by(desc(Influencer.id))\
        .all()

    # influencers = db.query(Influencer)\
    #     .filter(Influencer.client_id == 2)\
    #     .filter(Influencer.message_status == False)\
    #     .filter(Influencer.error_code.isnot(None))\
    #     .filter(Influencer.error_reason != "Highlight Restriction")\
    #     .filter(Influencer.error_code != "PRIVATE_PROFILE")\
    #     .order_by(desc(Influencer.id))\
    #     .all()
    
    if not influencers:
        return {"message": "No influencers found to send messages."}
    
    async with LoginService() as login_service:
        page = await login_service.login()

        # MESSAGE = """Hello,\n\nI’m Sarah from Echooo.AI, an Influencer Management Platform working with brands like Nestlé, Packages Group, Sutas Dairy, HerBeauty, Moyuum, and Fasset across Pakistan and the MENA region.\n\nNestlé is looking for influencers to help create awareness about child malnutrition in Pakistan through a paid collaboration. The scope includes:\n\n\u2022  1 Instagram Reel or YouTube Video (platform based on preference)\n\u2022  3–4 Instagram Stories or 1–2 YouTube Shorts\n\u2022  Cross-posting on all your social media handles\n\nPayment: Processed within 30–45 days after content goes live (15% platform fee applies).\n\nIf interested, please share your charges, availability, and social media URLs.\n\nLooking forward to your response!\n\nBest,\nSarah\nEchooo.AI"""
        # MESSAGE = """Hello,\n\nWe are reaching out to offer you an exciting campaign with HERBeauty.\n\nScope of Work:\n\u2022 1 Collaborative Reel, 2-3 Story\n\nKey Details:\n\u2022 Timeline: Content delivery within 5 days of receiving the products.\n\u2022 Content Focus: The content should be creative and in accordance with your audience and must be posted on Instagram.\n\u2022 Payment Terms: Please note that the amount you quote must includes a 15% platform fee, which will be deducted before the final payout. The payment is made within 30-45 days of the content going live\n\nNext Steps:\n\nTo confirm your spot in the campaign, please let us know if you agree with the above terms.\nWe're excited to collaborate with you on this campaign and look forward to partnering on many more exciting opportunities in the future!\n\nBest regards,\n\nTeam Echooo.AI"""
        MESSAGE = """Hi, I hope you're doing well!\n\nWe're excited to offer you a paid collaboration with IGI Insurance.\n\nScope of Work:\n\u2022 1 Collaborative Reel\n\u2022 2-3 Stories\n\nCampaign Overview:\nIGI Insurance isn't your typical insurance company—it makes staying fit rewarding! Users complete weekly fitness challenges, earn points, and redeem them at gyms, restaurants, and even for airline tickets. The reel should be fun and quirky to highlight this unique approach.\n\nPayment Terms:\n\u2022 Payment will be processed within 30-45 days after content submission\n\u2022 Please ensure your quoted amount includes a 15% platform fee\n\u2022 Please share your email and number for further coordination\n\nNext Steps:\nLet me know if you're interested or have any questions. Looking forward to collaborating!"""
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
            delay = random.uniform(90, 200)
            print(f"Sleeping for {delay:.2f} seconds...")
            await asyncio.sleep(delay)
  
        return {"results": results}