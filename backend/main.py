from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from typing import List
import uvicorn
import random

from models import Recommendation, ChatMessage, UserProfile
from database import engine, create_db_and_tables, get_session
from ai_service import get_ai_response, analyze_interests, score_recommendations, get_chat_and_interests

from fastapi.staticfiles import StaticFiles
import os

app = FastAPI(title="AuraAI - Enhanced")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files at the end (moved after routes is better practice, but mount works)
# We will do it after the routes are defined to ensure API routes take precedence.

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    # Seed initial content if empty
    with Session(engine) as session:
        # Seed User if not exists
        if not session.get(UserProfile, 1):
            session.add(UserProfile(id=1, interests=""))
        
        statement = select(Recommendation)
        results = session.exec(statement).all()
        if not results:
            initial_content = [
                Recommendation(
                    title="Meta Prometheus Supercluster", 
                    description="January 2026 update: Meta secures 6.6GW of nuclear energy for its massive AI supercluster in Ohio.", 
                    category="Tech News", 
                    image_url="https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=800&q=80",
                    url="https://about.fb.com/news/"
                ),
                Recommendation(
                    title="Falcon-H1R 7B Breakthrough", 
                    description="TII reveals the Falcon-H1R 7B, proving mid-sized models can match goliaths in performance.", 
                    category="AI", 
                    image_url="https://images.unsplash.com/photo-1677442136019-21780ecad995?auto=format&fit=crop&w=800&q=80",
                    url="https://tii.ae/news"
                ),
                Recommendation(
                    title="Regenerative Timber Design", 
                    description="2026 architecture shifts towards timber and stone, prioritizing low-carbon, characterful forms over minimalism.", 
                    category="Architecture", 
                    image_url="https://images.unsplash.com/photo-1518005020250-68a377a747e7?auto=format&fit=crop&w=800&q=80",
                    url="https://www.vectorworks.net/blog"
                ),
                Recommendation(
                    title="Solarpunk Community Infrastructure", 
                    description="The Solarpunk community is launching initiatives to connect industrial solar projects directly to citizens.", 
                    category="Sustainability", 
                    image_url="https://images.unsplash.com/photo-1508514177221-188b1cf16e9d?auto=format&fit=crop&w=800&q=80",
                    url="https://solarpunkmagazine.com/"
                ),
                Recommendation(
                    title="The Prototype Economy", 
                    description="AI is accelerating product development cycles, creating a 'prototype economy' for rapid innovation.", 
                    category="Economy", 
                    image_url="https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?auto=format&fit=crop&w=800&q=80",
                    url="https://www.captechconsulting.com/blogs"
                ),
                Recommendation(
                    title="Bio-Digital Evolution", 
                    description="Latest research shows AI acting as central 'lab assistants' in physics and biology experimental cycles.", 
                    category="Science", 
                    image_url="https://images.unsplash.com/photo-1532187863486-abf9d39d6627?auto=format&fit=crop&w=800&q=80",
                    url="https://www.microsoft.com/en-us/research/blog/"
                ),
                Recommendation(
                    title="Generative Engine Optimization", 
                    description="Marketing shifts from SEO to GEO as brands optimize content specifically for AI chat discovery.", 
                    category="Marketing", 
                    image_url="https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=800&q=80",
                    url="https://www.stanberry.com/blog"
                ),
                Recommendation(
                    title="Solarpunk Magazine 5th Anniversary", 
                    description="Celebrating 5 years of optimistic literature with the 'Radical Hope' series launch.", 
                    category="Culture", 
                    image_url="https://images.unsplash.com/photo-1544947950-fa07a98d237f?auto=format&fit=crop&w=800&q=80",
                    url="https://solarpunkmagazine.com/issues/"
                ),
            ]
            for item in initial_content:
                session.add(item)
            session.commit()

@app.get("/")
async def root():
    return {"message": "AuraAI Enhanced API is running with SQLModel and Gemini"}

@app.post("/chat")
async def chat(request: dict, session: Session = Depends(get_session)):
    user_message = request.get("message")
    if not user_message:
        raise HTTPException(status_code=400, detail="Message is required")

    # Store user message
    db_msg = ChatMessage(role="user", content=user_message)
    session.add(db_msg)
    
    # Get current user profile
    user = session.get(UserProfile, 1)
    if not user:
        user = UserProfile(id=1, interests="")
        session.add(user)
    
    # Combined AI call to save quota (1 call instead of 2)
    ai_data = await get_chat_and_interests(user_message, user.interests)
    ai_reply = ai_data["reply"]
    new_interests = ai_data["interests"]
    
    user.interests = new_interests
    
    # Store AI response
    db_ai_msg = ChatMessage(role="ai", content=ai_reply)
    session.add(db_ai_msg)
    
    session.commit()
    return {"reply": ai_reply}

@app.get("/recommendations", response_model=List[Recommendation])
async def get_recommendations(session: Session = Depends(get_session)):
    user = session.get(UserProfile, 1)
    interests = [i.strip() for i in user.interests.split(",")] if user and user.interests else []
    
    statement = select(Recommendation)
    all_items = session.exec(statement).all()
    
    if not all_items:
        return []

    if not interests:
        return random.sample(all_items, min(len(all_items), 6))
    
    # Use Gemini to score items for better "relatedness"
    items_dicts = [{"id": i, "title": r.title, "category": r.category, "description": r.description} for i, r in enumerate(all_items)]
    scored_results = await score_recommendations(interests, items_dicts)
    
    # Sort by score and convert back to original objects
    # scored_results is a list of (score, item_dict) tuples
    scored_results.sort(key=lambda x: x[0], reverse=True)
    
    top_items = []
    for score, item_dict in scored_results:
        original_item = all_items[item_dict["id"]]
        top_items.append(original_item)
        
    return top_items[:6]

# Serve frontend static files
# We check if the dir exists to avoid crashes in local dev if not built
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
