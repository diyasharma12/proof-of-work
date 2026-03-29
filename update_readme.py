from collections import defaultdict
import json
import os

from github import Github


def load_organizations(config_path="config.json"):
    if not os.path.exists(config_path):
        return set()

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    orgs = config.get("organizations", [])
    if not isinstance(orgs, list):
        return set()

    return {org.strip().lower() for org in orgs if isinstance(org, str) and org.strip()}


def should_include_org(org_name, allowed_orgs):
    return not allowed_orgs or org_name.lower() in allowed_orgs


print("Script started...")
g = Github(os.getenv("GITHUB_TOKEN"))
username = os.getenv("GITHUB_ACTOR", "").strip()
if not username:
    # Local fallback when running outside GitHub Actions.
    username = g.get_user().login
allowed_orgs = load_organizations()

print("Username:", username)
print("Configured org filters:", sorted(allowed_orgs) if allowed_orgs else "all orgs")

prs_by_org = defaultdict(list)
issues_by_org = defaultdict(list)

# Pull Requests authored by the user.
pr_query = f"author:{username} type:pr"
pr_results = g.search_issues(query=pr_query)
print("Total PRs fetched (all orgs):", pr_results.totalCount)

for pr in pr_results:
    org_name = pr.repository.full_name.split("/")[0]
    if not should_include_org(org_name, allowed_orgs):
        continue

    repo = g.get_repo(pr.repository.full_name)
    full_pr = repo.get_pull(pr.number)

    prs_by_org[org_name].append(
        {
            "repo": pr.repository.name,
            "number": pr.number,
            "title": pr.title,
            "state": "Merged" if full_pr.merged_at else pr.state.capitalize(),
            "url": pr.html_url,
            "created_at": pr.created_at.strftime("%Y-%m-%d"),
            "merged_at": full_pr.merged_at.strftime("%Y-%m-%d") if full_pr.merged_at else "-",
        }
    )

# Issues authored by the user (excluding PRs via type:issue).
issue_query = f"author:{username} type:issue"
issue_results = g.search_issues(query=issue_query)
print("Total issues fetched (all orgs):", issue_results.totalCount)

for issue in issue_results:
    org_name = issue.repository.full_name.split("/")[0]
    if not should_include_org(org_name, allowed_orgs):
        continue

    issues_by_org[org_name].append(
        {
            "repo": issue.repository.name,
            "number": issue.number,
            "title": issue.title,
            "state": issue.state.capitalize(),
            "url": issue.html_url,
            "created_at": issue.created_at.strftime("%Y-%m-%d"),
            "closed_at": issue.closed_at.strftime("%Y-%m-%d") if issue.closed_at else "-",
        }
    )

all_orgs = sorted(set(prs_by_org.keys()) | set(issues_by_org.keys()))
total_prs = sum(len(items) for items in prs_by_org.values())
merged_prs = sum(1 for items in prs_by_org.values() for pr in items if pr["merged_at"] != "-")
total_issues = sum(len(items) for items in issues_by_org.values())
closed_issues = sum(
    1 for items in issues_by_org.values() for issue in items if issue["closed_at"] != "-"
)

readme = "# 🚀 Proof of Work\n\n"
readme += "My open-source contributions to public organizations.\n\n"
readme += (
    f"**Total PRs**: {total_prs} | **Merged PRs**: {merged_prs} | "
    f"**Total Issues**: {total_issues} | **Closed Issues**: {closed_issues}\n\n"
)

if not all_orgs:
    readme += "_No contributions found for the configured organizations yet._\n"

for org in all_orgs:
    org_prs = sorted(prs_by_org[org], key=lambda x: x["created_at"], reverse=True)
    org_issues = sorted(issues_by_org[org], key=lambda x: x["created_at"], reverse=True)
    readme += f"\n## Organization: {org}\n\n"
    readme += f"- PRs: {len(org_prs)}\n"
    readme += f"- Issues: {len(org_issues)}\n\n"

    if org_prs:
        readme += "### Pull Requests\n\n"
        readme += "| Repository | PR Title | Status | Created At | Merged At | Link |\n"
        readme += "|------------|----------|--------|------------|-----------|------|\n"
        for pr in org_prs:
            readme += (
                f"| {pr['repo']} | {pr['title']} | {pr['state']} | {pr['created_at']} | "
                f"{pr['merged_at']} | [PR #{pr['number']}]({pr['url']}) |\n"
            )
        readme += "\n"

    if org_issues:
        readme += "### Issues\n\n"
        readme += "| Repository | Issue Title | Status | Created At | Closed At | Link |\n"
        readme += "|------------|-------------|--------|------------|-----------|------|\n"
        for issue in org_issues:
            readme += (
                f"| {issue['repo']} | {issue['title']} | {issue['state']} | {issue['created_at']} | "
                f"{issue['closed_at']} | [Issue #{issue['number']}]({issue['url']}) |\n"
            )
        readme += "\n"

with open("README.md", "w", encoding="utf-8") as f:
    f.write(readme)

print("README updated successfully!")
