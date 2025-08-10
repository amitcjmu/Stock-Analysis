# Labels Policy

Existing labels to use where possible:
- backlog (default for new issues)
- ready
- in progress
- in review
- type:task
- type:bug
- type:docs
- priority:high / priority:medium / priority:low

If any are missing in the repo, create them via GitHub UI or a labels sync script. Suggested additions:
- type:tech-debt
- area:backend
- area:frontend
- area:infra
- phase:1, phase:2, phase:3, phase:4, phase:5 (optional; aligns with audit phases)

Git LFS suggestion (manual setup):
- Track large media: `git lfs track "*.pdf" "*.png" "*.jpeg"`
- Commit `.gitattributes` and push. Coordinate history rewrite separately if needed.
