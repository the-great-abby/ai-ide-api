--
-- PostgreSQL database dump
--

-- Dumped from database version 15.12 (Debian 15.12-1.pgdg120+1)
-- Dumped by pg_dump version 15.12 (Debian 15.12-1.pgdg120+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.alembic_version (version_num) FROM stdin;
cd49c47dfc87
dc83b8ed7bef
\.


--
-- Data for Name: bug_reports; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.bug_reports (id, description, reporter, page, "timestamp") FROM stdin;
\.


--
-- Data for Name: enhancements; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.enhancements (id, description, suggested_by, page, tags, categories, "timestamp", proposal_id, status, project, examples, applies_to) FROM stdin;
403181e3-40cb-4fa1-a59a-85e54de27945	Add a project field to rule and enhancement submissions to allow tracking which rules/enhancements are project-specific versus global. This enables better filtering, assignment, and management of rules across multiple projects.	$(git config user.name)	API design	feature,project-field,multi-project	api,rules,enhancements	2025-05-12 20:09:02.497982	\N	completed	\N	\N	
6ceefb3b-9c02-4489-a4b5-ca91fafb6b43	Maintain an up-to-date knowledge graph for the repository in Markdown/Mermaid format for AI and user review. To improve discoverability, onboarding, and collaboration for both AI and human contributors, all AI-IDE projects should: Maintain a knowledge graph in Markdown/Mermaid format. Keep the graph up to date as rules, workflows, and project structure evolve. Use the knowledge graph to assist both AI agents and human users in navigating and understanding the repository. Reference the knowledge graph in onboarding and documentation materials.	\N	\N			2025-05-12 19:53:16.352595	\N	completed	\N	\N	
0d4829e7-7b92-4ab3-b2b0-79ab68ba6329	Allow rules to be tagged with multiple categories for better filtering.	ai-ide	/rules	filtering,categories	usability,search	2025-05-13 11:56:54.358889	\N	accepted	ai-ide-api	[{"before": "GET /rules?category=automation returns only rules in the automation category.", "after": "GET /rules?category=automation,search returns rules in both automation and search categories."}, {"ui": "In the admin UI, allow selecting multiple categories when filtering rules."}]	
6b78a47e-e5be-4ac3-99a6-4eb20b663f73	Allow rules to be tagged with multiple categories for better filtering.	ai-ide	/rules	filtering,categories	usability,search	2025-05-13 11:54:08.528502	\N	rejected	ai-ide-api	\N	
\.


--
-- Data for Name: feedback; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.feedback (id, rule_id, project, feedback_type, comment, submitted_by, "timestamp") FROM stdin;
\.


--
-- Data for Name: proposals; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.proposals (id, rule_type, description, diff, status, submitted_by, project, "timestamp", version, categories, tags, rule_id, examples, applies_to) FROM stdin;
510aede7-b47b-42a4-94ce-13a3914ce6c4	automation	Projects must provide a script and Makefile.ai target to fetch and sync rules from the central rule server, saving them to .cursor/rules/.	All AI-IDE projects must automate the process of fetching and syncing rules from the central rule server. This ensures all agents and contributors are always up to date with the latest approved rules. The automation should:\n- Use a script (e.g., fetch_remote_rules.py) to fetch rules from the API.\n- Save the rules to .cursor/rules/ in the correct .mdc format.\n- Provide a Makefile.ai target (e.g., ai-fetch-remote-rules) to run the sync process.\n- Ensure the process is idempotent and easy to run for both humans and agents.	approved	\N	\N	2025-05-12 19:53:04.723499	1			\N	\N	
60ad6ecd-15f7-4b4b-8fcf-b3f63f20781a	workflow	All new rules must be proposed as .mdc files, reviewed, and approved via the central rule server before being used in automation.	To ensure quality and prevent conflicts, all new rules must:\n- Be proposed as .mdc files in the .cursor/rules/proposals/ directory.\n- Undergo review and approval via the central rule server or admin UI before being used in automation or workflows.\n- Be clearly documented with description and globs frontmatter.\n- Be tracked for status (proposed, approved, rejected) in the rule management system.	approved	\N	\N	2025-05-12 19:53:10.480315	1			\N	\N	
ab091fc8-e8f9-47bd-9104-225570f49797	process	Definition of Done (DoD) for all rules, enhancements, and features.	A task is considered done when: 1) Code is implemented and linted, 2) All tests pass, 3) Documentation is updated, 4) Rules/workflows are updated if needed, 5) Code is reviewed and approved, 6) Deployed to the appropriate environment, 7) No open critical bugs, 8) Changelog is updated if required.	approved	$(git config user.name)	\N	2025-05-12 21:14:10.354995	1			\N	\N	
25352d22-49fd-4218-985a-9b759ee37933	automation	Projects must provide a script and Makefile.ai target to fetch and sync rules from the central rule server, saving them to .cursor/rules/.	All AI-IDE projects must automate the process of fetching and syncing rules from the central rule server. This ensures all agents and contributors are always up to date with the latest approved rules. The automation should:\n- Use a script (e.g., fetch_remote_rules.py) to fetch rules from the API.\n- Save the rules to .cursor/rules/ in the correct .mdc format.\n- Provide a Makefile.ai target (e.g., ai-fetch-remote-rules) to run the sync process.\n- Ensure the process is idempotent and easy to run for both humans and agents.	approved	ai-ide	ai-ide-api	2025-05-13 11:48:20.173775	1	automation,sync	fetch,rules,Makefile.ai	510aede7-b47b-42a4-94ce-13a3914ce6c4	- description: Sync rules from the central server\n  command: make -f Makefile.ai ai-fetch-remote-rules\n- description: Fetch rules using a script\n  command: python scripts/fetch_remote_rules.py	
6f6d5646-e5d7-4799-8bfe-763d807dea16	automation	Projects must provide a script and Makefile.ai target to fetch and sync rules from the central rule server, saving them to .cursor/rules/.	All AI-IDE projects must automate the process of fetching and syncing rules from the central rule server. This ensures all agents and contributors are always up to date with the latest approved rules. The automation should:\n- Use a script (e.g., fetch_remote_rules.py) to fetch rules from the API.\n- Save the rules to .cursor/rules/ in the correct .mdc format.\n- Provide a Makefile.ai target (e.g., ai-fetch-remote-rules) to run the sync process.\n- Ensure the process is idempotent and easy to run for both humans and agents.	rejected	ai-ide	ai-ide-api	2025-05-13 11:48:29.324601	1	automation,sync	fetch,rules,Makefile.ai	510aede7-b47b-42a4-94ce-13a3914ce6c4	[{"description": "Sync rules from the central server", "command": "make -f Makefile.ai ai-fetch-remote-rules"}, {"description": "Fetch rules using a script", "command": "python scripts/fetch_remote_rules.py"}]	
af0f3fa5-9d7c-4a5a-bfab-f3fc2cf4c00c	automation	Projects must provide a script and Makefile.ai target to fetch and sync rules from the central rule server, saving them to .cursor/rules/.	All AI-IDE projects must automate the process of fetching and syncing rules from the central rule server. This ensures all agents and contributors are always up to date with the latest approved rules. The automation should:\n- Use a script (e.g., fetch_remote_rules.py) to fetch rules from the API.\n- Save the rules to .cursor/rules/ in the correct .mdc format.\n- Provide a Makefile.ai target (e.g., ai-fetch-remote-rules) to run the sync process.\n- Ensure the process is idempotent and easy to run for both humans and agents.	rejected	ai-ide	ai-ide-api	2025-05-13 11:53:25.892876	1	automation,sync	fetch,rules,Makefile.ai	510aede7-b47b-42a4-94ce-13a3914ce6c4	[{"description": "Sync rules from the central server", "command": "make -f Makefile.ai ai-fetch-remote-rules"}, {"description": "Fetch rules using a script", "command": "python scripts/fetch_remote_rules.py"}]	
\.


--
-- Data for Name: rule_versions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.rule_versions (id, rule_id, version, rule_type, description, diff, status, submitted_by, added_by, project, "timestamp", categories, tags, examples, applies_to) FROM stdin;
d7dd9bc3-84c2-4dac-ab96-bf1cc664b91c	510aede7-b47b-42a4-94ce-13a3914ce6c4	1	automation	Projects must provide a script and Makefile.ai target to fetch and sync rules from the central rule server, saving them to .cursor/rules/.	All AI-IDE projects must automate the process of fetching and syncing rules from the central rule server. This ensures all agents and contributors are always up to date with the latest approved rules. The automation should:\n- Use a script (e.g., fetch_remote_rules.py) to fetch rules from the API.\n- Save the rules to .cursor/rules/ in the correct .mdc format.\n- Provide a Makefile.ai target (e.g., ai-fetch-remote-rules) to run the sync process.\n- Ensure the process is idempotent and easy to run for both humans and agents.	approved	\N	\N	\N	2025-05-12 19:53:04.723499			\N	
\.


--
-- Data for Name: rules; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.rules (id, rule_type, description, diff, status, submitted_by, added_by, project, "timestamp", version, categories, tags, examples, applies_to) FROM stdin;
60ad6ecd-15f7-4b4b-8fcf-b3f63f20781a	workflow	All new rules must be proposed as .mdc files, reviewed, and approved via the central rule server before being used in automation.	To ensure quality and prevent conflicts, all new rules must:\n- Be proposed as .mdc files in the .cursor/rules/proposals/ directory.\n- Undergo review and approval via the central rule server or admin UI before being used in automation or workflows.\n- Be clearly documented with description and globs frontmatter.\n- Be tracked for status (proposed, approved, rejected) in the rule management system.	approved	\N	\N	\N	2025-05-12 19:53:10.480315	1			\N	
ab091fc8-e8f9-47bd-9104-225570f49797	process	Definition of Done (DoD) for all rules, enhancements, and features.	A task is considered done when: 1) Code is implemented and linted, 2) All tests pass, 3) Documentation is updated, 4) Rules/workflows are updated if needed, 5) Code is reviewed and approved, 6) Deployed to the appropriate environment, 7) No open critical bugs, 8) Changelog is updated if required.	approved	$(git config user.name)	$(git config user.name)	\N	2025-05-12 21:14:10.354995	1			\N	
510aede7-b47b-42a4-94ce-13a3914ce6c4	automation	Projects must provide a script and Makefile.ai target to fetch and sync rules from the central rule server, saving them to .cursor/rules/.	All AI-IDE projects must automate the process of fetching and syncing rules from the central rule server. This ensures all agents and contributors are always up to date with the latest approved rules. The automation should:\n- Use a script (e.g., fetch_remote_rules.py) to fetch rules from the API.\n- Save the rules to .cursor/rules/ in the correct .mdc format.\n- Provide a Makefile.ai target (e.g., ai-fetch-remote-rules) to run the sync process.\n- Ensure the process is idempotent and easy to run for both humans and agents.	approved	ai-ide	ai-ide	ai-ide-api	2025-05-13 11:48:20.173775	2	automation,sync	fetch,rules,Makefile.ai	- description: Sync rules from the central server\n  command: make -f Makefile.ai ai-fetch-remote-rules\n- description: Fetch rules using a script\n  command: python scripts/fetch_remote_rules.py	
\.


--
-- PostgreSQL database dump complete
--

