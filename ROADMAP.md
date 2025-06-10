# Project Roadmap

This roadmap outlines the planned features, improvements, and research directions for the project. It's organized by priority and links to user stories and design docs where available. Please update regularly as priorities shift and features are completed!

---

## Immediate / Small Wins
- **Tag and cluster existing memory nodes**
- **Add "summary" node type and manual summaries** ([AI Knowledge Summarization](docs/user_stories/ai_knowledge_summarization.md))
- **Build simple trace and clustering scripts**
- **Add trace endpoint and basic UI for summaries/traces** ([Explainable Decision Tracing](docs/user_stories/explainable_decision_tracing.md))

---

## Core Feature Prototypes
- **AI Knowledge Summarization (automated, LLM-based)**  
  [User Story & Design](docs/user_stories/ai_knowledge_summarization.md)
- **Explainable Decision Tracing (visual and textual)**  
  [User Story & Design](docs/user_stories/explainable_decision_tracing.md)
- **Collaborative Knowledge Curation (merge/split/edit proposals)**  
  [User Story & Design](docs/user_stories/collaborative_knowledge_curation.md)
- **Personalized Memory Views (filtering, saving, sharing)**  
  [User Story & Design](docs/user_stories/personalized_memory_views.md)

---

## Advanced / Research Features
- **Feedback Quality Scoring**
- **Automated Documentation Generation**
- **Federated Knowledge Sharing**
- **Feedback Loop Analytics**
- **Context-Aware AI Suggestions**

---

## Infrastructure & Best Practices
- **CQRS/Event-Driven Architecture**
  - Separate command (write) and query (read) models for scalability and flexibility.
  - Use RabbitMQ for event-driven workflows (tagging, summarization, analytics, etc.).
  - Phased approach: define event schemas, implement command/query separation, add event-driven workers, optimize read models.
- **CI/CD improvements and deployment guides**
- **Security and permissions enhancements**
- **Contribution guidelines and code review process**

---

## Planned Improvements

- Add feedback endpoints for onboarding and user experience
  - We already invite feedback, but endpoints are not yet set up
  - Consider using or adapting the test feedback endpoint as inspiration

---

## How to Use This Roadmap
- **Contributors:** Pick an item, check the linked user story/design, and open a PR or issue to discuss or implement.
- **Team Leads:** Update priorities, add new features, and mark completed items.
- **Researchers:** Propose experiments or studies based on the roadmap.

---

*See something missing? Please add your ideas, user stories, or research questions!* 