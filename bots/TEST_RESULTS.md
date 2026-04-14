# Telegram Bot / Backend Flow Test Results

## Health endpoint

- `GET /health` returns `200` with status `ok`.

## End-to-end flow smoke test

Executed:

```bash
API_BASE_URL=http://127.0.0.1:8000 /Users/eliasansariy/calvados-science-assistance-slave/venv/bin/python bots/test_backend_flow.py
```

Result:

```json
{
  "upload": {
    "file_id": "4cd04aa3-229c-4982-b0d7-38286bbe29e7",
    "filename": "sample_tz.txt",
    "uploaded_at": "2026-04-14T19:39:19.385804+00:00",
    "warning": null,
    "text_length": 120
  },
  "last_agent": "report",
  "report_status": 200,
  "report_size": 11839
}
```

This confirms:

1. upload works with `file + user_id`
2. all agent endpoints are callable in sequence
3. report generation + report download works
