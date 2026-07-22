import os
import sys
from datetime import date
from dotenv import load_dotenv

# Add backend to path so we can import src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

from src.config.db import get_db
from src.services.gemini_engine import embed_text

PRECEDENTS = [
    {
        "event_title": "1973 Oil Crisis (Yom Kippur War)",
        "event_date": date(1973, 10, 19),
        "description": "OAPEC proclaimed an oil embargo targeted at nations perceived as supporting Israel. The embargo caused an oil shock with severe price increases and supply chain blockades.",
        "economic_impact_summary": "Global oil prices quadrupled from $3 to nearly $12 per barrel. GDP growth dropped globally, leading to severe inflation and rationing."
    },
    {
        "event_title": "2021 Suez Canal Obstruction (Ever Given)",
        "event_date": date(2021, 3, 23),
        "description": "The Ever Given, a 20,000 TEU container ship, ran aground in the Suez Canal, blocking the global shipping chokepoint for six days and stalling billions of dollars in maritime trade, including crude carriers.",
        "economic_impact_summary": "Held up an estimated $9.6 billion of trade per day. Freight rates spiked up to 300% temporarily, though structural crude prices saw only a brief 4% hike before stabilizing."
    },
    {
        "event_title": "1990 Gulf War Oil Shock",
        "event_date": date(1990, 8, 2),
        "description": "The invasion of Kuwait by Iraq led to military escalation in the Middle East and the loss of millions of barrels of daily supply due to sanctions and war destruction.",
        "economic_impact_summary": "Oil prices doubled from $21 to $46 per barrel in three months. The U.S. GDP dropped, leading to a recession in early 1991."
    },
    {
        "event_title": "2019 Abqaiq-Khurais Attack",
        "event_date": date(2019, 9, 14),
        "description": "Drone attacks on Saudi Aramco's facilities knocked out 5.7 million barrels of daily crude production, approximately 5% of global supply, triggering an immediate and severe supply shock.",
        "economic_impact_summary": "Brent crude spiked nearly 20% in one day (the largest intraday jump ever). Prices stabilized quickly after Saudi Arabia announced a rapid return to production using existing reserves."
    }
]

def seed():
    print("Connecting to Supabase...")
    db = get_db()
    
    print("Clearing old precedents...")
    try:
        db.table("historical_precedents").delete().neq("id", 0).execute()
    except Exception as e:
        pass

    print("Generating embeddings and seeding data...")
    for p in PRECEDENTS:
        # Create a rich text representation to embed
        text_to_embed = f"Event: {p['event_title']}. Date: {p['event_date']}. Description: {p['description']} Economic Impact: {p['economic_impact_summary']}"
        print(f"Embedding: {p['event_title']}...")
        
        try:
            emb = embed_text(text_to_embed)
            emb_str = "[" + ",".join(map(str, emb)) + "]"
            
            # Escape single quotes in text
            title = p["event_title"].replace("'", "''")
            desc = p["description"].replace("'", "''")
            impact = p["economic_impact_summary"].replace("'", "''")
            date_str = p["event_date"].isoformat()
            
            sql = f"INSERT INTO historical_precedents (event_title, event_date, description, economic_impact_summary, embedding) VALUES ('{title}', '{date_str}', '{desc}', '{impact}', '{emb_str}');"
            print(sql)
            print("---")
            
        except Exception as e:
            print(f" -> Failed to embed: {e}")
            
    print("Done seeding precedents.")

if __name__ == "__main__":
    seed()
