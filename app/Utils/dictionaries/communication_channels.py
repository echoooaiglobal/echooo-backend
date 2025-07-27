# app/Utils/dictionaries/communication_channels.py

"""
Default communication channels for the influencer marketing platform
"""

DEFAULT_COMMUNICATION_CHANNELS = [
   # INSTAGRAM CHANNELS
   {
       "name": "Instagram Direct Message",
       "code": "ig_dm",
       "platform_id": "instagram",
       "is_active": True,
       "order": 1,
       "description": "Direct message on Instagram"
   },
   {
       "name": "Instagram Story Reply",
       "code": "ig_story",
       "platform_id": "instagram",
       "is_active": True,
       "order": 2,
       "description": "Reply to Instagram story"
   },
   {
       "name": "Instagram Post Comment",
       "code": "ig_comment",
       "platform_id": "instagram",
       "is_active": True,
       "order": 3,
       "description": "Comment on Instagram post"
   },
   {
       "name": "Instagram Live Comment",
       "code": "ig_live",
       "platform_id": "instagram",
       "is_active": True,
       "order": 4,
       "description": "Comment during Instagram live stream"
   },

   # WHATSAPP CHANNELS
   {
       "name": "WhatsApp Direct Message",
       "code": "whatsapp_dm",
       "platform_id": "whatsapp",
       "is_active": True,
       "order": 5,
       "description": "Direct message on WhatsApp"
   },
   {
       "name": "WhatsApp Business Message",
       "code": "whatsapp_business",
       "platform_id": "whatsapp",
       "is_active": True,
       "order": 6,
       "description": "WhatsApp Business API message"
   },
   {
       "name": "WhatsApp Group Message",
       "code": "whatsapp_group",
       "platform_id": "whatsapp",
       "is_active": True,
       "order": 7,
       "description": "Message in WhatsApp group"
   },

   # TIKTOK CHANNELS
   {
       "name": "TikTok Direct Message",
       "code": "tiktok_dm",
       "platform_id": "tiktok",
       "is_active": True,
       "order": 8,
       "description": "Direct message on TikTok"
   },
   {
       "name": "TikTok Comment",
       "code": "tiktok_comment",
       "platform_id": "tiktok",
       "is_active": True,
       "order": 9,
       "description": "Comment on TikTok video"
   },
   {
       "name": "TikTok Live Comment",
       "code": "tiktok_live",
       "platform_id": "tiktok",
       "is_active": True,
       "order": 10,
       "description": "Comment during TikTok live stream"
   },

   # LINKEDIN CHANNELS
   {
       "name": "LinkedIn Direct Message",
       "code": "linkedin_dm",
       "platform_id": "linkedin",
       "is_active": True,
       "order": 11,
       "description": "Direct message on LinkedIn"
   },
   {
       "name": "LinkedIn Connection Request",
       "code": "linkedin_connect",
       "platform_id": "linkedin",
       "is_active": True,
       "order": 12,
       "description": "LinkedIn connection request with message"
   },
   {
       "name": "LinkedIn Post Comment",
       "code": "linkedin_comment",
       "platform_id": "linkedin",
       "is_active": True,
       "order": 13,
       "description": "Comment on LinkedIn post"
   },

   # EMAIL CHANNELS
   {
       "name": "Email",
       "code": "email",
       "platform_id": "email",
       "is_active": True,
       "order": 14,
       "description": "Email message"
   },
   {
       "name": "Business Email",
       "code": "business_email",
       "platform_id": "email",
       "is_active": True,
       "order": 15,
       "description": "Formal business email"
   },

   # YOUTUBE CHANNELS
   {
       "name": "YouTube Comment",
       "code": "youtube_comment",
       "platform_id": "youtube",
       "is_active": True,
       "order": 16,
       "description": "Comment on YouTube video"
   },
   {
       "name": "YouTube Live Chat",
       "code": "youtube_live",
       "platform_id": "youtube",
       "is_active": True,
       "order": 17,
       "description": "Message in YouTube live chat"
   },

   # TWITTER/X CHANNELS
   {
       "name": "Twitter Direct Message",
       "code": "twitter_dm",
       "platform_id": "X",
       "is_active": True,
       "order": 18,
       "description": "Direct message on Twitter/X"
   },
   {
       "name": "Twitter Reply",
       "code": "twitter_reply",
       "platform_id": "X",
       "is_active": True,
       "order": 19,
       "description": "Reply to Twitter/X post"
   },
   {
       "name": "Twitter Mention",
       "code": "twitter_mention",
       "platform_id": "X",
       "is_active": True,
       "order": 20,
       "description": "Mention on Twitter/X"
   },

   # FACEBOOK CHANNELS
   {
       "name": "Facebook Messenger",
       "code": "fb_messenger",
       "platform_id": "facebook",
       "is_active": True,
       "order": 21,
       "description": "Facebook Messenger message"
   },
   {
       "name": "Facebook Post Comment",
       "code": "fb_comment",
       "platform_id": "facebook",
       "is_active": True,
       "order": 22,
       "description": "Comment on Facebook post"
   },
   {
       "name": "Facebook Page Message",
       "code": "fb_page_message",
       "platform_id": "facebook",
       "is_active": True,
       "order": 23,
       "description": "Message to Facebook page"
   },

   # TELEGRAM CHANNELS
   {
       "name": "Telegram Direct Message",
       "code": "telegram_dm",
       "platform_id": "telegram",
       "is_active": True,
       "order": 24,
       "description": "Direct message on Telegram"
   },
   {
       "name": "Telegram Group Message",
       "code": "telegram_group",
       "platform_id": "telegram",
       "is_active": True,
       "order": 25,
       "description": "Message in Telegram group"
   },

   # SMS CHANNELS
   {
       "name": "SMS",
       "code": "sms",
       "platform_id": "sms",
       "is_active": True,
       "order": 26,
       "description": "SMS text message"
   },
   {
       "name": "Business SMS",
       "code": "business_sms",
       "platform_id": "sms",
       "is_active": True,
       "order": 27,
       "description": "Business SMS message"
   }
]