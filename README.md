# RAG-Agent
# Agentic Tech Support LLM: A Screen-Sharing and Feedback-Driven Autonomous Support System

**Author:** Vikram Rajpurohit  
**ID:** 240375096

## Introduction

Software complexity drives demand for efficient technical support. Traditional systems, reliant on human agents or static chatbots, struggle with context-specific issues (3). Agentic AI and large language models (LLMs) enable autonomous, adaptive support using screen sharing and feedback.

This research proposes an Agentic Tech Support LLM that leverages multimodal inputs (screen visuals, logs, dialogue) and reinforcement learning with human feedback (RLHF) to diagnose and resolve issues (1). It builds on human-AI interaction (2) and screen-based paradigms (3).

For HCI researchers and tech support providers, the project offers:

- **Academic:** Advances agentic AI applications.
- **Technical:** Delivers a prototype for adaptive support.
- **Business:** Reduces costs, enhances satisfaction.
- **Social:** Improves digital accessibility.

## Problem Statement

Technical support systems lack contextual awareness, underutilizing screen sharing and system logs (3). Current AI agents rarely adapt via user feedback (1), limiting effectiveness for complex issues.

This research addresses the need for autonomous, context-aware tech support using screen sharing, log analysis, and RLHF. Evaluated via user studies, it answers: Why is adaptive, screen-sharing-based support needed?

## Research Questions

The research is guided by:

1. How effectively can an agentic LLM interpret issues using screen-sharing and log analysis compared to text-based inputs?
2. To what extent can RLHF improve accuracy and user satisfaction?
3. What are the usability and ethical challenges in deploying such a system?

These questions are scoped for the dissertation timeframe and relevant to HCI.

## Methods

A mixed-methods approach will design, implement, and evaluate the system:

1. **System Design:** Develop a multimodal LLM agent in Python, integrating open-source models (e.g., LLaMA) with screen-parsing (OpenCV, Tesseract OCR), log analysis, NLP, and RLHF (1).

2. **Prototype Implementation:** Build a prototype using PyTorch for RLHF, Flask for the interface, and LangChain/LangGraph for agentic workflows (7). The system will:
   - **Agentic Browser Capabilities:** Use LangChain with Selenium to analyze browser errors (e.g., JavaScript console, network logs) and infer UI context (e.g., broken elements) (3). LangChain manages tool integration and conversational context for troubleshooting.
   - **Windows Log Analysis:** Parse Windows Event Viewer logs using Python’s win32evtlog, inspired by Nxthink, to identify errors (e.g., application crashes, driver issues). LangChain integrates log data with screen visuals for comprehensive diagnostics.
   - **Remote Task Execution:** Employ LangGraph to model troubleshooting as stateful graphs, orchestrating tasks (e.g., restarting services, clearing caches) on remote Windows systems via secure APIs (e.g., WinRM). LangGraph enables dynamic decision-making and feedback loops.
   - Process screen captures, extract UI elements, and generate solutions via dialogue or automation, refined by RLHF.

3. **User Studies:** Test with 20–30 participants, comparing performance (accuracy, response time) to text-based chatbots, collecting qualitative feedback.

4. **Evaluation:** Measure issue resolution rate, user satisfaction (Likert scales), and RLHF improvement (reward convergence). Iterate based on feedback.

Python’s libraries, LangChain, and LangGraph ensure robust development (7). OpenCV/Tesseract enable screen parsing, and RLHF aligns with adaptive learning (1). Browser automation, log analysis, and remote execution enhance context-awareness.

## Ethical Implications

Using the AI4People framework (4) and autonomous system insights (5), the project addresses:

- **Privacy:** Screen sharing and log analysis risk data exposure. Data minimization and anonymization will be used (5).
- **Transparency:** Users will be informed of agent actions.
- **Bias:** LLM biases may affect diverse users. Inclusive datasets will be explored (2).
- **Accountability:** Errors require human-in-the-loop escalation (6).

Ethical guidelines from Ethics and AI (24 February 2025) ensure responsible deployment.

## Requirements and Feasibility

- **Functional:** Real-time screen parsing, log analysis, dialogue-based diagnosis, remote task execution, feedback-driven learning.
- **Non-functional:** 80% issue resolution rate, <5-second response, secure data handling.
- **User:** Intuitive interface, accessibility (e.g., text-to-speech).

Accessible tools (Python, OpenCV, PyTorch, LangChain, LangGraph) and a 6-month timeline ensure feasibility. Risks include:

- **Screen/Log Parsing Inaccuracies (Medium Likelihood, High Impact):** Use robust OCR/UI detection, manual validation.
- **Slow RLHF Convergence (Medium Likelihood, Medium Impact):** Use pre-trained models, simulated feedback.
- **User Recruitment Delays (Low Likelihood, Medium Impact):** Leverage university platforms.

## Project Plan

From 15 May 2025 to 15 November 2025, tasks include:

- **May 15–Jun 15:** Literature review, system design. Deliverable: Design document.
- **Jun 16–Aug 15:** Prototype development (screen parsing, log analysis, LLM, RLHF). Milestone: Functional prototype.
- **Aug 16–Sep 15:** Testing, refinement. Deliverable: Test report.
- **Sep 16–Oct 15:** User studies, data collection. Milestone: Completed evaluations.
- **Oct 16–Nov 10:** Analysis, dissertation writing. Deliverable: Draft dissertation.
- **Nov 11–15:** Final revisions, submission. Deliverable: Final dissertation.

The schedule aligns with methods (Section 4).

## References

[1] Anonymous, Agentic AI for Scientific Discovery: A Survey of Progress, Challenges, and Future Directions, arXiv:2503.xxxxx, 2025.

[2] Anonymous, Human-AI Interaction in the Age of Agentic AI: A System-Theoretical Approach, Frontiers in Human-Computer Interaction, doi:10.3389/xxxxx, 2025.

[3] T. Masterman, Computer Use and AI Agents: A New Paradigm for Screen Interaction, Medium, 2024, https://medium.com/tds-archive/computer-use-and-ai-agents.

[4] L. Floridi, J. Cowls, M. Beltrametti, et al., AI4People—An Ethical Framework for a Good AI Society: Opportunities, Risks, Principles, and Recommendations, Minds and Machines, 28:689–707, 2018.

[5] D.J. Glancy, Privacy in Autonomous Vehicles, Santa Clara Law Review, 52(4):1171–1239, 2012.

[6] N.J. Goodall, Ethical Decision Making During Automated Driving, IEEE Intelligent Systems, 29(4):92–96, 2014.

[7] Anonymous, LangChain and LangGraph: Frameworks for Agentic AI Workflows, arXiv:2504.xxxxx, 2025.

[8] F. Pajares, Elements of a Proposal, 2007, http://des.emory.edu/mfp/proposal.html.

[9] A.M. Wilkinson, The Scientist’s Handbook for Writing Papers and Dissertations, Prentice Hall, Englewood Cliffs, NJ, 1991.

[10] J.W. Creswell, Research Design: Qualitative and Quantitative Approaches, Sage, Thousand Oaks, CA, 1994.

[11] W. Wiersma, Research Methods in Education: An Introduction (Sixth edition), Allyn and Bacon, Boston, 1995.
