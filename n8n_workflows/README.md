# n8n Workflows for Calvados AI

Included workflows:

- `full_analysis_workflow.json` — upload + 8 agents in phases
- `quick_analysis_workflow.json` — upload + 2 agents + report
- `error_notification_workflow.json` — `Error Trigger` + outbound notification

## Import

Use n8n UI (**Import from File**) or CLI:

```bash
n8n import:workflow --input=n8n_workflows/full_analysis_workflow.json
n8n import:workflow --input=n8n_workflows/quick_analysis_workflow.json
n8n import:workflow --input=n8n_workflows/error_notification_workflow.json
```

## Required env vars in n8n

- `API_BASE_URL` (default expected: `http://localhost:8000`)
- `ERROR_NOTIFY_WEBHOOK` (optional; where to send workflow failures)

## Webhook URLs (changed / standardized)

After import, n8n will expose:

- Full analysis:
  - Test: `POST /webhook-test/calvados/full-analysis`
  - Prod: `POST /webhook/calvados/full-analysis`
- Quick analysis:
  - Test: `POST /webhook-test/calvados/quick-analysis`
  - Prod: `POST /webhook/calvados/quick-analysis`

## Payload format

For both webhooks:

- body: `user_id` (optional; defaults to `n8n-user`)
- binary: file in property `data` (used by upload node with multipart form-data)

## Reliability

All HTTP Request nodes use:

- retries: `3`
- delay: `1000ms`

## Notes

- Backend endpoints used:
  - `POST /api/upload` (multipart: `file`, `user_id`)
  - `POST /agent/{text-analysis|requirement-analysis|structure|compliance|scoring|recommendation|generation|report}`
