# Product Requirements Document: CivicAI Multi-Agent Debate System

## Introduction/Overview

CivicAI is an AI-powered civic engagement platform that helps citizens understand policy trade-offs through adversarial multi-agent debates. The system uses specialized agents representing different stakeholder perspectives to help users form well-rounded opinions and take effective civic action.

**Problem Statement**: Civic engagement is fundamentally broken because citizens lack the tools to navigate the adversarial nature of policy-making. While access to information is a known issue, the more critical barrier is that policies are presented as dense, one-sided documents. This leaves people unable to grasp the inherent trade-offs, understand opposing viewpoints, or form a well-rounded opinion, ultimately preventing them from advocating for their interests effectively.

**Goal**: Build a dynamic multi-agent AI system that can instantiate any stakeholder perspectives relevant to a policy issue, helping citizens understand complex trade-offs and advocate effectively for their interests.

## Goals

1. **Dynamic Agent Instantiation**: Create an orchestration system that can spawn stakeholder agents for any policy domain
2. **Multi-Stakeholder Debates**: Enable complex debates between 2-4 stakeholder perspectives simultaneously
3. **Generic Trade-off Analysis**: Identify tensions and compromises across any policy domain (housing, labor, public safety, etc.)
4. **Contextual Personalization**: Connect abstract policies to users' concrete roles and situations
5. **Universal Civic Framework**: Demonstrate scalable architecture that works for any civic issue

## User Stories

### Primary User Stories
- **As a San Francisco renter**, I want to understand how new rent control policies affect both my interests and my landlord's so that I can advocate for balanced solutions
- **As a gig worker**, I want to see how labor classification policies impact both workers and platform companies so that I can understand the full complexity
- **As a small business owner**, I want to understand minimum wage debates from both employer and employee perspectives before commenting to city council
- **As a community member**, I want to see how public safety policies affect residents, police, and city budget simultaneously
- **As a civic participant**, I want to input my role/situation and get personalized multi-stakeholder policy analysis

### Secondary User Stories
- **As a parent**, I want to understand school policy debates from teacher, administrator, and family perspectives
- **As an environmentalist**, I want to see climate policies debated between environmental, business, and labor stakeholders
- **As a policy advocate**, I want to understand opposition arguments so I can build more effective coalitions

## Functional Requirements

### Core Multi-Agent System
1. **The system must implement a Dynamic Orchestration Agent** that analyzes policy issues and determines relevant stakeholder perspectives
2. **The system must include a Stakeholder Agent Factory** that can instantiate agents with any specified perspective (renter, landlord, employee, employer, resident, etc.)
3. **The system must support multi-party debates** with 2-4 stakeholder agents simultaneously engaged in policy discussions
4. **The system must use A2A (Agent-to-Agent) protocols** for structured debate communication between any combination of stakeholder agents
5. **The system must integrate with W&B Weave** for transparency in agent reasoning and dynamic debate orchestration

### Dynamic Agent Configuration
6. **The system must include predefined stakeholder templates** for common civic roles (renter/landlord, employee/employer, resident/police/city official, student/teacher/administrator)
7. **The system must allow custom stakeholder definition** where users can specify unique perspectives relevant to their situation
8. **The system must automatically identify relevant stakeholders** for any given policy based on issue analysis
9. **The system must balance debate participation** ensuring all stakeholder voices are heard proportionally

### User Input & Personalization
10. **The system must accept various user context documents** (lease agreements, employment contracts, business licenses, etc.) to determine user's stakeholder role
11. **The system must allow users to specify their primary stakeholder identity** (e.g., "I am a renter and small business owner")
12. **The system must identify relevant existing policies** that affect the user's specified roles and situations
13. **The system must monitor new policy proposals** across multiple domains (housing, labor, public safety, environment, etc.)

### Generic Debate & Analysis System
14. **The system must orchestrate structured debates** between any combination of stakeholder agents on specific policies
15. **The system must ensure each agent presents authentic stakeholder arguments** backed by role-appropriate data and concerns
16. **The system must identify cross-cutting trade-offs** that affect multiple stakeholder groups differently
17. **The system must synthesize multi-party debate outcomes** into clear summaries of competing interests and potential compromises

### Supporting Agent Infrastructure
18. **The system must include a Universal Policy Discovery Agent** that finds relevant policies across multiple domains using BrowserBase and Exa
19. **The system must include a Cross-Domain Policy Monitoring Agent** that tracks new proposals from various government levels and departments
20. **The system must include a Contextual Research Agent** that provides domain-specific background and precedent for any policy area
21. **The system must include a Personalized Action Agent** that crafts communications appropriate to user's stakeholder role and representatives

### User Interface & Experience
22. **The system must provide dynamic debate interface** adapting to show 2-4 stakeholder agents based on policy complexity
23. **The system must offer stakeholder role selection** allowing users to choose their primary perspective or multiple roles
24. **The system must generate role-appropriate action outputs** including draft communications tailored to user's stakeholder identity
25. **The system must maintain cross-domain debate history** so users can reference discussions across different policy areas

### Data Integration & Processing
26. **The system must integrate with sponsor tools** including Exa for multi-domain policy research, BrowserBase for government monitoring, and Google Cloud for dynamic agent coordination
27. **The system must parse various user context documents** to extract relevant terms and stakeholder roles
28. **The system must maintain cross-domain policy databases** covering housing, labor, public safety, environment, and other civic areas
29. **The system must track representative information** across different government departments and levels based on policy domain

## Non-Goals (Out of Scope)

1. **Legal advice provision** - The system provides perspective analysis, not legal counsel across any domain
2. **Actual policy drafting** - No creation of legislative language or formal policy documents
3. **Real-time government integration** - No direct submission of comments to government systems
4. **Financial calculations** - No economic impact modeling or financial projections
5. **Dispute resolution services** - No mediation between actual stakeholders
6. **Domain-specific management tools** - No lease management, HR systems, or operational features
7. **Social networking elements** - No user-to-user communication or community features
8. **Real-time voice debates** - Text-based interface only for hackathon scope

## Design Considerations

### Dynamic Debate Interface Design
- **Flexible agent representation** with distinct visual styling for each stakeholder type
- **Scalable conversation threading** supporting 2-4 simultaneous perspectives
- **Cross-cutting issue highlighting** emphasizing trade-offs that affect multiple groups
- **Adaptive synthesis summaries** reflecting complexity of multi-party discussions

### Universal User Experience Flow
- **Role identification**: Upload context documents OR select stakeholder identity
- **Policy discovery**: System finds relevant policies across user's domains of interest
- **Stakeholder mapping**: Orchestration agent determines relevant perspectives for debate
- **Multi-party debate**: Watch/participate in structured discussions between relevant agents
- **Contextual action**: Craft communications appropriate to user's role and representatives

### Generic Architecture Components
- **Stakeholder Template Library**: Predefined personas (renter, landlord, employee, employer, resident, police, city official, student, teacher, business owner, etc.)
- **Policy Domain Mapping**: Automated classification of policies into relevant stakeholder categories
- **Dynamic Agent Spawning**: Runtime instantiation of appropriate agents based on policy analysis
- **Cross-Domain Knowledge Base**: Shared factual foundation accessible to all stakeholder agents

## Technical Considerations

### Dynamic Multi-Agent Architecture
- **Agent factory pattern** for runtime instantiation of stakeholder perspectives
- **Modular debate protocols** that adapt to 2-4 participant discussions
- **Cross-domain knowledge integration** ensuring agents have appropriate expertise for their assigned roles
- **Conflict escalation mechanisms** when stakeholder positions reach fundamental disagreements

### Generic Context Processing
- **Multi-format document parsing** (leases, contracts, licenses, employment agreements, etc.)
- **Stakeholder role extraction** from various user context documents
- **Policy relevance mapping** connecting documents to applicable policy domains
- **Privacy-preserving analysis** protecting sensitive information across all document types

### Universal Policy Monitoring
- **Multi-domain government tracking** across housing, labor, public safety, environment, education, etc.
- **Cross-jurisdictional monitoring** from federal to local levels based on user's stakeholder roles
- **Policy classification systems** automatically categorizing proposals by affected stakeholder groups
- **Impact prediction algorithms** estimating which stakeholders are most affected by each policy

## Success Metrics

### Technical Success
- **Dynamic agent instantiation**: Orchestration agent successfully spawns appropriate stakeholders for any policy domain
- **Multi-party debate coherence**: 2-4 agents maintain distinct, authentic perspectives throughout complex discussions
- **Cross-domain functionality**: System works effectively across housing, labor, public safety, and other policy areas
- **A2A protocol scalability**: Smooth coordination between variable numbers of agents based on policy complexity

### User Experience Success
- **Stakeholder authenticity**: Users recognize genuine representation of different perspectives, not caricatures
- **Cross-cutting insight**: Users identify trade-offs and connections they hadn't considered across stakeholder groups
- **Role relevance**: System accurately identifies user's stakeholder position and generates appropriate analysis
- **Actionable complexity**: Users can form nuanced opinions and craft sophisticated civic communications

### Demo Success
- **Architectural innovation**: Judges understand the technical sophistication of dynamic agent instantiation
- **Universal applicability**: Clear demonstration that framework works beyond initial housing use case
- **Scalability demonstration**: Obvious path to expand across all civic policy domains
- **Competitive differentiation**: No existing system provides dynamic multi-stakeholder policy analysis

## Open Questions

1. **Agent selection algorithms**: How does the orchestration agent determine which stakeholders are most relevant for complex, multi-domain policies?
2. **Stakeholder authenticity**: How do we ensure dynamic agents represent genuine perspectives without harmful stereotypes across all domains?
3. **Debate scaling**: What's the optimal number of agents for different policy complexities, and how do we manage conversation flow?
4. **Cross-domain expertise**: How do we ensure agents have appropriate knowledge depth across all possible policy areas?
5. **User role conflicts**: How do we handle users with multiple, potentially conflicting stakeholder identities (e.g., renter AND small business owner)?
6. **Template extensibility**: What's the most efficient way to add new stakeholder templates as we expand to new policy domains?
7. **Context document variety**: How do we handle the wide variety of documents users might upload across different domains?
8. **Representative matching**: How do we determine the most relevant government contacts across multiple policy areas and jurisdictions?

## Implementation Priority for Hackathon

### Phase 1 (Day 1): Dynamic Agent Architecture
- Orchestration Agent with stakeholder analysis capabilities
- Stakeholder Agent Factory with basic templates (renter, landlord, employee, employer)
- Dynamic A2A protocol supporting variable agent numbers
- W&B Weave integration for multi-agent transparency

### Phase 2 (Day 2 Morning): Cross-Domain Integration
- Universal Policy Discovery agents using BrowserBase and Exa
- Multi-domain policy database (housing + labor policies for demo)
- Contextual Research Agent with cross-domain knowledge
- Flexible debate interface supporting 2-4 agents

### Phase 3 (Day 2 Afternoon): Demo Scenarios & Polish
- Two complete demo scenarios: housing (renter vs landlord) + labor (employee vs employer)
- Personalized Action Agent for role-appropriate communications
- End-to-end testing with dynamic agent spawning
- DevPost submission highlighting universal architecture

## Demo Scenarios

### Scenario 1: "SF Rent Control Expansion" (Housing Domain)
**Setup**: User uploads lease → System spawns Renter Agent vs Landlord Agent
**Policy**: New SF proposal to expand rent control to post-1995 buildings
**Demo**: Live debate showing housing-specific trade-offs

### Scenario 2: "Gig Worker Classification" (Labor Domain) 
**Setup**: User indicates gig worker status → System spawns Employee Agent vs Employer Agent
**Policy**: CA Assembly Bill on independent contractor classification
**Demo**: Same architecture, different domain - showing universal applicability

This demonstrates the system's ability to dynamically adapt to any policy domain while maintaining sophisticated multi-stakeholder analysis.