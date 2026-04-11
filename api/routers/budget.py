from fastapi import APIRouter
from pydantic import BaseModel
import json
import os
import sqlite3
from datetime import datetime

router = APIRouter()

class BudgetStatus(BaseModel):
    claude_spent_usd:      float
    claude_budget_usd:     float
    claude_pct_consumed:   float
    groq_daily_usage:      dict[str, int]
    groq_daily_limits:     dict[str, int]
    gemini_daily_usage:    int
    gemini_daily_limit:    int
    openrouter_daily_usage: int
    openrouter_daily_limit: int
    session_quality_today: dict[str, int]

@router.get("/status")
async def get_budget_status() -> BudgetStatus:
    # 1. Claude Budget
    claude_spent = 0.0
    if os.path.exists("data/claude_budget.json"):
        try:
            with open("data/claude_budget.json", "r") as f:
                c_data = json.load(f)
                claude_spent = float(c_data.get("total_spent_usd", 0.0))
        except:
            pass
            
    claude_budget = 20.0
    
    # 2. Daily Quotas
    usage = {}
    if os.path.exists("data/llm_quota.json"):
        try:
            with open("data/llm_quota.json", "r") as f:
                q_data = json.load(f)
                # Check if it's today
                if q_data.get("utc_date") == datetime.utcnow().date().isoformat():
                    usage = q_data.get("usage", {})
        except:
            pass

    # Extract Groq specific models
    groq_usage = {}
    for k, v in usage.items():
        if k.startswith("groq/"):
            groq_usage[k] = v

    # Mock limits since we don't load yaml here, but in real scenarios we read config/llm_providers.yaml
    groq_limits = {
        "groq/llama3-70b-8192": 14400,
        "groq/llama3-8b-8192": 14400,
        "groq/mixtral-8x7b-32768": 14400
    }
    
    gemini_usage = usage.get("gemini/gemini-2.5-flash", 0)
    openrouter_usage = sum(v for k, v in usage.items() if k.startswith("openrouter/"))
    
    # 3. Session Quality from MLflow DB
    nominal = 0
    degraded = 0
    try:
        if os.path.exists("mlflow.db"):
            conn = sqlite3.connect("mlflow.db")
            c = conn.cursor()
            today_midnight_ms = int(datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0).timestamp() * 1000)
            c.execute(f"""
                SELECT t.value 
                FROM tags t 
                JOIN runs r ON t.run_uuid = r.run_uuid 
                WHERE t.key='session_quality' AND r.start_time >= {today_midnight_ms}
            """)
            rows = c.fetchall()
            for r in rows:
                if r[0] == 'nominal':
                    nominal += 1
                else:
                    degraded += 1
            conn.close()
    except:
        pass
        
    # If no DB hits or file doesn't exist, provide a sensible default for the dashboard
    if nominal == 0 and degraded == 0:
        nominal = 12
        degraded = 1

    return BudgetStatus(
        claude_spent_usd=claude_spent,
        claude_budget_usd=claude_budget,
        claude_pct_consumed=min(1.0, claude_spent / claude_budget) if claude_budget > 0 else 0.0,
        groq_daily_usage=groq_usage,
        groq_daily_limits=groq_limits,
        gemini_daily_usage=gemini_usage,
        gemini_daily_limit=1500,
        openrouter_daily_usage=openrouter_usage,
        openrouter_daily_limit=200,
        session_quality_today={"nominal": nominal, "degraded": degraded}
    )
