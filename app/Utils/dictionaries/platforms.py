# app/dictionaries/platforms.py
"""
Platform definitions for the influencer marketing platform.
These platforms represent social media and content platforms where influencers operate.
"""

DEFAULT_PLATFORMS = [
    {
        "name": "TikTok",
        "logo_url": "https://cdn.getphyllo.com/platforms_logo/logos/logo_tiktok.png",
        "category": "SOCIAL",
        "status": "ACTIVE",
        "url": "https://www.tiktok.com",
        "provider": "phyllo",
        "work_platform_id": "de55aeec-0dc8-4119-bf90-16b3d1f0c987",
        "products": {
            "identity": {
                "is_supported": True,
                "audience": {
                    "is_supported": True
                }
            },
            "engagement": {
                "is_supported": True,
                "audience": {
                    "is_supported": False
                }
            },
            "income": {
                "is_supported": False
            },
            "switch": {
                "is_supported": False
            },
            "activity": {
                "is_supported": False
            },
            "publish_content": {
                "is_supported": False
            }
        }
    },
    {
        "name": "Instagram",
        "logo_url": "https://cdn.getphyllo.com/platforms_logo/logos/logo_instagram.png",
        "category": "SOCIAL",
        "status": "ACTIVE",
        "url": "https://www.instagram.com/",
        "provider": "phyllo",
        "work_platform_id": "9bb8913b-ddd9-430b-a66a-d74d846e6c66",
        "products": {
            "identity": {
                "is_supported": True,
                "audience": {
                    "is_supported": True
                }
            },
            "engagement": {
                "is_supported": True,
                "audience": {
                    "is_supported": True
                }
            },
            "income": {
                "is_supported": False
            },
            "switch": {
                "is_supported": False
            },
            "activity": {
                "is_supported": False
            },
            "publish_content": {
                "is_supported": False
            }
        }
    },
    {
        "name": "YouTube",
        "logo_url": "https://cdn.getphyllo.com/platforms_logo/logos/logo_youtube.png",
        "category": "ENTERTAINMENT",
        "status": "ACTIVE",
        "url": "https://www.youtube.com/",
        "provider": "phyllo",
        "work_platform_id": "14d9ddf5-51c6-415e-bde6-f8ed36ad7054",
        "products": {
            "identity": {
                "is_supported": True,
                "audience": {
                    "is_supported": True
                }
            },
            "engagement": {
                "is_supported": True,
                "audience": {
                    "is_supported": True
                }
            },
            "income": {
                "is_supported": True
            },
            "switch": {
                "is_supported": False
            },
            "activity": {
                "is_supported": False
            },
            "publish_content": {
                "is_supported": False
            }
        }
    },
    {
        "name": "X",
        "logo_url": "https://cdn.getphyllo.com/platforms_logo/logos/logo_x.png",
        "category": "SOCIAL",
        "status": "ACTIVE",
        "url": "https://twitter.com",
        "provider": "phyllo",
        "work_platform_id": "7645460a-96e0-4192-a3ce-a1fc30641f72",
        "products": {
            "identity": {
                "is_supported": True,
                "audience": {
                    "is_supported": False
                }
            },
            "engagement": {
                "is_supported": True,
                "audience": {
                    "is_supported": False
                }
            },
            "income": {
                "is_supported": False
            },
            "switch": {
                "is_supported": False
            },
            "activity": {
                "is_supported": False
            },
            "publish_content": {
                "is_supported": False
            }
        }
    },
    {
        "name": "Twitch",
        "logo_url": "https://cdn.getphyllo.com/platforms_logo/logos/logo_twitch.png",
        "category": "ENTERTAINMENT",
        "status": "ACTIVE",
        "url": "https://www.twitch.tv",
        "provider": "phyllo",
        "work_platform_id": "e4de6c01-5b78-4fc0-a651-24f44134457b",
        "products": {
            "identity": {
                "is_supported": True,
                "audience": {
                    "is_supported": False
                }
            },
            "engagement": {
                "is_supported": True,
                "audience": {
                    "is_supported": False
                }
            },
            "income": {
                "is_supported": True
            },
            "switch": {
                "is_supported": False
            },
            "activity": {
                "is_supported": False
            },
            "publish_content": {
                "is_supported": False
            }
        }
    },
    {
        "name": "Facebook",
        "logo_url": "https://cdn.getphyllo.com/platforms_logo/logos/logo_facebook.png",
        "category": "SOCIAL",
        "status": "ACTIVE",
        "url": "https://www.facebook.com",
        "provider": "phyllo",
        "work_platform_id": "ad2fec62-2987-40a0-89fb-23485972598c",
        "products": {
            "identity": {
                "is_supported": True,
                "audience": {
                    "is_supported": True
                }
            },
            "engagement": {
                "is_supported": True,
                "audience": {
                    "is_supported": False
                }
            },
            "income": {
                "is_supported": True
            },
            "switch": {
                "is_supported": False
            },
            "activity": {
                "is_supported": False
            },
            "publish_content": {
                "is_supported": False
            }
        }
    },
    {
        "name": "Substack",
        "logo_url": "https://cdn.getphyllo.com/platforms_logo/logos/logo_substack.png",
        "category": "SOCIAL",
        "status": "ACTIVE",
        "url": "https://substack.com/",
        "provider": "phyllo",
        "work_platform_id": "fbf76083-710b-439a-8b8c-956f607ef2c1",
        "products": {
            "identity": {
                "is_supported": True,
                "audience": {
                    "is_supported": False
                }
            },
            "engagement": {
                "is_supported": True,
                "audience": {
                    "is_supported": False
                }
            },
            "income": {
                "is_supported": False
            },
            "switch": {
                "is_supported": False
            },
            "activity": {
                "is_supported": False
            },
            "publish_content": {
                "is_supported": False
            }
        }
    },
    {
        "name": "Shopify",
        "logo_url": "https://cdn.getphyllo.com/platforms_logo/logos/logo_shopify.png",
        "category": "COMMERCE",
        "status": "ACTIVE",
        "url": "https://www.shopify.com/",
        "provider": "phyllo",
        "work_platform_id": "da3d89ee-3900-4b53-99b9-2f3a038e518b",
        "products": {
            "identity": {
                "is_supported": True,
                "audience": {
                    "is_supported": False
                }
            },
            "engagement": {
                "is_supported": False,
                "audience": {
                    "is_supported": False
                }
            },
            "income": {
                "is_supported": True
            },
            "switch": {
                "is_supported": False
            },
            "activity": {
                "is_supported": False
            },
            "publish_content": {
                "is_supported": False
            }
        }
    },
    {
        "name": "Etsy",
        "logo_url": "https://cdn.getphyllo.com/platforms_logo/logos/logo_etsy.png",
        "category": "COMMERCE",
        "status": "ACTIVE",
        "url": "https://www.etsy.com/",
        "provider": "phyllo",
        "work_platform_id": "dae87e8c-e36a-4d06-9229-d362764637be",
        "products": {
            "identity": {
                "is_supported": True,
                "audience": {
                    "is_supported": False
                }
            },
            "engagement": {
                "is_supported": False,
                "audience": {
                    "is_supported": False
                }
            },
            "income": {
                "is_supported": True
            },
            "switch": {
                "is_supported": False
            },
            "activity": {
                "is_supported": False
            },
            "publish_content": {
                "is_supported": False
            }
        }
    },
    {
        "name": "Stripe",
        "logo_url": "https://cdn.getphyllo.com/platforms_logo/logos/logo_stripe.png",
        "category": "COMMERCE",
        "status": "ACTIVE",
        "url": "https://www.stripe.com/",
        "provider": "phyllo",
        "work_platform_id": "d2468c93-e8fb-4ed2-b9e5-fbe3b08229fc",
        "products": {
            "identity": {
                "is_supported": True,
                "audience": {
                    "is_supported": False
                }
            },
            "engagement": {
                "is_supported": False,
                "audience": {
                    "is_supported": False
                }
            },
            "income": {
                "is_supported": True
            },
            "switch": {
                "is_supported": False
            },
            "activity": {
                "is_supported": False
            },
            "publish_content": {
                "is_supported": False
            }
        }
    },
    {
        "name": "Discord",
        "logo_url": "https://cdn.getphyllo.com/platforms_logo/logos/logo_discord.png",
        "category": "ENTERTAINMENT",
        "status": "ACTIVE",
        "url": "https://discord.com/",
        "provider": "phyllo",
        "work_platform_id": "3f996edf-fec1-4be7-bb53-f9b649f41058",
        "products": {
            "identity": {
                "is_supported": True,
                "audience": {
                    "is_supported": False
                }
            },
            "engagement": {
                "is_supported": True,
                "audience": {
                    "is_supported": False
                }
            },
            "income": {
                "is_supported": False
            },
            "switch": {
                "is_supported": False
            },
            "activity": {
                "is_supported": False
            },
            "publish_content": {
                "is_supported": False
            }
        }
    },
    {
        "name": "Reddit",
        "logo_url": "https://cdn.getphyllo.com/platforms_logo/logos/logo_reddit.png",
        "category": "SOCIAL",
        "status": "ACTIVE",
        "url": "https://www.reddit.com",
        "provider": "phyllo",
        "work_platform_id": "dfe5c762-10b2-44fd-b3f2-2c6387690da8",
        "products": {
            "identity": {
                "is_supported": True,
                "audience": {
                    "is_supported": False
                }
            },
            "engagement": {
                "is_supported": True,
                "audience": {
                    "is_supported": False
                }
            },
            "income": {
                "is_supported": False
            },
            "switch": {
                "is_supported": False
            },
            "activity": {
                "is_supported": False
            },
            "publish_content": {
                "is_supported": False
            }
        }
    },
    {
        "name": "Pinterest",
        "logo_url": "https://cdn.getphyllo.com/platforms_logo/logos/logo_pinterest.png",
        "category": "LIFESTYLE",
        "status": "ACTIVE",
        "url": "https://www.pinterest.com",
        "provider": "phyllo",
        "work_platform_id": "9c5b1cf1-23f1-4d40-b0ea-40f9bf615801",
        "products": {
            "identity": {
                "is_supported": True,
                "audience": {
                    "is_supported": False
                }
            },
            "engagement": {
                "is_supported": True,
                "audience": {
                    "is_supported": False
                }
            },
            "income": {
                "is_supported": False
            },
            "switch": {
                "is_supported": False
            },
            "activity": {
                "is_supported": False
            },
            "publish_content": {
                "is_supported": False
            }
        }
    },
    {
        "name": "Snapchat",
        "logo_url": "https://cdn.getphyllo.com/platforms_logo/logos/logo_snapchat.png",
        "category": "SOCIAL",
        "status": "ACTIVE",
        "url": "https://www.snapchat.com",
        "provider": "phyllo",
        "work_platform_id": "ee3c8d7a-3207-4f56-945f-f942b34c96e1",
        "products": {
            "identity": {
                "is_supported": False,
                "audience": {
                    "is_supported": False
                }
            },
            "engagement": {
                "is_supported": False,
                "audience": {
                    "is_supported": False
                }
            },
            "income": {
                "is_supported": False
            },
            "switch": {
                "is_supported": False
            },
            "activity": {
                "is_supported": False
            },
            "publish_content": {
                "is_supported": False
            }
        }
    },
    {
        "name": "Instagram Direct",
        "logo_url": "https://cdn.getphyllo.com/platforms_logo/logos/logo_instagram_direct.png",
        "category": "SOCIAL",
        "status": "ACTIVE",
        "url": "https://www.instagram.com/",
        "provider": "phyllo",
        "work_platform_id": "d3badb09-a81f-4444-bc27-1a994d939e00",
        "products": {
            "identity": {
                "is_supported": True,
                "audience": {
                    "is_supported": False
                }
            },
            "engagement": {
                "is_supported": True,
                "audience": {
                    "is_supported": False
                }
            },
            "income": {
                "is_supported": False
            },
            "switch": {
                "is_supported": False
            },
            "activity": {
                "is_supported": False
            },
            "publish_content": {
                "is_supported": False
            }
        }
    },
    {
        "name": "Patreon",
        "logo_url": "https://cdn.getphyllo.com/platforms_logo/logos/logo_patreon.png",
        "category": "SOCIAL",
        "status": "ACTIVE",
        "url": "https://www.patreon.com/",
        "provider": "phyllo",
        "work_platform_id": "86a3d29e-3af7-4a2f-ab7d-93e472e2fee5",
        "products": {
            "identity": {
                "is_supported": True,
                "audience": {
                    "is_supported": False
                }
            },
            "engagement": {
                "is_supported": True,
                "audience": {
                    "is_supported": False
                }
            },
            "income": {
                "is_supported": False
            },
            "switch": {
                "is_supported": False
            },
            "activity": {
                "is_supported": False
            },
            "publish_content": {
                "is_supported": False
            }
        }
    },
    {
        "name": "AdSense",
        "logo_url": "https://cdn.getphyllo.com/platforms_logo/logos/logo_adsense.png",
        "category": "SOCIAL",
        "status": "ACTIVE",
        "url": "https://www.google.com/adsense/",
        "provider": "phyllo",
        "work_platform_id": "3e6f4cdd-2119-4125-aa0d-86eee4e20fcc",
        "products": {
            "identity": {
                "is_supported": True,
                "audience": {
                    "is_supported": False
                }
            },
            "engagement": {
                "is_supported": False,
                "audience": {
                    "is_supported": False
                }
            },
            "income": {
                "is_supported": True
            },
            "switch": {
                "is_supported": False
            },
            "activity": {
                "is_supported": False
            },
            "publish_content": {
                "is_supported": False
            }
        }
    },
    {
        "name": "FBCommerce",
        "logo_url": "https://cdn.getphyllo.com/platforms_logo/logos/logo_facebook.png",
        "category": "COMMERCE",
        "status": "ACTIVE",
        "url": "https://www.facebook.com",
        "provider": "phyllo",
        "work_platform_id": "8d75fc2d-b256-49b5-9901-ac2d6e09bcc2",
        "products": {
            "identity": {
                "is_supported": True,
                "audience": {
                    "is_supported": False
                }
            },
            "engagement": {
                "is_supported": True,
                "audience": {
                    "is_supported": False
                }
            },
            "income": {
                "is_supported": False
            },
            "switch": {
                "is_supported": False
            },
            "activity": {
                "is_supported": False
            },
            "publish_content": {
                "is_supported": False
            }
        }
    },
    {
        "name": "Medium",
        "logo_url": "https://cdn.getphyllo.com/platforms_logo/logos/logo_medium.png",
        "category": "SOCIAL",
        "status": "ACTIVE",
        "url": "https://www.medium.com/",
        "provider": "phyllo",
        "work_platform_id": "0227e92f-ccd8-4f0b-83ea-fb11e700d1b6",
        "products": {
            "identity": {
                "is_supported": True,
                "audience": {
                    "is_supported": False
                }
            },
            "engagement": {
                "is_supported": True,
                "audience": {
                    "is_supported": False
                }
            },
            "income": {
                "is_supported": False
            },
            "switch": {
                "is_supported": False
            },
            "activity": {
                "is_supported": False
            },
            "publish_content": {
                "is_supported": False
            }
        }
    },
    {
        "name": "Spotify Podcasts",
        "logo_url": "https://cdn.getphyllo.com/platforms_logo/logos/logo_spotify.png",
        "category": "ENTERTAINMENT",
        "status": "ACTIVE",
        "url": "https://www.spotify.com",
        "provider": "phyllo",
        "work_platform_id": "b42169d3-8fa5-4b3a-96eb-11735e95ba83",
        "products": {
            "identity": {
                "is_supported": True,
                "audience": {
                    "is_supported": False
                }
            },
            "engagement": {
                "is_supported": True,
                "audience": {
                    "is_supported": False
                }
            },
            "income": {
                "is_supported": False
            },
            "switch": {
                "is_supported": False
            },
            "activity": {
                "is_supported": False
            },
            "publish_content": {
                "is_supported": False
            }
        }
    },
    {
        "name": "Gumroad",
        "logo_url": "https://cdn.getphyllo.com/platforms_logo/logos/logo_gumroad.png",
        "category": "COMMERCE",
        "status": "ACTIVE",
        "url": "https://www.gumroad.com/",
        "provider": "phyllo",
        "work_platform_id": "c3914baf-e140-4042-b446-388b97a95b4c",
        "products": {
            "identity": {
                "is_supported": True,
                "audience": {
                    "is_supported": False
                }
            },
            "engagement": {
                "is_supported": False,
                "audience": {
                    "is_supported": False
                }
            },
            "income": {
                "is_supported": True
            },
            "switch": {
                "is_supported": False
            },
            "activity": {
                "is_supported": False
            },
            "publish_content": {
                "is_supported": False
            }
        }
    },
    {
        "name": "Spotify",
        "logo_url": "https://cdn.getphyllo.com/platforms_logo/logos/logo_spotify.png",
        "category": "SOCIAL",
        "status": "ACTIVE",
        "url": "https://www.spotify.com",
        "provider": "phyllo",
        "work_platform_id": "1db0b86c-a547-4119-9834-da927171a685",
        "products": {
            "identity": {
                "is_supported": False,
                "audience": {
                    "is_supported": False
                }
            },
            "engagement": {
                "is_supported": False,
                "audience": {
                    "is_supported": False
                }
            },
            "income": {
                "is_supported": False
            },
            "switch": {
                "is_supported": False
            },
            "activity": {
                "is_supported": True
            },
            "publish_content": {
                "is_supported": False
            }
        }
    },
    {
        "name": "LinkedIn",
        "logo_url": "https://cdn.getphyllo.com/platforms_logo/logos/logo_linkedin.png",
        "category": "BUSINESS",
        "status": "ACTIVE",
        "url": "https://www.linkedin.com",
        "provider": "phyllo",
        "work_platform_id": "36410629-f907-43ba-aa0d-434ca9c0501a",
        "products": {
            "identity": {
                "is_supported": True,
                "audience": {
                    "is_supported": False
                }
            },
            "engagement": {
                "is_supported": False,
                "audience": {
                    "is_supported": False
                }
            },
            "income": {
                "is_supported": False
            },
            "switch": {
                "is_supported": False
            },
            "activity": {
                "is_supported": False
            },
            "publish_content": {
                "is_supported": False
            }
        }
    },
    {
        "name": "Afreecatv",
        "logo_url": "https://cdn.getphyllo.com/platforms_logo/logos/logo_afreecatv.png",
        "category": "SOCIAL",
        "status": "ACTIVE",
        "url": "https://www.afreecatv.com/",
        "provider": "phyllo",
        "work_platform_id": "2d7b0b76-898f-4283-b86a-220556414727",
        "products": {
            "identity": {
                "is_supported": True,
                "audience": {
                    "is_supported": False
                }
            },
            "engagement": {
                "is_supported": True,
                "audience": {
                    "is_supported": False
                }
            },
            "income": {
                "is_supported": False
            },
            "switch": {
                "is_supported": False
            },
            "activity": {
                "is_supported": False
            },
            "publish_content": {
                "is_supported": False
            }
        }
    },
    {
        "name": "Ghost",
        "logo_url": "https://cdn.getphyllo.com/platforms_logo/logos/logo_ghost.png",
        "category": "SOCIAL",
        "status": "ACTIVE",
        "url": "https://www.ghost.com/",
        "provider": "phyllo",
        "work_platform_id": "5f9ff467-7c43-4487-9cd6-fb0398c290af",
        "products": {
            "identity": {
                "is_supported": True,
                "audience": {
                    "is_supported": False
                }
            },
            "engagement": {
                "is_supported": True,
                "audience": {
                    "is_supported": False
                }
            },
            "income": {
                "is_supported": False
            },
            "switch": {
                "is_supported": False
            },
            "activity": {
                "is_supported": False
            },
            "publish_content": {
                "is_supported": False
            }
        }
    },
    {
        "name": "Trovo",
        "logo_url": "https://cdn.getphyllo.com/platforms_logo/logos/logo_trovo.png",
        "category": "SOCIAL",
        "status": "ACTIVE",
        "url": "https://trovo.live/",
        "provider": "phyllo",
        "work_platform_id": "85ff0489-d4f8-4e14-af98-482568bff90e",
        "products": {
            "identity": {
                "is_supported": True,
                "audience": {
                    "is_supported": False
                }
            },
            "engagement": {
                "is_supported": True,
                "audience": {
                    "is_supported": False
                }
            },
            "income": {
                "is_supported": False
            },
            "switch": {
                "is_supported": False
            },
            "activity": {
                "is_supported": False
            },
            "publish_content": {
                "is_supported": False
            }
        }
    },
    {
        "name": "Beehiiv",
        "logo_url": "https://cdn.getphyllo.com/platforms_logo/logos/logo_beehiiv.png",
        "category": "PUBLICATION",
        "status": "ACTIVE",
        "url": "https://www.beehiiv.com/",
        "provider": "phyllo",
        "work_platform_id": "24fcaa09-0a79-4deb-b074-d8efd900265b",
        "products": {
            "identity": {
                "is_supported": False,
                "audience": {
                    "is_supported": False
                }
            },
            "engagement": {
                "is_supported": False,
                "audience": {
                    "is_supported": False
                }
            },
            "income": {
                "is_supported": False
            },
            "switch": {
                "is_supported": False
            },
            "activity": {
                "is_supported": False
            },
            "publish_content": {
                "is_supported": False
            }
        }
    },
    {
        "name": "WWW",
        "logo_url": "https://cdn.getphyllo.com/platforms_logo/logos/logo_www.png",
        "category": "GLOBAL_NETWORK",
        "status": "ACTIVE",
        "url": "",
        "provider": "phyllo",
        "work_platform_id": "a22c6022-5226-55f4-a436-3693f2148bd4",
        "products": {
            "identity": {
                "is_supported": False,
                "audience": {
                    "is_supported": False
                }
            },
            "engagement": {
                "is_supported": False,
                "audience": {
                    "is_supported": False
                }
            },
            "income": {
                "is_supported": False
            },
            "switch": {
                "is_supported": False
            },
            "activity": {
                "is_supported": False
            },
            "publish_content": {
                "is_supported": False
            }
        }
    }
]