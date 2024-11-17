import httpx
from fastapi import FastAPI, HTTPException, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.future import select
from pydantic import BaseModel
from datetime import datetime

# Database URL (Replace with your credentials)
DATABASE_URL = "postgresql+asyncpg://[your_username]:[your_password]@[your_postgres_hostip]/cricket"

# Database Setup
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

# SQLAlchemy models
class IPLLiveScores(Base):
    __tablename__ = "ipl_livescores"
    match_id: Mapped[str] = mapped_column(primary_key=True)
    league_name: Mapped[str]
    season: Mapped[int]
    team1: Mapped[str]
    team2: Mapped[str]
    venue: Mapped[str]
    match_date: Mapped[str]
    start_time: Mapped[str]
    match_status: Mapped[str]
    score1: Mapped[int]
    score2: Mapped[int]
    wickets1: Mapped[int]
    wickets2: Mapped[int]
    runs1: Mapped[int]
    runs2: Mapped[int]
    overs1: Mapped[float]
    overs2: Mapped[float]
    man_of_the_match: Mapped[str]
    umpire1: Mapped[str]
    umpire2: Mapped[str]
    match_type: Mapped[str]
    toss_winner: Mapped[str]
    batting_first: Mapped[str]
    total_runs: Mapped[int]
    extra_runs: Mapped[int]
    target_runs: Mapped[int]
    match_duration: Mapped[int]
    winning_team: Mapped[str]

class Players(Base):
    __tablename__ = "players"
    id: Mapped[int] = mapped_column(primary_key=True)
    country_id: Mapped[int]
    firstname: Mapped[str]
    lastname: Mapped[str]
    fullname: Mapped[str]
    dateofbirth: Mapped[str]
    gender: Mapped[str]
    battingstyle: Mapped[str]
    bowlingstyle: Mapped[str]
    updated_at: Mapped[str]

class Countries(Base):
    __tablename__ = "countries"
    resource: Mapped[str]
    id: Mapped[int] = mapped_column(primary_key=True)
    continent_id: Mapped[int]
    name: Mapped[str]

class ClickLog(Base):
    __tablename__ = "click_logs"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime]
    ip_address: Mapped[str]
    team_name: Mapped[str]
    location: Mapped[str]

# Pydantic model for log data
class LogEntry(BaseModel):
    ip_address: str
    team_name: str

# FastAPI app instance
app = FastAPI()

# Dependency for session management
async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session

# Geolocation lookup using ip-api
async def get_location_from_ip(ip: str) -> str:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://ip-api.com/json/{ip}")
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    return f"{data.get('city', 'Unknown')}, {data.get('country', 'Unknown')}"
                else:
                    return "Unknown Location"
            else:
                return "Unknown Location"
    except Exception:
        return "Unknown Location"

# Startup event to ensure the database schema is created
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# GET endpoint to fetch all records from ipl_livescores table
@app.get("/ipl-all")
async def get_all_records(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(IPLLiveScores))
    records = result.scalars().all()
    return records

@app.get("/players")
async def get_player_records(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Players))
    records = result.scalars().all()
    return records

@app.get("/countries")
async def get_country_records(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Countries))
    records = result.scalars().all()
    return records

@app.get("/team-results")
async def get_team_records(team1: str = Query(None), session: AsyncSession = Depends(get_session)):
    query = select(IPLLiveScores)
    if team1:
        query = query.where(IPLLiveScores.team1 == team1)

    # Execute the query
    result = await session.execute(query)
    matches = result.scalars().all()

    return matches

# POST endpoint for logging button clicks with geolocation
@app.post("/log-click")
async def log_click(log_entry: LogEntry, session: AsyncSession = Depends(get_session)):
    try:
        # Fetch location from IP
        location = await get_location_from_ip(log_entry.ip_address)

        # Create a new log entry
        new_log = ClickLog(
            timestamp=datetime.utcnow(),
            ip_address=log_entry.ip_address,
            team_name=log_entry.team_name,
            location=location
        )
        session.add(new_log)
        await session.commit()
        return {
            "message": "Log entry created successfully",
            "ip_address": log_entry.ip_address,
            "team_name": log_entry.team_name,
            "location": location
        }
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating log entry: {str(e)}")
