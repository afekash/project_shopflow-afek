Plan data engineering course materials for a new topic. Before creating content, gather the instructor's intent.

## Questions to Ask

Group naturally and ask follow-ups based on answers -- don't ask all at once:

1. **Scope**: Topic, lecture duration, practical vs theory balance
2. **Depth**: What to cover deeply, what to mention briefly, what to skip entirely
3. **Internals**: How much "how it works under the hood" vs practical usage
4. **Context**: Historical context needed? What existed before this tool/concept?
5. **Industry**: Related tools, CI/CD integration, cloud patterns, team workflows to mention
6. **Exercises**: Type of hands-on practice -- demos, guided exercises, open-ended challenges
7. **Lab environment**: Does the lesson need sidecar services? Check existing `labs/*/` directories first
8. **Audience**: What students already know, what IDE/OS they use
9. **Style**: Any specific tone, format, or emphasis preferences

## Plan Output

After gathering intent, create a plan with:

- **Folder structure** -- full directory tree of all files to create under `materials/[topic]/`
- **Content outline per file** -- bullet points of what each file covers, with estimated line count
- **Time allocation table** -- how lecture time maps to sections
- **Lab environment** -- which lab to use (or "none" if lesson uses only SQLite/stdlib)

## Material Standards

- Files go under `materials/[topic]/` with a `README.md` entry point
- Numbered folders (`01-introduction/`) and files (`01-topic-name.md`)
- Max 250 lines per `.md` file; split large subjects into smaller files
- Exercises grouped at the end
- Include runnable demo code in a `demo-app/` folder when applicable
- Follow all conventions in the `author-lessons` skill

## Examples and Code

Examples should be simple and easy to follow, but mimic real-life usage patterns. Students should see how things actually look in practice without getting lost in complexity.

## After Planning

Ask if the instructor wants to adjust anything before starting implementation.

$ARGUMENTS
