# Contributor Covenant Code of Conduct

All the contributors need to strictly follow this Code of Conduct to provide smooth rendering and workflow of the contributions inside Fusion repository. Here are certain guidelines you need to follow in order to make relevant changes in the repo:

## Designing APIs

- All APIs services should only return data in **JSON format**. No other return types are compatible or treated correct.

- The response to every API call must return a corresponding status code along with a message/body. Refer to this [guide](https://restfulapi.net/http-status-codes/) for deciding the correct status code for each case.

- Use **underscores**, not camelCase, for variable, function and method names

    (i.e. `poll.get_unique_voters()`, not `poll.getUniqueVoters()`).

- Use **InitialCaps** for class names (or for factory functions that return classes).

- Use **camelCase** for defining API routes (i.e `route/postNewRecord`)

- Routes must be kept clear and consice to avoid any confusions.
    - If a given route allows more than one CRUD operations, they must not have differing names. The API method achieves that result for us.
    

## Designing Database

1. ### Correct Model Naming
    It is generally recommended to use singular nouns for model naming, for example: User, Post, Article. That is, the last component of the name should be a noun, e.g.: Some New Shiny Item. It is correct to use singular numbers when one unit of a model does not contain information about several objects.

2. ### Relationship Field Naming
    For relationships such as ForeignKey, OneToOneKey, ManyToMany it is sometimes better to specify a name. Imagine there is a model called Article, - in which one of the relationships is ForeignKey for model User. If this field contains information about the author of the article, then author will be a more appropriate name than user.

3. ### Correct Related-Name
    It is reasonable to indicate a related-name in plural as related-name addressing returns queryset. Please, do set adequate related-names. In the majority of cases, the name of the model in plural will be just right. For example:

    ```python
    class Owner(models.Model):
        pass
    class Item(models.Model):
        owner = models.ForeignKey(Owner, related_name='items')
    ```

4. ### Do not use ForeignKey with unique=True
    There is no point in using ForeignKey with unique=Trueas there exists OneToOneField for such cases.

5. ### Attributes and Methods Order in a Model
    Preferable attributes and methods order in a model (an empty string between the points).
    ```python
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