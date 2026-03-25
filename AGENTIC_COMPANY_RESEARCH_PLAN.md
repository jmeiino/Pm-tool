# Research-Plan: Agentic Company — AI-Agent-Microservice

## Vision

Ein eigenständiger Microservice, der als **virtuelle Firma aus KI-Agenten** operiert. Firmenähnliche Struktur mit CEO, Abteilungen und Spezialisten. Empfängt Aufgaben vom PM-Tool, verarbeitet sie autonom (mit Rückfragen) und liefert Ergebnisse zurück.

---

## 1. Zu erforschende Kernfragen

### 1.1 Agent-Architektur
- **Multi-Agent Frameworks:** Vergleich von CrewAI, AutoGen, LangGraph, Swarm (OpenAI), Claude Agent SDK
  - Welches Framework bietet die beste Orchestrierung von Agent-Hierarchien?
  - Unterstützung für Tool-Use, Memory, Delegation zwischen Agents?
  - Wie gut lässt sich eine firmenähnliche Struktur (CEO → Departments → Specialists) abbilden?
- **Agent Communication:** Wie kommunizieren Agents intern?
  - Message Passing vs. Shared State vs. Event-basiert?
  - Wie wird Kontext zwischen Agent-Übergaben (Handoffs) übertragen?
- **Agent Memory:** Kurzzeit vs. Langzeit-Gedächtnis
  - RAG (Retrieval-Augmented Generation) für Firmen-Wissen?
  - Vektorstore (Pinecone, Chroma, Qdrant) für persistentes Wissen?

### 1.2 Multi-Provider AI
- **Routing-Strategie:** Welcher Provider für welchen Agent?
  - Claude Opus für CEO (komplexe Entscheidungen, Planung)
  - Claude Sonnet für Department Heads (Aufgabenzerlegung)
  - GPT-4 für Coding-Specialists
  - Ollama/Lokale Modelle für einfache Tasks (Kosten-Optimierung)
- **Fallback-Ketten:** Was passiert wenn ein Provider ausfällt?
- **Kosten-Management:** Token-Tracking pro Agent, Budget-Limits?

### 1.3 Tool-Integration
- **Code-Ausführung:** Sandbox für Code-Generierung und Tests
  - Docker-basierte Sandboxes? E2B? Modal?
  - Git-Integration: Branches erstellen, PRs öffnen?
- **Design-Tools:** Figma API, generative Design-Tools?
- **Research:** Web-Suche, Dokumenten-Analyse?
- **Content:** Markdown/HTML-Generierung, Bild-Generierung (DALL-E, Midjourney API)?

### 1.4 Organisationsstruktur
- **Statische vs. dynamische Rollen:** Feste Agent-Rollen oder dynamisch generiert je nach Aufgabe?
- **Skalierung:** Können mehrere Instanzen eines Agent-Typs parallel arbeiten?
- **Eskalation:** Wann eskaliert ein Specialist zum Department Head, wann zum CEO?
- **QA-Prozess:** Automatische Tests + AI-basierte Code-Reviews?

---

## 2. Tech-Stack Evaluation

### Framework-Kandidaten:

| Framework | Stärken | Schwächen | Firmen-Struktur |
|-----------|---------|-----------|-----------------|
| **CrewAI** | Einfache Agent-Definition, Role-Based | Limitierte Orchestrierung | Gut (Crews + Tasks) |
| **LangGraph** | Graph-basierter Workflow, Checkpointing | Steile Lernkurve | Mittel (Custom Nodes) |
| **AutoGen** (Microsoft) | Multi-Agent Conversations | Overhead, komplex | Gut (GroupChat) |
| **Claude Agent SDK** | Native Claude-Integration, Tool-Use | Nur Claude | Mittel (Custom) |
| **Swarm** (OpenAI) | Leichtgewichtig, Handoff-Pattern | Experimentell | Gut (Agent Handoffs) |
| **Custom (FastAPI + Redis)** | Volle Kontrolle, kein Vendor Lock-in | Mehr Aufwand | Perfekt (maßgeschneidert) |

### Empfohlene Evaluation:
1. **Prototype A:** LangGraph (Graph-basiert, Checkpointing für lange Tasks)
2. **Prototype B:** Custom FastAPI + Redis (maximale Flexibilität)
3. **Vergleich:** Welcher Ansatz passt besser zur firmenähnlichen Struktur?

### Service-Stack:
- **API:** FastAPI (async, schnell, WebSocket-fähig)
- **Task Queue:** Celery + Redis oder Dramatiq
- **Database:** PostgreSQL (Agent-State, Task-History)
- **Vector Store:** Chroma oder Qdrant (Agent Memory)
- **Container:** Docker (für Code-Sandboxen + Deployment)

---

## 3. Proposed Repo-Struktur

```
agentic-company/
├── README.md
├── docker-compose.yml
├── pyproject.toml
├── .env.example
│
├── app/
│   ├── main.py                    # FastAPI Entry Point
│   ├── config.py                  # Settings, Provider-Config
│   │
│   ├── api/
│   │   ├── routes/
│   │   │   ├── tasks.py           # POST /tasks/, GET /tasks/{id}
│   │   │   ├── agents.py          # GET /agents/, GET /status/
│   │   │   └── webhooks.py        # Callbacks zum PM-Tool
│   │   └── schemas.py             # Pydantic Request/Response Models
│   │
│   ├── agents/
│   │   ├── base.py                # BaseAgent ABC
│   │   ├── ceo.py                 # CEO Agent (Task-Routing, Priorisierung)
│   │   ├── department_head.py     # Department Head (Aufgabenzerlegung)
│   │   ├── specialist.py          # Specialist (Ausführung)
│   │   ├── qa.py                  # QA Agent (Review, Tests)
│   │   └── registry.py            # Agent Registry + Factory
│   │
│   ├── departments/
│   │   ├── engineering/
│   │   │   ├── head.py            # Engineering Lead
│   │   │   ├── frontend_dev.py    # Frontend Specialist
│   │   │   ├── backend_dev.py     # Backend Specialist
│   │   │   └── devops.py          # DevOps Specialist
│   │   ├── design/
│   │   │   ├── head.py            # Design Lead
│   │   │   └── ui_designer.py     # UI/UX Specialist
│   │   ├── content/
│   │   │   ├── head.py            # Content Lead
│   │   │   └── writer.py          # Content Writer
│   │   └── research/
│   │       ├── head.py            # Research Lead
│   │       └── analyst.py         # Research Analyst
│   │
│   ├── orchestration/
│   │   ├── task_router.py         # CEO-Logik: welche Abteilung?
│   │   ├── workflow_engine.py     # Task Lifecycle Management
│   │   ├── handoff.py             # Agent-Übergaben
│   │   └── conflict_resolver.py   # Konflikt-Handling
│   │
│   ├── providers/
│   │   ├── base.py                # AI Provider Interface
│   │   ├── anthropic_provider.py  # Claude (Opus, Sonnet, Haiku)
│   │   ├── openai_provider.py     # GPT-4, GPT-4o
│   │   ├── ollama_provider.py     # Lokale Modelle
│   │   └── router.py              # Provider-Routing (Agent → Provider)
│   │
│   ├── tools/
│   │   ├── code_executor.py       # Sandboxed Code Execution
│   │   ├── git_tools.py           # Git Operations (Branch, PR)
│   │   ├── web_search.py          # Web-Recherche
│   │   ├── file_tools.py          # Dateien lesen/schreiben
│   │   └── design_tools.py        # Design-Generierung
│   │
│   ├── memory/
│   │   ├── short_term.py          # Conversation Context
│   │   ├── long_term.py           # Vector Store (RAG)
│   │   └── company_knowledge.py   # Firmen-Wissen, Best Practices
│   │
│   ├── callbacks/
│   │   ├── pm_tool_callback.py    # Webhook-Sender an PM-Tool
│   │   └── event_emitter.py       # Event-System (intern)
│   │
│   └── models/
│       ├── task.py                # SQLAlchemy: Task, SubTask
│       ├── agent.py               # SQLAlchemy: AgentState, AgentLog
│       └── message.py             # SQLAlchemy: Message, Decision
│
├── tests/
│   ├── test_ceo.py
│   ├── test_routing.py
│   ├── test_handoff.py
│   ├── test_providers.py
│   └── test_api.py
│
└── sandbox/
    └── Dockerfile                 # Isolated Code Execution Container
```

---

## 4. Forschungsschritte (Reihenfolge)

### Phase 1: Framework-Evaluation (1-2 Wochen)
1. LangGraph Prototype: CEO → Department Head → Specialist Pipeline
2. Custom FastAPI Prototype: gleiche Pipeline ohne Framework
3. Vergleich: Flexibilität, Debuggability, Performance

### Phase 2: Multi-Provider Integration (1 Woche)
4. Provider-Router implementieren (Claude, GPT, Ollama)
5. Kosten-Tracking + Fallback-Ketten testen
6. Latenz-Benchmarks pro Provider

### Phase 3: Agent-Kommunikation (1 Woche)
7. Handoff-Protokoll zwischen Agents designen
8. Decision-Flow implementieren (Agent fragt User)
9. PM-Tool Webhook-Integration testen (End-to-End)

### Phase 4: Tool-Use (1-2 Wochen)
10. Code-Sandbox einrichten (Docker-basiert)
11. Git-Integration (Branch erstellen, Dateien schreiben)
12. Web-Search + Document-Analyse
13. Design-Tool-Integration evaluieren

### Phase 5: Memory & Wissen (1 Woche)
14. Vektorstore einrichten (Chroma/Qdrant)
15. RAG-Pipeline für Firmen-Wissen
16. Agent-Langzeitgedächtnis testen

### Phase 6: MVP (2 Wochen)
17. Vollständiger Workflow: PM-Tool → CEO → Department → Specialist → QA → PM-Tool
18. 3 Aufgabentypen funktionsfähig (Software, Content, Research)
19. Echtzeit-Kommunikation mit PM-Tool via Webhooks/SSE
20. Tests + Dokumentation

---

## 5. Offene Design-Entscheidungen

| Entscheidung | Optionen | Empfehlung |
|---|---|---|
| Agent-Framework | LangGraph vs. Custom | Custom (mehr Kontrolle) |
| Datenbank | PostgreSQL vs. MongoDB | PostgreSQL (Konsistenz mit PM-Tool) |
| Task Queue | Celery vs. Dramatiq vs. asyncio | Celery (gleiche Infra wie PM-Tool) |
| Code Sandbox | Docker vs. E2B vs. Modal | Docker (self-hosted, keine Abhängigkeit) |
| Vector Store | Chroma vs. Qdrant vs. Pinecone | Chroma (self-hosted, einfach) |
| Deployment | Docker Compose vs. K8s | Docker Compose (Start), K8s (Skalierung) |

---

## 6. Integration mit PM-Tool (bereits implementiert)

Die PM-Tool-Seite der Integration ist bereits fertig:
- `AgentCompanyConfig` Model für Verbindungskonfiguration
- Webhook-Endpoint mit HMAC-Verifizierung (`/api/v1/agents/webhooks/event/`)
- SSE-Stream für Live-Updates (`/api/v1/agents/tasks/{id}/stream/`)
- REST-API für Task-Delegation, Reply, Cancel
- Frontend: AgentTaskPanel mit Org-Chart + Timeline + Chat
- 22 Backend-Tests für die Integration

**Der Agent-Service muss folgende Endpoints implementieren:**
```
POST /api/v1/tasks/                   # Aufgabe empfangen
POST /api/v1/tasks/{id}/reply/        # User-Antwort empfangen
POST /api/v1/tasks/{id}/cancel/       # Aufgabe abbrechen
GET  /api/v1/agents/                  # Agent-Profile liefern
GET  /api/v1/status/                  # Firmenstatus liefern
```

**Und folgende Events per Webhook senden:**
```
agent.message, task.accepted, task.assigned, task.status_changed,
task.needs_input, task.deliverable, task.completed, task.failed,
agent.status_changed
```
