from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import json
import os
from fastapi.responses import PlainTextResponse

router = APIRouter()

ONBOARDING_PATHS_FILE = os.path.join(os.path.dirname(__file__), '../onboarding_paths.json')

class OnboardingStep(BaseModel):
    instruction: str
    doc_link: Optional[str] = None

class OnboardingPathResponse(BaseModel):
    name: str
    buddy: str
    steps: List[OnboardingStep]

@router.get("/onboarding/path/{path_name}", response_model=OnboardingPathResponse)
def get_onboarding_path(path_name: str):
    try:
        with open(ONBOARDING_PATHS_FILE, 'r') as f:
            data = json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load onboarding paths: {e}")
    for path in data.get("paths", []):
        if path["name"] == path_name:
            return OnboardingPathResponse(
                name=path["name"],
                buddy=path["buddy"],
                steps=[OnboardingStep(**step) for step in path["steps"]]
            )
    raise HTTPException(status_code=404, detail=f"Onboarding path '{path_name}' not found.")

@router.get("/scripts/onboard_external.py", response_class=PlainTextResponse)
def get_onboard_external_py():
    script_path = os.path.join(os.path.dirname(__file__), "../scripts/onboard_external.py")
    with open(script_path, "r") as f:
        return f.read()

@router.get("/scripts/onboard_external.sh", response_class=PlainTextResponse)
def get_onboard_external_sh():
    script_path = os.path.join(os.path.dirname(__file__), "../scripts/onboard_external.sh")
    with open(script_path, "r") as f:
        return f.read() 