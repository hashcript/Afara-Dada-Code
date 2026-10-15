"""
Mock database of vetted African Female Tech Empowerment Organizations.
This represents the 'Trusted Data Layer' your agent accesses.

Region keys: 'pan-africa', 'west-africa', 'east-africa', 'global-diaspora'.
Queries are normalized via REGION_ALIASES, so callers can pass natural
inputs like 'Kenya', 'West Africa', or 'africa' and still get results.
"""

# Normalized database of 5 highly credible organizations
initiatives_db = {
    "pan-africa": [
        {
            "name": "She Code Africa",
            "hq": "Lagos, Nigeria (West Africa)",
            "mission": "To build a community that embodies technical growth, networking, mentorship, and visibility for women in tech across Africa.",
            "impact_metrics": "62,000+ women trained, 40+ chapters across 20 countries.",
            "rating": 4.9,
            "efficiency": 0.95, # 95% of funds go directly to training programs
            "verification_source": "Registered Non-Profit; Partnered with Grow with Google & FedEx.",
            "website": "shecodeafrica.org"
        },
        {
            "name": "Women in Tech Africa",
            "hq": "Accra, Ghana (West Africa)",
            "mission": "Supporting African women to positively impact their communities through technology and leadership.",
            "impact_metrics": "Largest female tech group on the continent with chapters in 30 countries.",
            "rating": 4.8,
            "efficiency": 0.90,
            "verification_source": "Endorsed by the Graca Machel Trust; Founded by Ethel D. Cofie.",
            "website": "womenintechafrica.com"
        }
    ],
    "west-africa": [
        {
            "name": "She Code Africa",
            "hq": "Lagos, Nigeria (West Africa)",
            "mission": "To build a community that embodies technical growth, networking, mentorship, and visibility for women in tech across Africa.",
            "impact_metrics": "62,000+ women trained, 40+ chapters across 20 countries.",
            "rating": 4.9,
            "efficiency": 0.95, # 95% of funds go directly to training programs
            "verification_source": "Registered Non-Profit; Partnered with Grow with Google & FedEx.",
            "website": "shecodeafrica.org"
        },
        {
            "name": "Women in Tech Africa",
            "hq": "Accra, Ghana (West Africa)",
            "mission": "Supporting African women to positively impact their communities through technology and leadership.",
            "impact_metrics": "Largest female tech group on the continent with chapters in 30 countries.",
            "rating": 4.8,
            "efficiency": 0.90,
            "verification_source": "Endorsed by the Graca Machel Trust; Founded by Ethel D. Cofie.",
            "website": "womenintechafrica.com"
        }
    ],
    "east-africa": [
        {
            "name": "Pwani Teknowgalz",
            "hq": "Mombasa, Kenya (East Africa)",
            "mission": "To equip young women in marginalized communities (especially coastal Kenya) with employable tech skills.",
            "impact_metrics": "Empowered 6,800+ girls; 400+ secured jobs via CodeHack program.",
            "rating": 4.9,
            "efficiency": 0.92,
            "verification_source": "Awarded by Technovation; Partners with American Space Mombasa.",
            "website": "pwaniteknowgalz.org"
        },
        {
            "name": "Tambua Women in Tech",
            "hq": "Nairobi, Kenya (East Africa)",
            "mission": "To spotlight, recognize ('Tambua'), and amplify the voices of African women in STEM to create role models.",
            "impact_metrics": "Celebrated 350+ women globally; Hosting major 2025 Summit.",
            "rating": 4.7,
            "efficiency": 0.88,
            "verification_source": "Community-driven platform; Recognized by Google Developer Experts program.",
            "website": "womenintechblog.dev"
        }
    ],
    "global-diaspora": [
         {
            "name": "Empower Her Community",
            "hq": "Global (Strong African Presence)",
            "mission": "A tech-based community focused on training and promoting women of color in the field of information technology for free.",
            "impact_metrics": "5,000+ women empowered; 3,000+ trained in technical bootcamps.",
            "rating": 4.8,
            "efficiency": 0.94,
            "verification_source": " Verified Non-Profit Community; High engagement in open-source contributions.",
            "website": "empowerhercommunity.net"
        }
    ]
}

# Maps natural-language region/country inputs to the database keys above,
# so both users and the LLM can pass whatever phrasing they naturally use.
REGION_ALIASES = {
    # Continent-wide
    "africa": "africa",
    "african": "africa",
    "all": "africa",
    "pan africa": "pan-africa",
    "pan-african": "pan-africa",
    "continent": "pan-africa",

    # West Africa (countries + phrasings)
    "west africa": "west-africa",
    "western africa": "west-africa",
    "nigeria": "west-africa",
    "lagos": "west-africa",
    "ghana": "west-africa",
    "accra": "west-africa",
    "senegal": "west-africa",
    "cote d'ivoire": "west-africa",
    "ivory coast": "west-africa",

    # East Africa (countries + phrasings)
    "east africa": "east-africa",
    "eastern africa": "east-africa",
    "kenya": "east-africa",
    "nairobi": "east-africa",
    "mombasa": "east-africa",
    "tanzania": "east-africa",
    "uganda": "east-africa",
    "rwanda": "east-africa",
    "ethiopia": "east-africa",

    # Global / diaspora
    "global": "global-diaspora",
    "diaspora": "global-diaspora",
    "global diaspora": "global-diaspora",
    "international": "global-diaspora",
}


def _normalize_region(region: str) -> str:
    """Normalizes a region/country query to a database key (or 'africa')."""
    key = region.strip().lower().replace("_", "-").replace(" ", "-")
    # Try the raw normalized key first (e.g. 'east-africa' passed through)
    if key in initiatives_db or key == "africa":
        return key
    # Then try alias lookup with spaces preserved (e.g. 'west africa')
    return REGION_ALIASES.get(region.strip().lower(), key)


def get_initiatives_by_region(region: str):
    """
    Returns a list of vetted female tech empowerment initiatives for a given
    African region. Accepts region keys ('east-africa', 'west-africa',
    'pan-africa', 'global-diaspora'), country/city names ('kenya', 'nigeria'),
    or 'africa' to return every initiative in the database.
    """
    normalized = _normalize_region(region)

    # Return all if 'africa' (or an alias of it) is requested
    if normalized == "africa":
        all_initiatives = []
        seen_names = set()
        for key in initiatives_db:
            for initiative in initiatives_db[key]:
                # Orgs operating continent-wide appear in multiple regions;
                # only list each once.
                if initiative["name"] not in seen_names:
                    seen_names.add(initiative["name"])
                    all_initiatives.append(initiative)
        return all_initiatives

    return initiatives_db.get(normalized, [])
