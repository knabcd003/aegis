from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class HorizonAllocation(BaseModel):
    label: Optional[str] = None
    min_days: Optional[int] = None
    max_days: Optional[int] = None
    capital_weight: Optional[float] = None

class UniverseHardFilters(BaseModel):
    asset_classes_permitted: Optional[List[str]] = Field(default_factory=list)
    market_cap_range: Optional[str] = None
    min_avg_daily_volume_usd: Optional[float] = None
    price_range: Optional[str] = None
    geographies_permitted: Optional[List[str]] = Field(default_factory=list)
    sectors_of_interest: Optional[List[str]] = Field(default_factory=list)
    sectors_to_avoid: Optional[List[str]] = Field(default_factory=list)
    esg_exclusions: Optional[List[str]] = Field(default_factory=list)
    specific_tickers_focus: Optional[List[str]] = Field(default_factory=list)
    specific_tickers_exclude: Optional[List[str]] = Field(default_factory=list)
    tickers_never_touch: Optional[List[str]] = Field(default_factory=list)

class MandateHardConstraints(BaseModel):
    tier: Optional[int] = Field(1, alias="_tier")
    note: Optional[str] = Field(None, alias="_note")
    investable_capital: Optional[float] = None
    max_portfolio_drawdown_pct: Optional[float] = None
    max_single_position_pct: Optional[float] = None
    max_concurrent_live_strategies: Optional[int] = None
    leverage_permitted: Optional[bool] = False
    account_type: Optional[str] = None
    horizon_allocation: Optional[List[HorizonAllocation]] = Field(default_factory=list)
    universe_hard_filters: Optional[UniverseHardFilters] = Field(default_factory=UniverseHardFilters)

class OrderedPriority(BaseModel):
    rank: Optional[int] = None
    dimension: Optional[str] = None
    rationale: Optional[str] = None

class PreferenceFlexibility(BaseModel):
    preference: Optional[str] = None
    flexibility: Optional[str] = None
    rationale: Optional[str] = None

class MandatePriorityHierarchy(BaseModel):
    tier: Optional[int] = Field(2, alias="_tier")
    builder_note: Optional[str] = Field(None, alias="_builder_note")
    ordered_priorities: Optional[List[OrderedPriority]] = Field(default_factory=list)
    preference_flexibility: Optional[List[PreferenceFlexibility]] = Field(default_factory=list)
    trade_off_philosophy: Optional[str] = None
    conflict_notes: Optional[str] = None

class InvestorProfile(BaseModel):
    tier: Optional[int] = Field(2, alias="_tier")
    builder_note: Optional[str] = Field(None, alias="_builder_note")
    summary: Optional[str] = None
    investment_experience: Optional[str] = None
    portfolio_context: Optional[str] = None
    time_availability: Optional[str] = None
    behavioral_history: Optional[str] = None

class RiskProfile(BaseModel):
    tier: Optional[int] = Field(2, alias="_tier")
    builder_note: Optional[str] = Field(None, alias="_builder_note")
    summary: Optional[str] = None
    volatility_tolerance: Optional[str] = None
    gap_risk_tolerance: Optional[str] = None
    concentration_tolerance: Optional[str] = None
    tail_risk_tolerance: Optional[str] = None
    time_risk_tolerance: Optional[str] = None
    correlation_risk: Optional[str] = None
    regret_asymmetry: Optional[str] = None
    loss_aversion_context: Optional[str] = None

class PerformanceTargets(BaseModel):
    tier: Optional[int] = Field(2, alias="_tier")
    builder_note: Optional[str] = Field(None, alias="_builder_note")
    primary_objective: Optional[str] = None
    target_annual_return_pct: Optional[float] = None
    target_annual_return_context: Optional[str] = None
    benchmark: Optional[str] = None
    benchmark_context: Optional[str] = None
    return_character: Optional[str] = None
    min_acceptable_sharpe: Optional[float] = None
    target_win_rate_pct: Optional[float] = None
    max_acceptable_consecutive_losses: Optional[int] = None
    target_monthly_income_usd: Optional[float] = None
    target_return_horizon_months: Optional[float] = None
    success_definition: Optional[str] = None
    failure_definition: Optional[str] = None

class UniverseMandate(BaseModel):
    tier: Optional[int] = Field(2, alias="_tier")
    builder_note: Optional[str] = Field(None, alias="_builder_note")
    raw_desire: Optional[str] = None
    universe_description: Optional[str] = None
    sector_reasoning: Optional[str] = None
    asset_class_preferences: Optional[str] = None
    liquidity_and_price_character: Optional[str] = None
    equity_character: Optional[str] = None
    fundamental_screens: Optional[str] = None
    options_context: Optional[str] = None
    etf_preferences: Optional[str] = None
    existing_holdings: Optional[List[str]] = Field(default_factory=list)

class StrategyIntent(BaseModel):
    tier: Optional[int] = Field(2, alias="_tier")
    builder_note: Optional[str] = Field(None, alias="_builder_note")
    regime_preferences: Optional[str] = None
    regime_universe_pairs: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    catalyst_preferences: Optional[str] = None
    entry_philosophy: Optional[str] = None
    exit_philosophy: Optional[str] = None
    holding_philosophy: Optional[str] = None
    signal_type_preferences: Optional[str] = None
    complexity_preference: Optional[str] = None
    strategy_types_to_avoid: Optional[str] = None

class HorizonMandate(BaseModel):
    tier: Optional[int] = Field(2, alias="_tier")
    builder_note: Optional[str] = Field(None, alias="_builder_note")
    description: Optional[str] = None
    horizon_details: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    intraday_tolerance: Optional[str] = None
    overnight_tolerance: Optional[str] = None

class PortfolioScope(BaseModel):
    tier: Optional[int] = Field(2, alias="_tier")
    builder_note: Optional[str] = Field(None, alias="_builder_note")
    ambition_description: Optional[str] = None
    diversification_intent: Optional[str] = None
    correlation_intent: Optional[str] = None
    market_beta_intent: Optional[str] = None
    portfolio_beta_existing: Optional[str] = None
    pipeline_growth_intent: Optional[str] = None

class MarketContext(BaseModel):
    tier: Optional[int] = Field(2, alias="_tier")
    builder_note: Optional[str] = Field(None, alias="_builder_note")
    macro_views: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    current_regime_beliefs: Optional[str] = None
    regime_adaptivity_intent: Optional[str] = None
    sectors_with_tailwinds: Optional[str] = None
    sectors_with_headwinds: Optional[str] = None

class ExecutionProfile(BaseModel):
    tier: Optional[int] = Field(2, alias="_tier")
    builder_note: Optional[str] = Field(None, alias="_builder_note")
    available_windows: Optional[str] = None
    pre_post_market_capable: Optional[bool] = False
    execution_latency_context: Optional[str] = None
    order_type_philosophy: Optional[str] = None
    brokerage_constraints: Optional[str] = None

class ExclusionsAndConstraints(BaseModel):
    tier: Optional[int] = Field(2, alias="_tier")
    builder_note: Optional[str] = Field(None, alias="_builder_note")
    strategy_type_exclusions: Optional[str] = None
    instrument_exclusions: Optional[str] = None
    concentration_constraints: Optional[str] = None
    tax_considerations: Optional[str] = None

class FilingNotes(BaseModel):
    tier: Optional[int] = Field(2, alias="_tier")
    builder_note: Optional[str] = Field(None, alias="_builder_note")
    explicit_vs_inferred_summary: Optional[str] = None
    contradictions: Optional[List[str]] = Field(default_factory=list)
    expectation_corrections: Optional[List[str]] = Field(default_factory=list)
    open_questions: Optional[List[str]] = Field(default_factory=list)
    conversation_quality_note: Optional[str] = None

class V9IntakeSchema(BaseModel):
    schema_version: Optional[str] = Field(None, alias="_schema_version")
    path: Optional[str] = Field(None, alias="_path")
    path_note: Optional[str] = Field(None, alias="_path_note")
    for_llm: Optional[str] = Field(None, alias="_for_llm")
    builder_note: Optional[str] = Field(None, alias="_builder_note")

    mandate_hard_constraints: Optional[MandateHardConstraints] = Field(default_factory=MandateHardConstraints)
    mandate_priority_hierarchy: Optional[MandatePriorityHierarchy] = Field(default_factory=MandatePriorityHierarchy)
    investor_profile: Optional[InvestorProfile] = Field(default_factory=InvestorProfile)
    risk_profile: Optional[RiskProfile] = Field(default_factory=RiskProfile)
    performance_targets: Optional[PerformanceTargets] = Field(default_factory=PerformanceTargets)
    universe_mandate: Optional[UniverseMandate] = Field(default_factory=UniverseMandate)
    strategy_intent: Optional[StrategyIntent] = Field(default_factory=StrategyIntent)
    horizon_mandate: Optional[HorizonMandate] = Field(default_factory=HorizonMandate)
    portfolio_scope: Optional[PortfolioScope] = Field(default_factory=PortfolioScope)
    market_context: Optional[MarketContext] = Field(default_factory=MarketContext)
    execution_profile: Optional[ExecutionProfile] = Field(default_factory=ExecutionProfile)
    exclusions_and_constraints: Optional[ExclusionsAndConstraints] = Field(default_factory=ExclusionsAndConstraints)
    filing_notes: Optional[FilingNotes] = Field(default_factory=FilingNotes)

class ValidationResponse(BaseModel):
    mandate_summary: Dict[str, str]
    hard_errors: List[str]
    soft_contradictions: List[str]
    inferred_flags: List[str]
    is_valid: bool

class ConfirmResponse(BaseModel):
    workflow_id: str
    status: str
