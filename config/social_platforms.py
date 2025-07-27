# config/social_platforms.py
INSTAGRAM_CONFIG = {
    "api_version": "v19.0",
    "base_url": "https://graph.instagram.com",
    "required_scopes": [
        "instagram_basic",
        "instagram_content_publish",
        "instagram_manage_messages",
        "instagram_manage_insights"
    ],
    "webhook_fields": [
        "messages",
        "messaging_seen",
        "messaging_postbacks"
    ]
}

FACEBOOK_CONFIG = {
    "api_version": "v19.0",
    "base_url": "https://graph.facebook.com",
    "required_scopes": [
        "pages_manage_posts",
        "pages_manage_engagement", 
        "pages_messaging",
        "pages_read_engagement"
    ],
    "webhook_fields": [
        "messages",
        "messaging_postbacks",
        "feed"
    ]
}

WHATSAPP_CONFIG = {
    "api_version": "v19.0",
    "base_url": "https://graph.facebook.com",
    "required_scopes": [
        "whatsapp_business_messaging",
        "whatsapp_business_management"
    ],
    "webhook_fields": [
        "messages",
        "message_deliveries",
        "message_reads"
    ]
}

TIKTOK_CONFIG = {
    "api_version": "v1",
    "base_url": "https://open-api.tiktok.com",
    "required_scopes": [
        "video.upload",
        "video.list",
        "user.info.basic"
    ]
}