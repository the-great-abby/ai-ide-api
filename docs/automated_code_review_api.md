# Automated Code Review API (External Usage)

## Overview
Our API provides AI-powered code review for your Python (and other supported) files. Submit your code and receive actionable feedback and suggestions to improve code quality and follow best practices.

---

## How to Use

### Submit Files for Static Review

Send one or more files to the API and receive feedback for each file (static checks only):

```bash
curl -X POST http://localhost:9103/review-code-files \
  -F "files=@yourfile.py" \
  -F "files=@anotherfile.py"
```

- You can submit multiple files by repeating the `-F "files=@..."` flag.
- The response will be a JSON object with file names as keys and static feedback as values.

### Submit Files for LLM-Powered Review

Send one or more files to the API and receive LLM-generated, context-aware feedback for each file:

```bash
curl -X POST http://localhost:9103/review-code-files-llm \
  -F "files=@yourfile.py" \
  -F "files=@anotherfile.py"
```

- This endpoint uses an AI language model for deeper, context-aware review.
- The response will be a JSON object with file names as keys and LLM feedback as values.

### Submit a Code Snippet (Static Review)

Send a code snippet directly in the request body:

```bash
curl -X POST http://localhost:9103/review-code-snippet \
  -H "Content-Type: application/json" \
  -d '{"filename": "example.py", "code": "def foo(): return 42"}'
```

- The response will be a JSON array of static feedback suggestions for the snippet.

---

## Response Format

- **/review-code-files**: Returns a JSON object where each key is a filename and each value is the static feedback for that file.
- **/review-code-files-llm**: Returns a JSON object where each key is a filename and each value is the LLM-generated feedback for that file.
- **/review-code-snippet**: Returns a JSON array of static feedback suggestions for the submitted code snippet.

---

## Notes

- **Authentication:** No authentication required (for now).
- **File Size Limit:** 1MB per file.
- **Supported Languages:** Python (others coming soon).
- **Feedback:** All feedback is AI-generated. Please review suggestions before applying them to your codebase.
- **Privacy:** Submitted code is processed for review and not stored long-term.
- **LLM Review:** The `/review-code-files-llm` endpoint may take longer to respond than static review, as it uses a large language model for deeper analysis.

---

## Support

For questions, issues, or feature requests, contact: [your-email@example.com]

---

## Example Use Cases

- Open source contributors seeking a quick code review before submitting a pull request.
- Developers wanting a second opinion on code quality or best practices.
- Teams integrating automated code review into their CI/CD pipeline.

---

## Changelog
- 2024-06: Initial public documentation for external API users. 