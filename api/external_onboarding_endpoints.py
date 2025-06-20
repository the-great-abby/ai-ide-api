"""External Onboarding API Endpoints
Provides access to onboarding scripts and generated files for external users.
"""

import os
import json
import tempfile
import zipfile
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import FileResponse, StreamingResponse
import io

from auth import require_api_token
from db import ApiAccessToken, get_db
from sqlalchemy.orm import Session
from scripts.generate_external_makefile import generate_makefile

router = APIRouter(prefix="/external", tags=["external-onboarding"])

# Configuration
SCRIPTS_DIR = "scripts"
GENERATED_DIR = "."

# Files that are part of the onboarding package
ONBOARDING_FILES = [
    "onboard_external.sh",
    "onboard_external_updated.py",
    "generate_external_makefile.py"
]

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint for external onboarding.
    This endpoint is public and does not require authentication.
    """
    return {
        "status": "healthy",
        "service": "external-onboarding",
        "message": "External onboarding service is running"
    }

@router.get("/onboarding/files")
async def list_onboarding_files() -> Dict[str, Any]:
    """
    List all available onboarding files.
    This endpoint is public and does not require authentication.
    """
    files = {
        "scripts": {
            "onboard_external.sh": {
                "description": "Shell script for external project onboarding",
                "size": "~3KB",
                "usage": "chmod +x onboard_external.sh && ./onboard_external.sh"
            },
            "onboard_external_updated.py": {
                "description": "Python script for external project onboarding",
                "size": "~15KB", 
                "usage": "python onboard_external_updated.py"
            },
            "generate_external_makefile.py": {
                "description": "Generator for custom external project Makefiles",
                "size": "~8KB",
                "usage": "python generate_external_makefile.py --api-base <url> --output <filename>"
            }
        },
        "generated": {
            "Makefile.external": {
                "description": "Generated Makefile for external project operations",
                "size": "~2KB",
                "usage": "make -f Makefile.external help"
            },
            "README.external.md": {
                "description": "Documentation for external project usage",
                "size": "~3KB",
                "usage": "cat README.external.md"
            }
        },
        "examples": {
            "example_memory.txt": {
                "description": "Example memory content for testing",
                "size": "~1KB",
                "usage": "make -f Makefile.external memory-create FILE=example_memory.txt"
            },
            "example_rule.mdc": {
                "description": "Example rule file for testing",
                "size": "~1KB", 
                "usage": "make -f Makefile.external rule-propose FILE=example_rule.mdc"
            }
        }
    }
    
    return {
        "title": "AI-IDE-API External Onboarding Files",
        "description": "Available files for external project onboarding",
        "files": files,
        "download_endpoints": {
            "scripts": "/external/onboarding/download/scripts",
            "makefile": "/external/onboarding/download/makefile", 
            "readme": "/external/onboarding/download/readme",
            "examples": "/external/onboarding/download/examples",
            "all": "/external/onboarding/download/all"
        },
        "generator_endpoint": "/external/onboarding/generate"
    }

@router.get("/onboarding/download/{file_type}")
async def download_onboarding_file(
    file_type: str,
    current_user: ApiAccessToken = Depends(require_api_token)
):
    """
    Download onboarding files by type.
    Requires authentication.
    """
    if file_type == "scripts":
        return await _download_scripts_zip()
    elif file_type == "makefile":
        return await _download_makefile()
    elif file_type == "readme":
        return await _download_readme()
    elif file_type == "examples":
        return await _download_examples_zip()
    elif file_type == "all":
        return await _download_complete_package()
    else:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file_type: {file_type}. Use: scripts, makefile, readme, examples, or all"
        )

@router.get("/onboarding/quick-start")
async def get_quick_start_guide() -> Dict[str, Any]:
    """
    Get a quick start guide for external onboarding.
    This endpoint is public and does not require authentication.
    """
    return {
        "title": "AI-IDE-API External Onboarding Quick Start",
        "steps": [
            {
                "step": 1,
                "title": "Download Onboarding Package",
                "description": "Download the complete onboarding package",
                "command": "curl -H 'Authorization: Bearer YOUR_TOKEN' http://localhost:9103/external/onboarding/download/all -o ai-ide-api-onboarding.zip",
                "api_endpoint": "/external/onboarding/download/all"
            },
            {
                "step": 2,
                "title": "Extract Package",
                "description": "Extract the downloaded zip file",
                "command": "unzip ai-ide-api-onboarding.zip",
                "api_endpoint": None
            },
            {
                "step": 3,
                "title": "Run Onboarding",
                "description": "Execute the onboarding script",
                "command": "chmod +x onboard_external.sh && ./onboard_external.sh",
                "api_endpoint": None
            },
            {
                "step": 4,
                "title": "Use the Generated Makefile",
                "description": "Start using the generated Makefile",
                "command": "make -f Makefile.external help",
                "api_endpoint": None
            }
        ],
        "api_endpoints": {
            "list_files": "/external/onboarding/files",
            "download_all": "/external/onboarding/download/all",
            "download_scripts": "/external/onboarding/download/scripts",
            "download_makefile": "/external/onboarding/download/makefile",
            "generate_custom": "/external/onboarding/generate"
        },
        "configuration": {
            "default_api_base": "http://localhost:9103",
            "default_memory_api_base": "http://localhost:9103/memory"
        }
    }

@router.post("/onboarding/generate")
async def generate_custom_makefile(
    api_base: str = "http://localhost:9103",
    output_name: str = "Makefile.external",
    current_user: ApiAccessToken = Depends(require_api_token)
) -> Dict[str, Any]:
    """
    Generate a custom Makefile for external project usage.
    This creates a focused, project-specific Makefile instead of the complex generic one.
    """
    try:
        # Generate the custom Makefile
        makefile_content = generate_makefile(api_base, f"{api_base}/memory", output_name)
        
        # Save the generated Makefile
        makefile_path = os.path.join(GENERATED_DIR, output_name)
        with open(makefile_path, "w") as f:
            f.write(makefile_content)
        
        return {
            "status": "success",
            "message": f"Generated custom Makefile: {output_name}",
            "file_path": makefile_path,
            "api_base": api_base,
            "usage": f"make -f {output_name} help"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate Makefile: {str(e)}"
        )

async def _download_scripts_zip():
    """Download all script files as a zip."""
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for script in ONBOARDING_FILES:
            script_path = os.path.join(SCRIPTS_DIR, script)
            if os.path.exists(script_path):
                zipf.write(script_path, script)
    
    zip_buffer.seek(0)
    
    return StreamingResponse(
        io.BytesIO(zip_buffer.getvalue()),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=ai-ide-api-onboarding-scripts.zip"}
    )

async def _download_makefile():
    """Download the generated Makefile."""
    makefile_path = os.path.join(GENERATED_DIR, "Makefile.external")
    if not os.path.exists(makefile_path):
        raise HTTPException(
            status_code=404,
            detail="Makefile.external not found. Run the onboarding script first or use /external/onboarding/generate to create one."
        )
    
    return FileResponse(
        makefile_path,
        media_type="text/plain",
        filename="Makefile.external"
    )

async def _download_readme():
    """Download the README file."""
    readme_path = os.path.join(GENERATED_DIR, "README.external.md")
    if not os.path.exists(readme_path):
        raise HTTPException(
            status_code=404,
            detail="README.external.md not found. Run the onboarding script first."
        )
    return FileResponse(
        readme_path,
        media_type="text/markdown",
        filename="README.external.md"
    )

async def _download_examples_zip():
    """Download example files as a zip."""
    zip_buffer = io.BytesIO()
    
    example_files = ["example_memory.txt", "example_rule.mdc"]
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for example in example_files:
            example_path = os.path.join(GENERATED_DIR, example)
            if os.path.exists(example_path):
                zipf.write(example_path, example)
    
    zip_buffer.seek(0)
    
    return StreamingResponse(
        io.BytesIO(zip_buffer.getvalue()),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=ai-ide-api-onboarding-examples.zip"}
    )

async def _download_complete_package():
    """Download everything as a complete package."""
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add scripts
        for script in ONBOARDING_FILES:
            script_path = os.path.join(SCRIPTS_DIR, script)
            if os.path.exists(script_path):
                zipf.write(script_path, f"scripts/{script}")
        
        # Add generated files (if they exist)
        generated_files = ["Makefile.external", "README.external.md"]
        for file in generated_files:
            file_path = os.path.join(GENERATED_DIR, file)
            if os.path.exists(file_path):
                zipf.write(file_path, file)
        
        # Add example files (if they exist)
        example_files = ["example_memory.txt", "example_rule.mdc"]
        for example in example_files:
            example_path = os.path.join(GENERATED_DIR, example)
            if os.path.exists(example_path):
                zipf.write(example_path, f"examples/{example}")
        
        # Add setup instructions
        setup_content = """# AI-IDE-API External Onboarding Setup

## Quick Start

1. Extract this zip file
2. Run the onboarding script:
   ```bash
   chmod +x scripts/onboard_external.sh
   ./scripts/onboard_external.sh
   ```

3. Use the generated Makefile:
   ```bash
   make -f Makefile.external help
   ```

## Alternative: Generate Custom Makefile

For a more focused, project-specific Makefile:

```bash
# Generate custom Makefile
curl -X POST "http://localhost:9103/external/onboarding/generate" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{"api_base": "http://localhost:9103", "output_name": "Makefile.custom"}'
```

## Files Included

- `scripts/` - Onboarding scripts
- `Makefile.external` - Generated Makefile with essential operations
- `README.external.md` - Complete documentation
- `examples/` - Example files for testing

## API Endpoints

- List files: GET /external/onboarding/files
- Download package: GET /external/onboarding/download/all
- Generate custom: POST /external/onboarding/generate

## Support

Check README.external.md for detailed usage instructions.
"""
        
        zipf.writestr("SETUP.md", setup_content)
    
    zip_buffer.seek(0)
    
    return StreamingResponse(
        io.BytesIO(zip_buffer.getvalue()),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=ai-ide-api-onboarding-complete.zip"}
    )

