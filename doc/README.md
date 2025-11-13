# Documentation System

This `doc/` directory uses the **file-based orchestration pattern** for AI agent coordination.

## Structure

```
doc/
├── task/
│   └── context.md          ← Central source of truth for project state
├── research/
│   └── *.md                ← Sub-agent research outputs and plans
└── README.md               ← This file
```

## How It Works

### 1. Donnie (Orchestrator) Reads Context
At the start of every session, Donnie reads `doc/task/context.md` to understand:
- Current project state
- What's been done recently
- What's working and what's broken
- What needs to happen next

### 2. Sub-Agents Research and Plan
When a task requires research or planning:
- Donnie delegates to specialized sub-agents
- Sub-agents read `doc/task/context.md` for project context
- Sub-agents perform research/planning
- Sub-agents write detailed plans to `doc/research/*.md`

### 3. Donnie Reviews and Executes
- Donnie reads the research/plan from `doc/research/*.md`
- Donnie reviews it critically
- Donnie asks clarifying questions if needed
- Donnie executes the approved plan
- Donnie updates `doc/task/context.md` with the outcome

### 4. Continuous Context
Every completed task updates `doc/task/context.md`, ensuring:
- No context loss between sessions
- Clear audit trail of decisions
- Easy handoff between sessions
- Institutional knowledge builds over time

## Workflow Example

```
User: "Add Redis caching to this project"
    ↓
Donnie reads doc/task/context.md
    ↓
Donnie delegates to Infrastructure Agent
    ↓
Infrastructure Agent:
  - Reads doc/task/context.md
  - Researches Redis integration patterns
  - Creates doc/research/redis_integration_plan.md
  - Notifies Donnie: "Plan ready"
    ↓
Donnie:
  - Reads doc/research/redis_integration_plan.md
  - Reviews the plan
  - Approves it
  - Executes the plan (adds Redis to docker-compose, etc.)
  - Updates doc/task/context.md with outcome
```

## File Naming Conventions

### context.md
- Single file per project
- Always kept up to date
- 500-800 tokens max (concise)
- Updated after every significant change

### research/*.md
- One file per research task
- Format: `{topic}_{date}_plan.md`
- Examples:
  - `redis_integration_20251111_plan.md`
  - `database_migration_20251111_plan.md`
  - `ui_redesign_20251111_plan.md`

## Best Practices

### For Orchestrators (Donnie)
- ✅ Always read context.md first
- ✅ Always update context.md after completing work
- ✅ Review sub-agent plans critically before executing
- ✅ Ask questions if plans are unclear

### For Sub-Agents
- ✅ Always read context.md before starting research
- ✅ Write comprehensive, actionable plans
- ✅ Include rollback procedures
- ✅ Use standard completion message format

### For Humans
- ✅ Read context.md to see current project state
- ✅ Read research/ to see what's been planned
- ✅ Update context.md if you make manual changes
- ✅ Keep context.md concise (archive old info if needed)

## Maintenance

### When context.md Gets Too Large
If `doc/task/context.md` exceeds 800 tokens:
1. Archive old "Recent Changes" to `doc/history/changes_{month}.md`
2. Archive old "Key Decisions" to `doc/history/decisions_{month}.md`
3. Keep only last 7 days of changes in context.md
4. Keep only critical decisions that affect current work

### Cleanup research/
Periodically (monthly):
- Archive old research files to `doc/archive/research/`
- Keep only active/recent research in `doc/research/`
- Update context.md to reference archived research if needed

## Questions?

See: `kb/topics/orchestrator-patterns.md` for architectural details
