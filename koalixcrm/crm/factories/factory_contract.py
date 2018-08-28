# -*- coding: utf-8 -*-

import factory
from koalixcrm.crm.models import Contract
from koalixcrm.crm.factories.factory_user import StaffUserFactory
from koalixcrm.crm.factories.factory_customer import StandardCustomerFactory
from koalixcrm.crm.factories.factory_supplier import StandardSupplierFactory
from koalixcrm.crm.factories.factory_currency import StandardCurrencyFactory
from koalixcrm.djangoUserExtension.factories import StandardDefaultTemplateSet


class StandardContractFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Contract

    staff = factory.SubFactory(StaffUserFactory)
    description = "This is the description to a test contract"
    default_customer = factory.SubFactory(StandardCustomerFactory)
    default_supplier = factory.SubFactory(StandardSupplierFactory)
    default_currency = factory.SubFactory(StandardCurrencyFactory)
    default_template_set = factory.SubFactory(StandardDefaultTemplateSet)
    date_of_creation = "2018-05-01"
    last_modification = "2018-05-03"
    last_modified_by = factory.SubFactory(StaffUserFactory)
