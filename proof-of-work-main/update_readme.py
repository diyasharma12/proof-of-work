import os
from collections import defaultdict

from github import Github


README_PATH = "README.md"


def resolve_username() -> str:
    # Priority:
    # 1) Explicit GH_USERNAME env
    # 2) Owner from GITHUB_REPOSITORY (owner/repo)
    # 3) Token owner as fallback
    explicit = os.getenv("GH_USERNAME")
    if explicit:
        return explicit.strip()

    repo_slug = os.getenv("GITHUB_REPOSITORY", "")
    if "/" in repo_slug:
        return repo_slug.split("/", 1)[0]

    return g.get_user().login


def build_readme(prs_by_org: dict, total_prs: int, merged_prs: int, username: str) -> str:
    lines = [
        "# 🚀 Proof of Work",
        "",
        f"My open-source contributions to public organizations by **{username}**.",
        "",
        f"**Total PRs**: {total_prs} | **Merged PRs**: {merged_prs}",
        "",
    ]

    if total_prs == 0:
        lines.append("_No PRs found yet. Start contributing!_")
        lines.append("")
        return "\n".join(lines)

    for org in sorted(prs_by_org):
        lines.append(f"## Organization: {org}")
        lines.append("")
        lines.append("| Repository | PR Title | Status | Created At | Merged At | Link |")
        lines.append("|------------|----------|--------|------------|-----------|------|")

        for pr in sorted(prs_by_org[org], key=lambda x: x["created_at"], reverse=True):
            lines.append(
                f"| {pr['repo']} | {pr['title']} | {pr['state']} | {pr['created_at']} | "
                f"{pr['merged_at']} | [PR #{pr['number']}]({pr['url']}) |"
            )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


token = os.getenv("GITHUB_TOKEN")
if not token:
    raise RuntimeError("Missing GITHUB_TOKEN")

g = Github(token)
username = resolve_username()
print(f"Updating README for username: {username}")

query = f"author:{username} is:pr is:public"
prs = g.search_issues(query=query)

prs_by_org = defaultdict(list)
total_prs = 0
merged_prs = 0

for pr in prs:
    repo = g.get_repo(pr.repository.full_name)

    # Keep this project focused on organization contributions.
    if repo.owner.type != "Organization":
        continue

    full_pr = repo.get_pull(pr.number)
    merged_at = full_pr.merged_at.strftime("%Y-%m-%d") if full_pr.merged_at else "-"
    if merged_at != "-":
        merged_prs += 1

    total_prs += 1
    org_name = repo.owner.login
    prs_by_org[org_name].append(
        {
            "repo": repo.name,
            "number": pr.number,
            "title": pr.title.replace("\n", " ").strip(),
            "state": "Merged" if full_pr.merged_at else pr.state.capitalize(),
            "url": pr.html_url,
            "created_at": pr.created_at.strftime("%Y-%m-%d"),
            "merged_at": merged_at,
        }
    )

readme_content = build_readme(prs_by_org, total_prs, merged_prs, username)
with open(README_PATH, "w", encoding="utf-8") as f:
    f.write(readme_content)

print(f"README updated successfully with {total_prs} PRs.")
