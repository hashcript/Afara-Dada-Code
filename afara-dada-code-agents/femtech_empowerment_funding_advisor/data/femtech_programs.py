"""
Mock database of vetted African Female Tech Empowerment Organizations.
This represents the 'Trusted Data Layer' your agent accesses.
"""

def get_initiatives_by_region(region: str):
    """Returns a list of vetted female tech empowerment initiatives for a given African region.

    Accepts a region key ('pan-africa', 'east-africa', 'global-diaspora'), 'africa'/'all'
    for every initiative, or a location (country, city or sub-region) matched against HQ.
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
                "verification_source": "Verified Non-Profit Community; High engagement in open-source contributions.",
                "website": "empowerhercommunity.net"
            }
        ]
    }

    # Normalize free-text input (e.g. "East Africa", "east_africa") to the db keys ("east-africa")
    region_key = "-".join(region.strip().lower().replace("_", " ").split())

    all_initiatives = []
    for key in initiatives_db:
        all_initiatives.extend(initiatives_db[key])

    # Helper logic to return all if 'africa' is requested, otherwise specific region
    if region_key in ("africa", "all"):
        return all_initiatives

    if region_key in initiatives_db:
        return initiatives_db[region_key]

    # Fall back to matching the HQ location, so countries, cities and sub-regions
    # without their own key (e.g. "Kenya", "Nigeria", "West Africa") still resolve
    location = region_key.replace("-", " ")
    return [i for i in all_initiatives if location in i["hq"].lower()]