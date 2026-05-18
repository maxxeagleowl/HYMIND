Project 3 Brief Project

Project Overview
Project Name: Autonomous Company Research & Report Generation Agent Duration: 5 days, self-paced Type: Individual Module: Module 3 (Integrates skills from RAG, LangChain, LangGraph, and N8N)

Description
Welcome to your third main project! You'll build an autonomous AI agent. This project challenges you to integrate advanced AI concepts into a system that can operate independently.

Unlike simple chatbots or basic automation, your agent must demonstrate that it can:

Search the web or gather information from multiple sources
Synthesize complex information
Produce structured reports in the format that best fits your use case
The agent must handle the full workflow from research initiation to final report delivery.

This project integrates concepts from Module 3: RAG and retrieval patterns, LangChain or LangGraph for agent orchestration, n8n for workflow automation, tool/API integration, and context engineering for reliable outputs.

Learning Objectives
By the end of this project, students will be able to:

Find an AI use case: Define a realistic research/reporting workflow where an autonomous agent creates value
Design & implement agentic systems: Build an agent-based system using LangChain, LangGraph, n8n, or a justified combination of tools
Generate structured reports from unstructured data synthesis: Transform raw research data into comprehensive, well-structured written reports
Plan and structure an AI project: Scope requirements, choose appropriate tools, and justify design decisions
Project Requirements
Your project must:

Implement an agent-based system: Use LangChain, LangGraph, n8n, or another justified agent/workflow approach, and explain why your choice fits the use case
Integrate a minimum of two real API tools: These can be MCP tools, direct API integrations, n8n nodes, or custom tools you write yourself
Generate comprehensive reports: Produce well-structured written reports that synthesize findings in a format appropriate to the use case
Handle errors gracefully: Implement error handling, retry logic, and validation for tool calls and API interactions so the system is reliable in real-world conditions
Plan the work with Agile methods: Organize the project into user stories, sprint tasks, estimates, dependencies, and definitions of done
Document agent instructions and skills: Include the project specification written for the agent, every AGENTS.md file you create, and all project skills under skills/
Technical Stack
Required Tools
Backend or workflow runtime: Python 3.8+, n8n, or a justified combination
Agent/workflow framework: LangChain, LangGraph, n8n, or another appropriate framework
Tool/API integration: At least two real tools or APIs
LLM: OpenAI, Anthropic, or similar provider
Version Control: Git/GitHub
Agile planning documentation: docs/planning/stories.md at minimum, or linked GitHub Issues, Asana, or Jira board
Optional Tools
Vector database or retrieval layer: Pinecone, Chroma, FAISS, or another option if your use case benefits from RAG
MCP: Recommended when it helps standardize reusable tool integrations, but not required for every project
Project Scope and Constraints
To ensure focus on core objectives:

Industry selection: Choose ONE industry
Time constraints: Must be completed within 5 days
Resource limitations: Use free-tier APIs where possible, or clearly document API costs
Scope boundaries:
Minimum viable product (MVP) should autonomously research a company and generate a basic report
Advanced features (multi-company comparison, real-time monitoring, etc.) are optional enhancements
Autonomy requirement: The agent must operate without human intervention once triggered, human-in-the-loop is allowed
Planning requirement: Each task must include an estimate, dependencies, and a definition of done
Industry Selection (Suggestion)
In case you don't know which industry to choose, you can follow this path.

Choose ONE industry to focus your agent on:

Option 1: Market Research & Competitive Intelligence
Focus: Competitive analysis, market trends, company positioning

Example Research Tasks:

Analyze competitor strategies and positioning
Research market trends and opportunities
Compare company performance metrics
Identify competitive advantages and threats
Useful APIs: Financial data APIs (Alpha Vantage, Yahoo Finance), news APIs (NewsAPI), web search APIs

Option 2: Advertising & Marketing Analytics
Focus: Campaign performance, audience insights, marketing effectiveness

Example Research Tasks:

Analyze marketing campaign performance
Research audience demographics and behavior
Compare advertising strategies across competitors
Evaluate brand positioning and messaging
Useful APIs: Social media APIs (Twitter, LinkedIn), analytics APIs (Google Analytics), advertising APIs (Facebook Ads)

Option 3: Media, Journalism & Publishing
Focus: News analysis, content trends, media landscape

Example Research Tasks:

Research news coverage and media sentiment
Analyze content trends and topics
Compare media outlets and their coverage
Track story development and narratives
Useful APIs: News APIs (NewsAPI, Guardian API), content APIs (Reddit, Twitter), web scraping tools

Necessary Deliverables
Students must submit:

GitHub repository with organized, documented code

Clear README with setup instructions
Requirements.txt with all dependencies
Proper project structure following recommended layout
Commit history showing development progress
Architecture diagrams and workflow documentation
docs/planning/stories.md or links to GitHub Issues, Asana, or Jira showing user stories, sprint tasks, estimates, dependencies, and definitions of done
skills/ directory containing the skills used or created for the project
Project specification written for the agent and every AGENTS.md file created during development
Working autonomous agent (Python code, n8n workflow, or justified hybrid)

Agent/workflow implementation with a clear trigger and end-to-end flow
Minimum 2 real tool/API integrations
Complete workflow that researches, synthesizes, and generates a report
Error handling, retry logic, and validation for tool/API calls
Documentation of workflow logic and architecture decisions
Optional, if useful for your solution: ReAct pattern, LangGraph workflow, RAG system, MCP tools, webhook configuration, monitoring
Generated report examples (minimum 2-3)

Sample reports generated by the agent
Different companies or research topics
Demonstrates report quality and structure
Demo video or live presentation (5-7 minutes)

Demonstrate autonomous operation
Show complete workflow from trigger to report
Highlight key features and architecture
Explain design decisions and challenges
Documentation

Architecture overview
Workflow diagrams
API integration details
Tool descriptions and usage
Setup and deployment instructions
Agile planning artifacts with task estimates, dependencies, and definitions of done
Agent-facing project specification, agent instruction files, and skills documentation
Suggested Ways to Get Started
Choose your industry and define scope:

Select one industry from the three options
Research what information would be valuable for that industry
Identify at least 2 APIs or tools you'll need (web search, data analysis, document processing, etc.)
Define what a "comprehensive report" means for your industry
Write user stories and sprint tasks in
docs/planning/stories.md
, GitHub Issues, Asana, or Jira
Add estimates, dependencies, and a definition of done for each task
Set up your environment:

Create virtual environment:
python -m venv venv
Install only the dependencies your architecture needs, for example:
pip install langchain langchain-openai langgraph fastapi python-dotenv
Set up
.env
file for API keys (never commit this!)
Create accounts and keys for your chosen tools/APIs
Build the research foundation (Day 2):

Connect your first source or API
Decide whether your use case needs RAG, live search, database queries, or another retrieval pattern
If using RAG, set up a vector store and test document search
Validate that your system can collect useful research data
Build the agent workflow (Day 3):

Map out your workflow: Research → Analysis → Synthesis → Report Generation
Choose your implementation approach: LangChain, LangGraph, n8n, or hybrid
Write the project specification that you will give to the agent
Save any agent instructions, including
AGENTS.md
files, in your repository
Add one tool at a time, starting with the most important source
Test reasoning/action loops or workflow transitions
Add error handling
Integrate the second real tool/API (Day 3-4):

Add your second required tool/API integration
Validate inputs and outputs for each integration
Add retry or fallback behavior for fragile calls
Test each tool independently before combining them
Prepare orchestration and runtime (Day 4):

Create the script, workflow, or service that runs the agent end to end
Configure it to accept inputs such as company, topic, industry, or research question
Output results in a structured format
If using n8n, create a trigger and connect the workflow steps
Test and refine (Day 4-5):

Run end-to-end tests
Generate multiple reports
Fix bugs and edge cases
Confirm that each completed task meets its definition of done
Save all project skills under
skills/
Document everything
Useful Resources
LangChain Documentation - Complete guide to LangChain framework
LangGraph Documentation - LangGraph workflow building guide
Pinecone Documentation - Vector database setup and usage if your solution uses RAG
N8N Documentation - Workflow automation platform
MCP Framework - Model Context Protocol for tool integration
ReAct Paper - ReAct: Synergizing Reasoning and Acting in Language Models
N8N Execute Command Node - Running Python scripts in N8N
N8N Custom Nodes - Creating custom N8N nodes
OpenAI API Documentation - LLM API integration
Anthropic API Documentation - Claude API integration
Project Evaluation Criteria
Requirements Completion (25%)
Meets all specified technical requirements
Implements an agent-based system using a justified architecture
Integrates at least 2 real tools/APIs
Generates comprehensive reports autonomously
Includes error handling, retry logic, and validation for tool/API calls
Includes Agile planning artifacts, task estimates, dependencies, and definitions of done
Agent Architecture & Implementation (30%)
Agent workflow is well-designed from trigger to final report
Framework choices are justified and appropriate to the use case
Tool calls, context management, and report synthesis are integrated coherently
State, routing, prompts, or workflow steps are clear and maintainable
Agent operates autonomously after the initial trigger, with human-in-the-loop only where intentionally designed
Quality & Execution (25%)
Code, workflow, or hybrid implementation is organized and maintainable
Tool/API integrations are reliable, validated, and documented
Reports are accurate, useful, and appropriately structured for the chosen use case
Proper version control with meaningful commits
Optional advanced components, such as RAG, MCP, LangGraph, or n8n, are implemented effectively when used
Documentation & Presentation (20%)
Clear README with setup instructions
Well-documented code with comments
Architecture diagrams and workflow documentation
User stories, sprint plan, estimates, dependencies, and definitions of done are included
Agent-facing specification, AGENTS.md files, and project skills under skills/ are included
Effective demonstration of working system
Clear explanation of design decisions
Professional presentation quality
Scoring Scale
Score	Expectations
0	Does not meet expectations
1	Meets expectations
2	Exceeds expectations
Getting Help
Instructor Support: Reach out during office hours or scheduled check-ins
Peer Collaboration: Discuss approaches with classmates (but code independently)
Documentation First: Always check official API documentation before asking for help
Debugging Tips: Use print statements, logging, and test each component separately
Incremental Development: Build and test one component at a time (first tool/API → agent workflow → second tool/API → report generation → reliability)
Good luck building your autonomous research agent! Remember: the goal is to create a system that can operate independently, make intelligent decisions, and produce valuable insights. 🚀 
