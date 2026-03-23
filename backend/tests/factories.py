import factory
from django.utils import timezone

from apps.users.models import User
from apps.projects.models import Comment, Issue, Label, Project, Sprint
from apps.todos.models import DailyPlan, DailyPlanItem, PersonalTodo


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"testuser{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    password = factory.PostGenerationMethodCall("set_password", "testpass123")


class LabelFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Label

    name = factory.Sequence(lambda n: f"label-{n}")
    color = "#3B82F6"


class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Project

    name = factory.Sequence(lambda n: f"Projekt {n}")
    key = factory.Sequence(lambda n: f"PRJ{n}")
    owner = factory.SubFactory(UserFactory)
    status = Project.Status.ACTIVE


class SprintFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Sprint

    project = factory.SubFactory(ProjectFactory)
    name = factory.Sequence(lambda n: f"Sprint {n}")
    status = Sprint.Status.ACTIVE


class IssueFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Issue

    project = factory.SubFactory(ProjectFactory)
    title = factory.Sequence(lambda n: f"Issue {n}")
    key = factory.LazyAttribute(lambda obj: f"{obj.project.key}-{Issue.objects.filter(project=obj.project).count() + 1}")
    issue_type = Issue.IssueType.TASK
    priority = Issue.Priority.MEDIUM


class CommentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Comment

    issue = factory.SubFactory(IssueFactory)
    author = factory.SubFactory(UserFactory)
    body = factory.Faker("paragraph")


class PersonalTodoFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PersonalTodo

    user = factory.SubFactory(UserFactory)
    title = factory.Sequence(lambda n: f"Aufgabe {n}")
    priority = PersonalTodo.Priority.MEDIUM
    status = PersonalTodo.Status.PENDING


class DailyPlanFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DailyPlan

    user = factory.SubFactory(UserFactory)
    date = factory.LazyFunction(lambda: timezone.now().date())
