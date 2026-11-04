# AAMAD Agent Framework

This project uses the AAMAD framework for multi-agent development.
Framework version: 1.0.1
See the full agent definitions in the IDE-specific directories.

## Agent Personas
- **@product-mgr** — Product Manager: Orchestrates product vision and requirements
- **@system.arch** — System Architect: Reviews existing code (brownfield) and produces SAD/SFS
- **@ux.designer** — UX Designer: Interaction design and visual direction (`ux.md`)
- **@project.mgr** — Project Manager: Scaffolds project and environment
- **@frontend.eng** — Frontend Developer: Implements the approved MVP UI
- **@backend.eng** — Backend Developer: Builds backend for the selected runtime
- **@integration.eng** — Integration Engineer: Connects frontend and backend
- **@qa.eng** — QA Engineer: Validates MVP functionality (unit + integration)
- **@security.eng** — Security Engineer: Assesses MVP security before Deliver
- **@devops.eng** — DevOps Engineer: Packages deploy/CI, runbook, and user guide

## Workflow
Greenfield (default, `project.mode: greenfield`):
1. **Define** (Phase 1): @product-mgr → elicitation → Market Research (optional) → PRD → @system.arch → SAD → @ux.designer → ux.md (when UI is in scope)
2. **Build** (Phase 2): @project.mgr → @frontend.eng / @backend.eng → @integration.eng → @qa.eng → @security.eng
3. **Deliver** (Phase 3): @devops.eng → deploy.md + user-guide.md

Brownfield (`project.mode: brownfield`):
1. **Review** (Phase 0): @system.arch → *review-codebase → *create-sad (as-is + proposed enhancements) → operator decision
2. **Constrained Define** (Phase 1): @product-mgr writes PRD and stories only for approved enhancements
3. **UX** (material UI enhancements only): @ux.designer → enhancement-scoped ux.md
4. **Build** then **Deliver** as above; extend the existing tree — do not scaffold a replacement app

## Rules
All development follows AAMAD core rules. See project-context/ for artifacts.
Run `aamad validate` to check artifact quality gates.

## Agent Definitions
See `.cursor/agents/` for Cursor agent definitions.
