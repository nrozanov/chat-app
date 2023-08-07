from pytest_factoryboy import LazyFixture, register

from tests import factories

register(factories.UserFactory)
register(factories.UserFactory, "other_user")
register(factories.CustomerFactory)
register(factories.CustomerFactory, "other_customer", user=LazyFixture("other_user"))
register(factories.CustomerPhotoFactory)
register(factories.ContentReactionFactory)
register(factories.CustomerRelationFactory)
register(factories.CustomerRelationContentLinkFactory)
register(factories.ChatFactory)
register(factories.ChatMessageFactory)
register(factories.ConnectionRequestFactory)
register(factories.CustomerReportFactory)
register(factories.ConnectionRequestContentLinkFactory)
