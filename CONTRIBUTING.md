# Welcome to Fusion

## New contributor guide

To get an overview of the project, go through the [README](README.md). Here are some resources to help you get started with open source contributions:

- [Set up Git](https://docs.github.com/en/get-started/quickstart/set-up-git)
- [GitHub flow](https://docs.github.com/en/get-started/quickstart/github-flow)
- [Collaborating with pull requests](https://docs.github.com/en/github/collaborating-with-pull-requests)



# Issues

## Create a new issue

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

- Push them to your Github fork. That creates the "feature_x" branch at your Github fork and sets it as the remote of this branch
    ```
    git push -u origin feature_x
    ```

- When you now visit Github, you should see a proposal to create a pull request. 

- Make sure you target your pull request to `your module's branch only`. PRs made to any other branch will not be approved.

- Ensure that your fork is up to date with the branch at the original repository. It is possible that some other developer's PRs have been merged before you, which leads to merge conflicts, if not resolved beforehand. Use `git rebase` to get your branch up to date with origin. 

- If you later need to add new commits to the pull request, you can simply commit the changes to the local branch and then use git push to automatically update the pull request.

- If you need to change something in the existing pull request, you can use `git push -f` to overwrite the original commits. That is easy and safe when using a feature branch.

- All the PRs initialized/going to initialize should follow the PR title in the format. This convention has to be followed so that reviewers can quickly identify the PR belonging to their module.

    ```
    <module_name> : <week_no> : <PR_Title>
    ```

    `<module_name> `- You only have to specify the module name in lowercase letters. For example, os-2, ac-2

    ` <week_no> `- Specify the week number in the PR title that is the week in which this task has been assigned to you.

    `<PR_Title> `- Specify the title of the PR starting with the lowercase letter of the first word.

- Don't add the changes made in the settings.py file regarding the database setup you have made in the local system and don't push the database dump file in the PR. These PRs won't be considered to be merged the respective module branch.


# Designing APIs

- All APIs services should only return data in `JSON format`. No other return types are compatible or treated correct.

- The response to every API call must return a corresponding status code along with a message/body. Refer to this [guide](https://restfulapi.net/http-status-codes/) for deciding the correct status code for each case.

- Use `underscores`, not camelCase, for variable, function and method names

    (i.e. poll.get_unique_voters(), not poll.getUniqueVoters()).

- Use `InitialCaps` for class names (or for factory functions that return classes).

- Use `camelCase` for defining API routes (i.e route/postNewRecord)

- Routes must be kept clear and consice to avoid any confusions.
    - If a given route allows more than one CRUD operations, they must not have differing names. The API method achieves that result for us.
    

# Designing Database

1. ### Correct Model Naming
    It is generally recommended to use singular nouns for model naming, for example: User, Post, Article. That is, the last component of the name should be a noun, e.g.: Some New Shiny Item. It is correct to use singular numbers when one unit of a model does not contain information about several objects.

2. ### Relationship Field Naming
    For relationships such as ForeignKey, OneToOneKey, ManyToMany it is sometimes better to specify a name. Imagine there is a model called Article, - in which one of the relationships is ForeignKey for model User. If this field contains information about the author of the article, then author will be a more appropriate name than user.

3. ### Correct Related-Name
    It is reasonable to indicate a related-name in plural as related-name addressing returns queryset. Please, do set adequate related-names. In the majority of cases, the name of the model in plural will be just right. For example:

    ```js
    class Owner(models.Model):
        pass
    class Item(models.Model):
        owner = models.ForeignKey(Owner, related_name='items')
    ```

4. ### Do not use ForeignKey with unique=True
    There is no point in using ForeignKey with unique=Trueas there exists OneToOneField for such cases.

5. ### Attributes and Methods Order in a Model
    Preferable attributes and methods order in a model (an empty string between the points).
    ```
    constants (for choices and other)
    fields of the model
    custom manager indication
    meta
    def _unicode_ (python 2) or def _str_ (python 3)
    other special methods
    def clean
    def save
    def get_absolut_url
    other methods
    ```

6. ### BooleanField
    Do not use null=True or blank=True for BooleanField. It should also be pointed out that it is better to specify default values for such fields. If you realise that the field can remain empty, you need NullBooleanField.

7. ### Redundant model name in a field name
    Do not add model names to fields if there is no need to do so, e.g. if table User has a field user_status - you should rename the field into status, as long as there are no other statuses in this model.