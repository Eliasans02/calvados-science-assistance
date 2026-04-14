# n8n Workflow Test Results

## Backend availability

- `GET http://127.0.0.1:8000/health` → `200 OK`

## Workflow files validation

- `full_analysis_workflow.json` parsed (`20` nodes, `19` connection groups)
- `quick_analysis_workflow.json` parsed (`9` nodes, `8` connection groups)
- `error_notification_workflow.json` parsed (`3` nodes, `2` connection groups)

## Import/execution status in this environment

Attempted to run n8n via `npx n8n --version`, but package install failed with npm registry timeout:

- `npm ERR! code EIDLETIMEOUT`
- `Idle timeout reached for host registry.npmjs.org:443`

Docker-based fallback for n8n import was also unavailable because Docker daemon was not running:

- `Cannot connect to the Docker daemon at unix:///Users/eliasansariy/.docker/run/docker.sock`

## Retry/error handling implementation

All HTTP Request nodes in workflows include:

- `retryOnFail: true`
- `maxTries: 3`
- `waitBetweenTries: 1000`

Error notifications are implemented in `error_notification_workflow.json` via:

- `Error Trigger` -> `Build Notification` -> `Send Notification`

## Webhook URL updates required

- Full analysis:
  - `/webhook-test/calvados/full-analysis`
  - `/webhook/calvados/full-analysis`
- Quick analysis:
  - `/webhook-test/calvados/quick-analysis`
  - `/webhook/calvados/quick-analysis`
