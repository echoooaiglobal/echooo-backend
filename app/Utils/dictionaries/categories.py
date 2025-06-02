# app/Utils/dictionaries/categories.py

"""
Default categories for the influencer marketing platform
"""

DEFAULT_CATEGORIES = [
    {
        "name": "Television & Film",
        "description": "Entertainment industry, movies, TV shows, streaming content"
    },
    {
        "name": "Music",
        "description": "Music industry, artists, concerts, musical instruments"
    },
    {
        "name": "Shopping & Retail",
        "description": "Retail stores, shopping experiences, consumer goods"
    },
    {
        "name": "Coffee, Tea & Beverages",
        "description": "Hot and cold beverages, cafes, drink brands"
    },
    {
        "name": "Camera & Photography",
        "description": "Photography equipment, techniques, visual arts"
    },
    {
        "name": "Clothes, Shoes, Handbags & Accessories",
        "description": "Fashion items, clothing brands, style accessories"
    },
    {
        "name": "Beer, Wine & Spirits",
        "description": "Alcoholic beverages, breweries, wine tasting"
    },
    {
        "name": "Sports",
        "description": "Athletic activities, sports teams, competitions"
    },
    {
        "name": "Electronics & Computers",
        "description": "Technology products, gadgets, computer hardware"
    },
    {
        "name": "Gaming",
        "description": "Video games, gaming equipment, esports"
    },
    {
        "name": "Activewear",
        "description": "Athletic clothing, workout gear, sports apparel"
    },
    {
        "name": "Art & Design",
        "description": "Visual arts, graphic design, creative industries"
    },
    {
        "name": "Travel, Tourism & Aviation",
        "description": "Travel destinations, tourism, airlines, hotels"
    },
    {
        "name": "Business & Careers",
        "description": "Professional development, entrepreneurship, workplace"
    },
    {
        "name": "Beauty & Cosmetics",
        "description": "Makeup, skincare, beauty products and treatments"
    },
    {
        "name": "Healthcare & Medicine",
        "description": "Medical services, health products, wellness"
    },
    {
        "name": "Jewellery & Watches",
        "description": "Fine jewelry, timepieces, luxury accessories"
    },
    {
        "name": "Restaurants, Food & Grocery",
        "description": "Dining, culinary experiences, food products"
    },
    {
        "name": "Toys, Children & Baby",
        "description": "Children's products, toys, parenting, baby care"
    },
    {
        "name": "Fitness & Yoga",
        "description": "Physical fitness, yoga, wellness routines"
    },
    {
        "name": "Wedding",
        "description": "Wedding planning, bridal fashion, ceremonies"
    },
    {
        "name": "Tobacco & Smoking",
        "description": "Tobacco products, smoking accessories (regulated content)"
    },
    {
        "name": "Pets",
        "description": "Pet care, animal products, veterinary services"
    },
    {
        "name": "Healthy Lifestyle",
        "description": "Wellness, healthy living, nutrition, mental health"
    },
    {
        "name": "Luxury Goods",
        "description": "High-end products, premium brands, luxury experiences"
    },
    {
        "name": "Home Decor, Furniture & Garden",
        "description": "Interior design, home improvement, gardening"
    },
    {
        "name": "Friends, Family & Relationships",
        "description": "Social relationships, family life, personal connections"
    },
    {
        "name": "Cars & Motorbikes",
        "description": "Automotive industry, vehicles, transportation"
    }
]

# Category hierarchy - for future use if you want subcategories
CATEGORY_HIERARCHY = {
    "Lifestyle": [
        "Healthy Lifestyle",
        "Friends, Family & Relationships",
        "Wedding"
    ],
    "Fashion & Beauty": [
        "Beauty & Cosmetics",
        "Clothes, Shoes, Handbags & Accessories",
        "Jewellery & Watches",
        "Activewear"
    ],
    "Technology": [
        "Electronics & Computers",
        "Gaming",
        "Camera & Photography"
    ],
    "Entertainment": [
        "Television & Film",
        "Music",
        "Gaming"
    ],
    "Health & Fitness": [
        "Healthcare & Medicine",
        "Fitness & Yoga",
        "Healthy Lifestyle"
    ],
    "Food & Beverage": [
        "Restaurants, Food & Grocery",
        "Coffee, Tea & Beverages",
        "Beer, Wine & Spirits"
    ],
    "Home & Living": [
        "Home Decor, Furniture & Garden",
        "Pets"
    ],
    "Business & Professional": [
        "Business & Careers"
    ],
    "Travel & Automotive": [
        "Travel, Tourism & Aviation",
        "Cars & Motorbikes"
    ]
}
