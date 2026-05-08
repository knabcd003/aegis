from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, List

from api.prompts.section_validators import SECTION_PROMPTS
from engines.system.llm_adapter import LLMAdapter
import json

router = APIRouter()
llm_adapter = LLMAdapter()

class ContradictionEntry(BaseModel):
    field: str
    issue: str

class ValidationResponse(BaseModel):
    prose_fields: Dict[str, str]
    gap_questions: List[str]
    contradictions: List[ContradictionEntry]
    section_complete: bool

class ValidateSectionRequest(BaseModel):
    section_id: int
    structured_fields: Dict[str, Any]
    detail_text: str

@router.post("/validate_section", response_model=ValidationResponse)
async def validate_section(req: ValidateSectionRequest):
    if not req.detail_text.strip():
        return ValidationResponse(
            prose_fields={},
            gap_questions=["Please provide some detail about this section to proceed."],
            contradictions=[],
            section_complete=False
        )

    prompt_template = SECTION_PROMPTS.get(req.section_id)
    if not prompt_template:
        return ValidationResponse(
            prose_fields={},
            gap_questions=[],
            contradictions=[],
            section_complete=True
        )

    structured_str = str(req.structured_fields)
    
    messages = [
        {"role": "system", "content": prompt_template},
        {"role": "user", "content": f"Structured Inputs: {structured_str}\nDetail Text: {req.detail_text}\n\nRespond with ONLY valid JSON."}
    ]

    # Stateless LLM call for extraction
    try:
        adapter_res = llm_adapter.invoke(
            messages=messages,
            role="structured_extraction",
            workflow_id="intake_validation",
            node_id=f"val_sec_{req.section_id}"
        )
        content = adapter_res.content
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        response_data = json.loads(content)
    except Exception as e:
        # Fallback if parsing fails or LLM errors
        return ValidationResponse(
            prose_fields={},
            gap_questions=[],
            contradictions=[ContradictionEntry(field="System", issue=str(e))],
            section_complete=False
        )

    prose = response_data.get("prose_fields", {})
    gaps = response_data.get("gap_questions", [])
    
    contradictions_raw = response_data.get("contradictions", [])
    contradictions = []
    for c in contradictions_raw:
        if isinstance(c, dict) and "field" in c and "issue" in c:
            contradictions.append(ContradictionEntry(field=c["field"], issue=c["issue"]))
            
    is_complete = len(gaps) == 0 and len(contradictions) == 0

    return ValidationResponse(
        prose_fields=prose,
        gap_questions=gaps,
        contradictions=contradictions,
        section_complete=is_complete
    )
