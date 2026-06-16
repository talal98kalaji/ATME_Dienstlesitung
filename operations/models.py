from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from customers.models import Customer

User = get_user_model()


class Site(models.Model):
    """Cleaning / Security work is carried out."""

    SITE_TYPE = [
        ('BUILDING', _('Building')),
        ('COMPANY', _('Company')),
        ('SCHOOL', _('School')),
        ('UNIVERSITY', _('University')),
        ('GOVERNMENT', _('Government')),
        ('HOSPITAL', _('Hospital')),
        ('OTHER', _('Other')),
    ]

    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sites',
        verbose_name=_('Customer'),
    )
    name = models.CharField(max_length=255, verbose_name=_('Site Name'))
    site_type = models.CharField(max_length=20, choices=SITE_TYPE, default='BUILDING', verbose_name=_('Site Type'))

    street = models.CharField(max_length=255, verbose_name=_('Street Name'))
    house_number = models.CharField(max_length=10, blank=True, verbose_name=_('House Number'))
    post_number = models.CharField(max_length=10, blank=True, verbose_name=_('Postal Code'))
    city = models.CharField(max_length=100, blank=True, verbose_name=_('City'))

    # Optional geo-coordinates (useful later for attendance / check-in)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name=_('Latitude'))
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name=_('Longitude'))

    is_active = models.BooleanField(default=True, verbose_name=_('Active'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Site')
        verbose_name_plural = _('Sites')

    def __str__(self):
        return f"{self.name} ({self.get_site_type_display()})"


class Assignment(models.Model):
    """Links an employee (Cleaner / Security) to a Site."""

    SERVICE_CHOICES = [
        ('CLEANING', _('Cleaning')),
        ('SECURITY', _('Security')),
    ]

    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='assignments', verbose_name=_('Site'))
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='site_assignments', verbose_name=_('Employee'))
    service_type = models.CharField(max_length=20, choices=SERVICE_CHOICES, verbose_name=_('Service Type'))

    start_date = models.DateField(null=True, blank=True, verbose_name=_('Start Date'))
    end_date = models.DateField(null=True, blank=True, verbose_name=_('End Date'))
    is_active = models.BooleanField(default=True, verbose_name=_('Active'))
    notes = models.TextField(blank=True, null=True, verbose_name=_('Notes'))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Assignment')
        verbose_name_plural = _('Assignments')

    def __str__(self):
        return f"{self.employee.username} -> {self.site.name} ({self.get_service_type_display()})"
