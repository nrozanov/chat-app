import factory

from config.settings import settings
from core import s3
from models.user import User
from models.customer import Customer
from models.chat import Chat, ChatMessage
from tests.session import TestSession
from tests import factories


class BaseFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        abstract = True
        sqlalchemy_session = TestSession
        sqlalchemy_session_persistence = "commit"


class UserFactory(BaseFactory):
    email = factory.Sequence(lambda n: f"{n}@test.com")
    phone_number = factory.Sequence(lambda n: f"+7915000000{n}")

    last_login = None

    class Meta:
        model = User

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        return super()._create(model_class, *args, **kwargs)


class CustomerFactory(BaseFactory):
    name = factory.Faker("first_name")
    zip_code = "12345"
    bio = factory.Faker("sentence")
    occupation = factory.Faker("sentence")

    user = factory.SubFactory(UserFactory)

    class Meta:
        model = Customer


class ChatFactory(BaseFactory):
    customer_relation = factory.SubFactory(CustomerRelationFactory)

    class Meta:
        model = Chat


class ChatMessageFactory(BaseFactory):
    message = factory.Faker("sentence")
    is_from_from_customer = True

    chat = factory.SubFactory(ChatFactory)

    class Meta:
        model = ChatMessage
