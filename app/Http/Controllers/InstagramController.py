from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.Services.Instagram.LoginService import LoginService
from app.Services.Instagram.ProfileAnalysisService import ProfileAnalysisService
from app.Services.Instagram.DMService import DMService
from app.Services.Instagram.StoryMessagingService import StoryMessagingService
from config.settings import INSTAGRAM_URL
from config.database import SessionLocal
from app.Models.Influencer import Influencer

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/send-messages")
def send_messages(db: Session = Depends(get_db)):
    # Retrieve all influencers from the database
    influencers = db.query(Influencer).all()
    usernames = [influencer.username for influencer in influencers]
    print(f"Usernamesss: {usernames}")
    if not usernames:
        return {"message": "No influencers found to send messages."}

    login_service = LoginService()
    page = login_service.login()  # Login once, session persists

    results = []
    for username in usernames:
        print(f"🔹 Visiting profile: {username}")
        page.goto(f"{INSTAGRAM_URL}/{username}/")
        page.wait_for_timeout(5000)  # Ensure page loads

        profile_service = ProfileAnalysisService(page)
        dm_service = DMService(page)
        story_service = StoryMessagingService(page)

        profile = profile_service.check_profile(username)

        if profile["is_public"] and profile["can_dm"]:
            status = dm_service.send_message("Hello how are you?")  # Pass username
        elif profile["has_story"]:
            status = story_service.reply_to_story("Hey, saw your story!")  # Pass username
        else:
            status = "No message sent"

        results.append({"username": username, "status": status})

    login_service.close()  # Close browser after all users

    return {"results": results}
