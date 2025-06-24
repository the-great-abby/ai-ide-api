# AI-IDE-API External Onboarding Setup

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
curl -X POST "http://localhost:9103/external/onboarding/generate" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
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
