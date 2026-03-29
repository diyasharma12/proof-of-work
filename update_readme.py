from github import Github
import os
from collections import defaultdict

print("Script started...")

g = Github(os.getenv("GITHUB_TOKEN"))
user = g.get_user()
username = user.login

print("Username:", username)

query = f"author:{username} type:pr"
prs = g.search_issues(query=query)

print("Total PRs fetched:", prs.totalCount)

prs_by_org = defaultdict(list)

for pr in prs:
    org_name = pr.repository.full_name.split("/")[0]

    repo = g.get_repo(pr.repository.full_name)
    full_pr = repo.get_pull(pr.number)

    prs_by_org[org_name].append({
        "repo": pr.repository.name,
        "number": pr.number,
        "title": pr.title,
        "state": "Merged" if full_pr.merged_at else pr.state.capitalize(),
        "url": pr.html_url,
        "created_at": pr.created_at.strftime("%Y-%m-%d"),
        "merged_at": full_pr.merged_at.strftime("%Y-%m-%d") if full_pr.merged_at else "-"
    })

# Generate README
readme = "# 🚀 Proof of Work\n\n"
readme += "My open-source contributions to public organizations.\n\n"

total_prs = prs.totalCount
merged_prs = sum(
    1 for org in prs_by_org.values() for pr in org if pr["merged_at"] != "-"
)

readme += f"**Total PRs**: {total_prs} | **Merged PRs**: {merged_prs}\n\n"

if total_prs == 0:
    readme += "_No PRs yet — start contributing 🚀_\n"

for org, prs in prs_by_org.items():
    readme += f"\n## Organization: {org}\n\n"
    readme += "| Repository | PR Title | Status | Created At | Merged At | Link |\n"
    readme += "|------------|----------|--------|------------|-----------|------|\n"

    for pr in sorted(prs, key=lambda x: x["created_at"], reverse=True):
        readme += f"| {pr['repo']} | {pr['title']} | {pr['state']} | {pr['created_at']} | {pr['merged_at']} | [PR #{pr['number']}]({pr['url']}) |\n"

with open("README.md", "w") as f:
    f.write(readme)

print("README updated successfully!")
