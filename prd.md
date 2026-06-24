# WhatsApp AI Agent MVP - Product Requirements Document (PRD)

## 1. Project Overview

### Project Name

WhatsApp AI Agent MVP

### Purpose

Build a WhatsApp chatbot that automatically replies to incoming WhatsApp messages using an AI model (Google Gemini Flash).

This project serves as the foundation for a future restaurant-ordering platform. The current phase focuses only on creating a working WhatsApp ↔ AI communication system.

### Goal

Allow a user to send a message to a WhatsApp Business number and receive an AI-generated response automatically.

---

# 2. Scope

## Included in MVP

* WhatsApp Cloud API integration
* Incoming message handling
* AI-generated responses
* Outgoing WhatsApp replies
* FastAPI backend
* Webhook implementation
* Local development using ngrok
* Production-ready architecture foundation

## Excluded from MVP

* Restaurant ordering
* Restaurant dashboards
* Multi-tenancy
* Authentication
* Admin panel
* Payment processing
* Order management
* Conversation memory
* PostgreSQL
* Redis queues

---

# 3. User Story

As a WhatsApp user,

I want to send a message to a WhatsApp Business number,

So that I can receive intelligent AI-generated responses automatically.

---

# 4. Success Criteria

The MVP is considered successful when:

1. User sends a WhatsApp message.
2. Meta sends the message to the FastAPI webhook.
3. FastAPI extracts the message.
4. Gemini generates a response.
5. FastAPI sends the response back through WhatsApp.
6. User receives the AI-generated response.

Expected flow:

```text
User
 ↓
WhatsApp
 ↓
Meta Cloud API
 ↓
FastAPI Webhook
 ↓
Gemini Flash
 ↓
FastAPI
 ↓
Meta Cloud API
 ↓
User
```

---

# 5. Functional Requirements

## FR-1: WhatsApp Cloud API Integration

### Description

Integrate Meta WhatsApp Cloud API for sending and receiving messages.

### Requirements

* Connect to Meta WhatsApp Cloud API
* Use test phone number initially
* Support text messages
* Support outgoing responses

---

## FR-2: Webhook Verification

### Endpoint

```http
GET /webhook
```

### Purpose

Verify webhook ownership with Meta.

### Input

```text
hub.mode
hub.verify_token
hub.challenge
```

### Expected Behavior

If verify token matches:

```text
Return hub.challenge
```

Else:

```text
Return 403 Forbidden
```

---

## FR-3: Receive Incoming Messages

### Endpoint

```http
POST /webhook
```

### Purpose

Receive WhatsApp message events.

### Responsibilities

* Parse incoming payload
* Extract sender information
* Extract message content
* Handle only text messages

### Extracted Data

```json
{
  "phone_number": "+923001234567",
  "message": "Hello"
}
```

---

## FR-4: AI Response Generation

### Provider

Google Gemini Flash

### Input

```text
Hello
```

### Output

```text
Hello! How can I help you today?
```

### Requirements

* Send user message to Gemini
* Receive AI response
* Return plain text response

---

## FR-5: Send WhatsApp Reply

### Purpose

Send AI-generated response back to user.

### Endpoint Used

```http
POST https://graph.facebook.com/v25.0/{PHONE_NUMBER_ID}/messages
```

### Message Format

```json
{
  "messaging_product": "whatsapp",
  "to": "<user_number>",
  "type": "text",
  "text": {
    "body": "<ai_response>"
  }
}
```

---

## FR-6: Error Handling

### AI Failure

If Gemini API fails:

Return:

```text
Sorry, I am unable to respond right now.
Please try again later.
```

### WhatsApp Failure

* Log error
* Prevent application crash

### Invalid Payload

* Ignore unsupported message types
* Return HTTP 200

---

# 6. Non-Functional Requirements

## Performance

Target response time:

```text
< 5 seconds
```

Ideal response time:

```text
< 2 seconds
```

---

## Scalability

Current Target:

```text
100 messages/day
```

Future Target:

```text
10,000+ messages/day
```

Architecture should allow:

* Redis integration
* Queue-based processing
* Horizontal scaling

---

## Reliability

Requirements:

* Webhook must not crash
* FastAPI should handle malformed requests
* All exceptions should be logged

---

# 7. Technical Stack

## Backend

FastAPI

Responsibilities:

* Webhook handling
* AI orchestration
* WhatsApp API integration

---

## AI Provider

Google Gemini Flash

Responsibilities:

* Generate conversational responses

---

## Database

None for MVP

Future:

```text
PostgreSQL
```

---

## Hosting

Development:

```text
Localhost + ngrok
```

Production:

```text
Railway
DigitalOcean
Render
```

---

# 8. API Design

## Health Check

### Endpoint

```http
GET /
```

### Response

```json
{
  "status": "running"
}
```

---

## Webhook Verification

### Endpoint

```http
GET /webhook
```

### Purpose

Meta webhook verification

---

## Message Reception

### Endpoint

```http
POST /webhook
```

### Purpose

Receive WhatsApp messages

---

# 9. Environment Variables

```env
WHATSAPP_ACCESS_TOKEN=

WHATSAPP_PHONE_NUMBER_ID=

WHATSAPP_VERIFY_TOKEN=

GEMINI_API_KEY=
```

---

# 10. Project Structure

```text
app/
│
├── main.py
│
├── routes/
│   └── webhook.py
│
├── services/
│   ├── whatsapp_service.py
│   └── ai_service.py
│
├── config/
│   └── settings.py
│
├── models/
│
└── utils/
```

---

# 11. Implementation Milestones

## Milestone 1

Meta Cloud API Setup

Deliverables:

* Access token generated
* Test phone number configured
* Test message successfully sent

---

## Milestone 2

FastAPI Backend

Deliverables:

* FastAPI server running
* Health endpoint available

---

## Milestone 3

Webhook Verification

Deliverables:

* Meta webhook verification successful

---

## Milestone 4

Incoming Message Processing

Deliverables:

* WhatsApp messages received by FastAPI

---

## Milestone 5

Gemini Integration

Deliverables:

* AI responses generated successfully

---

## Milestone 6

End-to-End Chatbot

Deliverables:

* User sends WhatsApp message
* AI response returned automatically

---

# 12. Future Roadmap

## Phase 2

Conversation Memory

Features:

* Chat history
* Context-aware responses

---

## Phase 3

Restaurant Ordering

Features:

* Menu ingestion
* Order extraction
* Structured JSON orders

---

## Phase 4

Restaurant Dashboard

Features:

* Order management
* Status updates
* Order history

---

## Phase 5

Multi-Tenant SaaS Platform

Features:

* Multiple restaurants
* Tenant isolation
* Role-based access

---

## Phase 6

Production Scaling

Features:

* PostgreSQL
* Redis
* Background workers
* Monitoring
* Analytics
* Queue processing

```
```
