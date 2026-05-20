# HYMIND n8n Workflow

## Overview

The n8n workflow (`n8n/HYMIND.json`) automates weekly report generation and delivery. It triggers the HYMIND Python agent via HTTP, converts the Markdown output to HTML, and delivers it via Gmail. Delivery outcomes are logged to Google Sheets.

A companion error handler workflow (`n8n/Global Error Handler.json`) catches unhandled workflow errors and sends an alert email.

---

## Workflow Nodes

| Node | Type | Purpose |
|---|---|---|
| Schedule Trigger | Schedule | Fires every Monday at 08:00 |
| Edit Fields | Set | Prepares the research topic and run metadata |
| HTTP Request | HTTP | `POST /run-hymind` to the HYMIND FastAPI server via ngrok |
| IF | Conditional | Routes on `$json.status == "success"` |
| Markdown | Markdown | Converts `$json.report_content` from Markdown to HTML |
| Send HYMIND report | Gmail | Sends the HTML report to the configured recipient |
| Edit Fields - sent logging | Set | Builds the logging payload |
| Append row in sheet | Google Sheets | Logs timestamp, report title, status, delivery channel |
| Edit Fields - error | Set | Builds the error payload on the failure branch |
| Send a message - error | Gmail | Sends an error alert email on failure |

---

## Workflow Flow

```
Schedule Trigger (Monday 08:00)
  ↓
Edit Fields (set topic, report_type, run_mode)
  ↓
HTTP Request → POST https://YOUR-NGROK-URL/run-hymind
  ↓
IF $json.status == "success"
  ├── TRUE →  Markdown (→ HTML)
  │             ↓
  │           Send HYMIND report (Gmail)
  │             ↓
  │           Edit Fields - sent logging
  │             ↓
  │           Append row in sheet (Google Sheets)
  │
  └── FALSE → Edit Fields - error
                ↓
              Send a message - error (Gmail)
              [Global Error Handler workflow linked via errorWorkflow setting]
```

---

## Setup After Importing the Workflow

### 1. Update the ngrok URL

The exported workflow contains a placeholder ngrok URL. After importing:

1. Open the **HTTP Request** node
2. Update the URL to your own ngrok URL: `https://YOUR-NGROK-URL.ngrok-free.app/run-hymind`

If you have a fixed ngrok domain (available on ngrok free with an account):

```powershell
ngrok http --domain=your-fixed-domain.ngrok-free.app 8000
```

The `start_hymind_api.py` script starts both FastAPI and ngrok and prints the active endpoint.

### 2. Reconfigure credentials

The workflow references these credentials (by name) which must be recreated in your n8n instance:

| Credential | Used by | What it needs |
|---|---|---|
| `Header Auth account` | HTTP Request node | Name: `x-api-key`, Value: your `HYMIND_API_KEY` (leave empty if auth is disabled) |
| `Gmail account` | Both Gmail nodes | Google OAuth2 — authenticate with the sending Gmail account |
| `Google Sheets account` | Google Sheets node | Google OAuth2 — same or different account with Sheets access |

### 3. Update the Google Sheets reference

The Google Sheets node writes to a specific spreadsheet. After importing:

1. Open the **Append row in sheet** node
2. Select your own Google Spreadsheet and sheet tab
3. Map the columns: `date`, `public repos` (report title), `user` (status), `followers` (delivery channel)
   - Note: the column names in the sheet can be renamed to match your own spreadsheet schema

### 4. Update email recipients

Both Gmail nodes send to a hardcoded email address. Update them to your own recipient addresses.

---

## API Request Body

The HTTP Request node sends:

```json
{
  "topic": "weekly hydrogen and fuel cell market intelligence",
  "report_type": "weekly_executive",
  "run_mode": "scheduled"
}
```

Change `topic` to customize what the agent researches on each scheduled run.

---

## PDF vs HTML Delivery

The workflow uses n8n's built-in **Markdown** node to convert the report content from Markdown to HTML before sending via Gmail. This produces a formatted, email-readable report without any additional tooling or external dependencies.

**PDF generation was descoped from the MVP.** If PDF delivery is required in a future phase, it can be added by:
- Adding a **Code** node that calls a PDF generation library
- Or routing to a dedicated PDF service (e.g., Gotenberg, WeasyPrint API)

---

## Error Handling

- The HTTP Request node retries twice with a 5-second wait on failure
- The IF node routes failures to the error Gmail node
- The `errorWorkflow` setting in the workflow config references the Global Error Handler workflow by ID
- The Global Error Handler (`n8n/Global Error Handler.json`) is a separate workflow that catches unhandled errors

---

## Timing

A full HYMIND pipeline run takes approximately 2–5 minutes depending on:
- API response times from Serper, NewsAPI, RSS feeds
- Web crawl success rate
- OpenAI synthesis time

The n8n HTTP Request node default timeout is 300 seconds. If runs exceed this, increase the timeout in:
**n8n Settings → Workflow Settings → HTTP Request Timeout**

---

## Testing the Workflow Manually

1. Start the HYMIND API server:
   ```powershell
   python start_hymind_api.py
   ```
2. In n8n, open the HYMIND workflow and click **Test workflow**
3. Check the IF node output to confirm `status == success`
4. Check Gmail for the delivered report
5. Check Google Sheets for the delivery log entry
