from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from django.contrib.postgres.fields import ArrayField
from django.utils.translation import gettext_lazy as _

class Customer (models.Model):
    CUSTOMER_TYPE = [
            ('COMPANY', _('Company')),
            ('SCHOOL', _('School')),
            ('UNIVERSITY', _('University')),
            ('GOVERNMENT', _('Government')),
            ('CHILDREN', _('Children Facility')),
            ('HOMELESS', _('Homeless Shelter')),
            ('ORGANIZATION',_('organization'))
        ]
    customer_type = models.CharField( max_length=20,  choices=CUSTOMER_TYPE,  default='COMPANY',  verbose_name=_('Customer Type')
    )
    name = models.CharField(max_length=127, null=False, blank=False, verbose_name=_('Customer Name'))
    email = models.EmailField(unique=False, null=False, blank=False, verbose_name=_('Email Address'))
    street = models.CharField(max_length=253, null=False, blank=False, verbose_name=_('Street Name'))
    post_number = models.CharField(max_length=11, null=True, blank=True, verbose_name=_('Postal Code'))    
    phone_number = PhoneNumberField(region='DE', null=False, blank=False, verbose_name=_('Phone Number'))    
    services = ArrayField(
        models.CharField(max_length=63, null=False, blank=False), 
        blank=True, 
        null=True,
        verbose_name=_('Services'),
        help_text=_("Example: ['Cleaning', 'Security', 'Web App']")
    )

    def __str__(self):
        return f"{self.name} - {self.get_customer_type_display()}"