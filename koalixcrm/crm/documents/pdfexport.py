# -*- coding: utf-8 -*-

import os
from subprocess import check_output
from subprocess import STDOUT

from django.conf import settings
from django.contrib import auth
from django.core import serializers
from django.utils.translation import ugettext as _
from koalixcrm.crm.exceptions import *
from koalixcrm import djangoUserExtension
from koalixcrm.crm.contact.contact import Contact
from koalixcrm.crm.contact.contact import PostalAddressForContact
from koalixcrm.crm.contact.phoneaddress import PhoneAddress
from koalixcrm.crm.contact.emailaddress import EmailAddress
from koalixcrm.crm.contact.postaladdress import PostalAddress
from koalixcrm.crm.product.currency import Currency
from koalixcrm.crm.product.unit import Unit
from koalixcrm.crm.product.product import Product
from koalixcrm.crm.documents.quote import Quote
from koalixcrm.crm.documents.invoice import Invoice
from lxml import etree
import koalixcrm.crm.documents.salescontractposition
import koalixcrm.crm.documents.purchaseorder


class PDFExport:

    def createPDF(object_to_create_pdf):
        if (type(object_to_create_pdf) == Quote) or (type(object_to_create_pdf) == Invoice):
            position_class = koalixcrm.crm.documents.salescontractposition.SalesContractPosition
            export_customer = True
            export_supplier = False
        else:
            position_class = koalixcrm.crm.documents.purchaseorder.PurchaseOrderPosition
            export_customer = False
            export_supplier = True

        file_with_serialized_xml = str(object_to_create_pdf) + ".xml"
        file_output_pdf = str(object_to_create_pdf) + ".pdf"

        XMLSerializer = serializers.get_serializer("xml")
        xml_serializer = XMLSerializer()
        out = open(os.path.join(settings.PDF_OUTPUT_ROOT, file_with_serialized_xml), "wb")
        objects_to_serialize = list(type(object_to_create_pdf).objects.filter(id=object_to_create_pdf.id))
        if export_supplier:
            objects_to_serialize += list(Contact.objects.filter(id=object_to_create_pdf.supplier.id))
        if export_customer:
            objects_to_serialize += list(Contact.objects.filter(id=object_to_create_pdf.customer.id))
        objects_to_serialize += list(Currency.objects.filter(id=object_to_create_pdf.currency.id))
        objects_to_serialize += list(position_class.objects.filter(contract=object_to_create_pdf.id))
        for position in list(position_class.objects.filter(contract=object_to_create_pdf.id)):
            objects_to_serialize += list(koalixcrm.crm.documents.salescontractposition.Position.objects.filter(id=position.id))
            objects_to_serialize += list(Product.objects.filter(id=position.product.id))
            objects_to_serialize += list(Unit.objects.filter(id=position.unit.id))
        objects_to_serialize += list(auth.models.User.objects.filter(id=object_to_create_pdf.staff.id))
        userExtension = djangoUserExtension.models.UserExtension.objects.filter(user=object_to_create_pdf.staff.id)
        if len(userExtension) == 0:
            raise UserExtensionMissing(_("During PurchaseOrder PDF Export"))
        phone_address = djangoUserExtension.models.UserExtensionPhoneAddress.objects.filter(
            userExtension=userExtension[0].id)
        if len(phone_address) == 0:
            raise UserExtensionPhoneAddressMissing(_("During PurchaseOrder PDF Export"))
        email_address = djangoUserExtension.models.UserExtensionEmailAddress.objects.filter(
            userExtension=userExtension[0].id)
        if len(email_address) == 0:
            raise UserExtensionEmailAddressMissing(_("During PurchaseOrder PDF Export"))
        objects_to_serialize += list(userExtension)
        objects_to_serialize += list(EmailAddress.objects.filter(id=email_address[0].id))
        objects_to_serialize += list(PhoneAddress.objects.filter(id=phone_address[0].id))
        template_set = djangoUserExtension.models.TemplateSet.objects.filter(
            id=userExtension[0].defaultTemplateSet.id)
        if len(template_set) == 0:
            raise TemplateSetMissing(_("During PurchaseOrder PDF Export"))
        objects_to_serialize += list(template_set)
        objects_to_serialize += list(auth.models.User.objects.filter(id=object_to_create_pdf.lastmodifiedby.id))
        if export_customer:
            objects_to_serialize += list(PostalAddressForContact.objects.filter(person=object_to_create_pdf.customer.id))
            for address in list(PostalAddressForContact.objects.filter(person=object_to_create_pdf.customer.id)):
                objects_to_serialize += list(PostalAddress.objects.filter(id=address.id))
        if export_supplier:
            objects_to_serialize += list(PostalAddressForContact.objects.filter(person=object_to_create_pdf.supplier.id))
            for address in list(PostalAddressForContact.objects.filter(person=object_to_create_pdf.supplier.id)):
                objects_to_serialize += list(PostalAddress.objects.filter(id=address.id))
        xml_serializer.serialize(objects_to_serialize, stream=out, indent=3)
        out.close()
        xml = etree.parse(os.path.join(settings.PDF_OUTPUT_ROOT, file_with_serialized_xml))
        rootelement = xml.getroot()
        filebrowserdirectory = etree.SubElement(rootelement, "filebrowserdirectory")
        filebrowserdirectory.text = settings.MEDIA_ROOT
        xml.write(os.path.join(settings.PDF_OUTPUT_ROOT, file_with_serialized_xml))
        check_output(
            [settings.FOP_EXECUTABLE, '-c', userExtension[0].defaultTemplateSet.fopConfigurationFile.path_full,
             '-xml',
             os.path.join(settings.PDF_OUTPUT_ROOT, file_with_serialized_xml), '-xsl',
             userExtension[0].defaultTemplateSet.purchaseorderXSLFile.xslfile.path_full, '-pdf',
             os.path.join(settings.PDF_OUTPUT_ROOT, file_output_pdf)], stderr=STDOUT)
        return os.path.join(settings.PDF_OUTPUT_ROOT, file_output_pdf)
