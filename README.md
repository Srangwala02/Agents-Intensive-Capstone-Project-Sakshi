# IntelliGuide

## Overview
IntelliGuide is an AI-powered tutoring agent designed to provide personalized, real-time learning support tailored to software engineering students. It addresses the challenge students face in obtaining timely, customized help for course concepts, exam preparation, and practice questions when teachers or peers are unavailable. Unlike static resources, IntelliGuide adapts to individual doubts and weak areas, ensuring comprehensive understanding across key subjects like operating systems, computer networks, and databases.

## Motivation
Software engineering students often struggle with:
- Getting immediate, tailored help with complex topics.
- Using generic resources that do not adapt to their unique learning needs.
- Filling knowledge gaps before exams due to lack of personalized guidance.

IntelliGuide resolves these issues by offering an interactive assistant that answers conceptual doubts, generates practice quizzes, and evaluates student performance in a focused manner.

## Why Multi-agent Architecture?
Multi-agent systems fit this educational problem because:
- They enable specialized agents to focus on specific tasks such as doubt resolution, quiz generation, evaluation, and domain-specific reasoning.
- Domain expert agents (Database, OS, Networking) provide deep, accurate knowledge in their subject areas.
- A root orchestrator agent coordinates workflows, routing requests efficiently to the relevant specialists.
- This division improves the quality and reliability of tutoring compared to a monolithic AI solution.

The architecture supports a planner–solver–evaluator workflow pattern recommended for educational multi-agent systems.

## System Components
- **Root/Orchestrator Agent:** Manages overall workflow, directing requests to doubt resolver, quiz generator, or evaluator agents.
- **Doubt Resolver Agent:** Handles conceptual questions, consulting domain experts to provide step-by-step explanations tailored to student levels.
- **Quiz Generation Agent:** Creates quizzes based on requested topics, calls domain experts for question content, and stores quizzes in MongoDB, associating quiz IDs with user sessions.
- **Quiz Evaluator Agent:** Retrieves stored quiz answers from MongoDB using session quiz IDs, compares student answers, and generates detailed feedback and scores.
- **Domain Expert Agents:** Specialized in Operating Systems, Computer Networks, and Databases, providing deep subject-matter expertise.
- **MongoDB:** Used for quiz persistence and metadata storage.
- **Session Management:** Tracks active quiz IDs and student context across multiple interactions.
- **External Search Tool:** Built-in real-time web search integration for up-to-date reference information beyond internal agent knowledge.
- **Logging and Observability:** Captures interactions, agent decisions, tool calls, database operations, and evaluation results for monitoring, debugging, and improvement.

## Demo Workflow
1. A student asks a conceptual question via the chat interface.
2. The root agent recognizes it as a doubt and delegates the query to the doubt resolver.
3. The doubt resolver consults the relevant domain expert to generate a clear, tailored explanation.
4. The student requests a quiz on a specific topic.
5. The root agent routes this to the quiz generation agent, which creates the quiz using domain experts, saves it in MongoDB, and returns questions along with a quiz ID.
6. After submission, the quiz evaluator agent fetches the quiz by ID, compares answers, and delivers a detailed score and feedback, closing the personalized learning loop.

## Future Enhancements
With additional time, the system would be enhanced by:
- A **Guidance Agent** providing longitudinal, personalized coaching based on quiz history, doubt patterns, and interaction data.
- Rich analytics dashboards for teachers and mentors to monitor real-time progress, common misconceptions, and risk indicators.
- Adaptive difficulty tuning to adjust question complexity and hints dynamically, supporting learners at different proficiency levels.
- Expansion to multi-domain support by swapping domain experts, enabling use in subjects like mathematics, science, or language learning.
- Alignment with curricula or exam boards for targeted learning plans and enriched teacher/parent engagement.

---

IntelliGuide exemplifies how multi-agent AI tutoring systems can create deeply personalized, scalable educational experiences that improve student outcomes through modular expertise and orchestrated workflows.
