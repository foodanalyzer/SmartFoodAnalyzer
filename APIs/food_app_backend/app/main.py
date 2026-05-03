from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth,nutrition, depth, food,meals,users
from app.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="NutriScan API")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

app.include_router(auth.router)
app.include_router(depth.router)
app.include_router(food.router)
app.include_router(nutrition.router)
app.include_router(meals.router)
app.include_router(users.router)