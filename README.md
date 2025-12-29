# SLA AI Dashboard

## Overview  
The SLA AI Dashboard aggregates SLA and ticketing data, analyzes it using AI, and displays performance insights through an interactive ASP.NET Core dashboard. It combines **Kusto Query Language (KQL)** for data extraction, **AI microservices** for executive summaries and ticket suggestions, and **Power Automate** concepts for workflow automation.  

## Live Demo  
<a href="./SLA_Dashboard.mp4">
  <img src="https://img.shields.io/badge/Download-Demo-blue?style=for-the-badge">
</a>

*(Click the link above to download the demo locally and watch it on your machine)*

## Key Features  
- **AI-Driven Insights:** Integrated OpenAI GPT API to generate contextual SLA summaries and actionable ticket suggestions.  
- **Full-Stack Integration:** ASP.NET Core Razor Pages frontend with C# backend linked to a Python FastAPI AI microservice.  
- **Knowledge Base Support:** Markdown-based KB documents for Retrieval-Augmented Generation (RAG) context.  
- **Data Extraction & Automation:** KQL queries for SLA/ticket data; Power Automate workflows for proactive notifications; Azure DevOps integration for SLA work item tracking.  

## Tech Stack  
- **Languages:** Python, C# (.NET)  
- **AI:** OpenAI GPT API, transformers, RAG  
- **Backend:** FastAPI, ASP.NET Core  
- **Data & Automation:** KQL, Power Automate, Azure DevOps  
- **Version Control:** Git & GitHub
