# Welcome to Fusion

## New contributor guide

To get an overview of the project, go through the [README](README.md). Here are some resources to help you get started with open source contributions:

- [Set up Git](https://docs.github.com/en/get-started/quickstart/set-up-git)
- [GitHub flow](https://docs.github.com/en/get-started/quickstart/github-flow)
- [Collaborating with pull requests](https://docs.github.com/en/github/collaborating-with-pull-requests)


## Issues

### Create a new issue

If you spot a problem with the code, [search if an issue already exists](https://docs.github.com/en/github/searching-for-information-on-github/searching-on-github/searching-issues-and-pull-requests#search-by-the-title-body-or-comments). If a related issue doesn't exist, you can open a new issue using a relevant [issue form](https://github.com/github/docs/issues/new/choose). 

These points must be kept in mind when opening a new issue: 
- Use the `module name` (in lowercase, followed by a colon) where the issue has occured as the title's prefix.
- Give a brief description about the issue or steps to reproduce it.

<br>

## Making PRs

Pull requests are the easiest way to contribute changes to git repositories at Github. They are the preferred contribution method, as they offer a nice way for commenting and amending the proposed changes.

- You need a local "fork" of the branch of your respective modules, from the [main Fusion repository](https://github.com/FusionIIIT/Fusion).

- Use a "feature branch" for your changes. That separates the changes in the pull request from your other changes and makes it easy to edit/amend commits in the pull request. Workflow using "feature_x" as the example:

- Update your local git fork to the tip (of the master, usually)

- Create the feature branch:
    ```
    git checkout -b <branch_name>
    ```

- Edit changes and commit them locally:
    ```
    git add .
    git commit -m "<commit_message>"
    ```

- Push them to your Github fork. That creates the "feature_x" branch at your G ithub fork and sets it as the remote of this branch
    ```
    git push -u origin feature_x
    ```

- When you now visit Github, you should see a proposal to create a pull request. 

- Make sure you target your pull request to `your module's branch only`. PRs made to any other branch will not be approved.

- Ensure that your fork is up to date with the branch at the original repository. It is possible that some other developer's PRs have been merged before you, which leads to merge conflicts, if not resolved beforehand. Use `git rebase` or `git merge <branch_name>` to get your branch up to date with origin. 

- If you later need to add new commits to the pull request, you can simply commit the changes to the local branch and then use git push to automatically update the pull request.

- If you need to change something in the existing pull request, you can use `git push -f` to overwrite the original commits. That is easy and safe when using a feature branch.

- All the PRs initialized/going to initialize should follow the PR title in the format. This convention has to be followed so that reviewers can quickly identify the PR belonging to their module.

    ```
    <module_name> : <week_no> : <PR_Title>
    ```

    `<module_name> `- You only have to specify the module name in lowercase letters. For example, os-2, ac-2

    ` <week_no> `- Specify the week number in the PR title that is the week in which this task has been assigned to you.

    `<PR_Title> `- Specify the title of the PR starting with the lowercase letter of the first word.

- Don't add the changes made in the `settings/development.py` file regarding the database setup you have made in the local system and don't push the database dump file in the PR. These PRs won't be considered to be merged the respective module branch.

- Don't make any changes regarding the dependencies or their versions in the `requirements.txt` file. If you find any dependency which is in need to be added or upgraded inside the repository, contact the Project leads first and make suitable changes then. 

## Code of Conduct
Fusion has adopted a Code of Conduct that we expect project participants to adhere to. Please [read the full text](./CODE_OF_CONDUCT.md) so that you can understand what sort of behaviour is expected.

