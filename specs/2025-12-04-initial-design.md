# js-interaction-detector Design Specification

## Section 1: Purpose & Scope

**js-interaction-detector** is a Python CLI tool that takes a URL and produces a JSON report of all JavaScript-driven input validations on that page.

**v1 Scope:**
- Input validation detection only (formatting, visibility, data fetching, etc. deferred to v2)
- Publicly accessible pages only (no auth handling)
- Framework-agnostic analysis (works on any page, but doesn't understand framework internals)

**Primary use case:** Feed structured data into a Playwright test generator so it can automatically create tests for client-side validation behavior.

**Core philosophy:** Clarity over completeness. When the tool can't fully understand a validation, it says so explicitly (`"type": "unknown"`) rather than guessing. A tool that's honest about its limitations builds trust.

---

## Section 2: Detection Approach

**Hybrid static/dynamic analysis:**

1. **Load the page** — Use Playwright to load the URL in a headless browser
2. **Wait for ready** — Wait for network idle to ensure dynamic content has loaded
3. **Find candidates** — Query the DOM for all elements with JavaScript event listeners attached
4. **Filter to inputs** — Keep only input-related elements (`<input>`, `<textarea>`, `<select>`, and elements with `contenteditable`)
5. **Extract details** — For each candidate, extract the element info, event triggers, and validation logic
6. **Infer rules** — Apply pattern matching to recognize common validation types (email, phone, required, etc.)

---

## Section 3: Output Format

**Flat JSON array** written to stdout:

```json
{
  "url": "https://example.com/signup",
  "analyzed_at": "2025-12-04T10:30:00Z",
  "errors": [],
  "interactions": [
    {
      "element": {
        "selector": "input#phone",
        "tag": "input",
        "type": "tel",
        "name": "phone",
        "id": "phone",
        "placeholder": "Enter phone number",
        "attributes": {
          "maxlength": "12",
          "pattern": "[0-9]{3}-[0-9]{3}-[0-9]{4}"
        }
      },
      "triggers": ["blur", "input"],
      "validation": {
        "type": "phone",
        "rule_description": "Must be 10 digits in format XXX-XXX-XXXX",
        "confidence": "high",
        "raw_code": "function validatePhone(e) { ... }"
      },
      "error_display": {
        "method": "sibling_element",
        "selector": "span.error-message",
        "sample_message": "Please enter a valid phone number"
      },
      "examples": {
        "valid": ["555-123-4567"],
        "invalid": ["123", "abcdefghij"]
      }
    }
  ]
}
```

**Field notes:**
- `errors`: array of any non-fatal errors encountered during analysis
- `validation.type`: one of the recognized types, or `"unknown"` if inference failed
- `validation.confidence`: `"high"`, `"medium"`, or `"low"` based on pattern match quality
- `validation.raw_code`: always included, even when type is recognized

---

## Section 4: Validation Rule Inference

**Pattern matching** for v1. The tool recognizes these common validation types:

| Type | Detection Pattern |
|------|------------------|
| `required` | Checks for empty/null/undefined, or `required` attribute |
| `email` | Regex containing `@`, common email patterns |
| `phone` | Regex for digit sequences, phone format patterns |
| `numeric` | Checks `isNaN`, digit-only regex |
| `min_length` | `.length >= n` or `minlength` attribute |
| `max_length` | `.length <= n` or `maxlength` attribute |
| `pattern` | Custom regex validation (capture the regex) |
| `url` | URL format regex patterns |
| `date` | Date parsing or date format regex |
| `unknown` | Could not infer rule type |

**Inference process:**
1. Parse the validation function code
2. Look for characteristic patterns (regex literals, length checks, etc.)
3. If a known pattern matches, assign the type and generate `rule_description`
4. If no pattern matches, set `type: "unknown"` and include only `raw_code`

**Confidence levels:**
- `high`: Clear pattern match (e.g., obvious email regex)
- `medium`: Probable match but code has additional complexity
- `low`: Weak signal, might be wrong

---

## Section 5: CLI Interface & Error Handling

**CLI Interface:**

```bash
python -m js_interaction_detector https://example.com/form
```

- Single positional argument: the URL to analyze
- Output: JSON to stdout
- Errors/warnings: to stderr
- Exit codes: 0 on success (even with partial results), non-zero only for fatal errors (can't load page, invalid URL)

**Error handling — partial results strategy:**

The tool returns whatever it successfully extracted. The `errors` array in the JSON documents what went wrong:

```json
{
  "errors": [
    {
      "element": "input#weird-field",
      "error": "Could not extract event listener code",
      "phase": "extraction"
    }
  ],
  "interactions": [...]
}
```

**Error phases:**
- `loading`: Page load failures
- `discovery`: Problems finding elements
- `extraction`: Could not extract listener/validation code for a specific element
- `inference`: Pattern matching failed (not really an error — handled via `type: "unknown"`)

**Logging:** Per project guidelines, functions log their own actions. Progress/debug info goes to stderr when issues occur.

---

## Future Work (v2+)

Deferred to future versions:
- Input formatting detection (auto-format phone, credit card, etc.)
- Dynamic visibility (show/hide based on user action)
- Form submission handlers (AJAX, pre-submit validation)
- Data fetching (autocomplete, search-as-you-type)
- Authentication support (cookies, login flow, browser context)
- LLM-based rule inference for complex validation logic
- Behavioral probing to verify inferred rules
- Framework detection with completeness warnings
