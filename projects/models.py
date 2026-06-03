from django.db import models
from django.contrib.auth import get_user_model
from customers.models import Customer
from django.utils.translation import gettext_lazy as _
from datetime import date

User = get_user_model()

class Project(models.Model):
    STATUS_CHOICES = [
        ('PENDING', _('Pending ')),
        ('STARTED', _('Started ')),
        ('ON_WORK', _('On Work ')),
        ('FINISHED', _('Finished ')),
    ]

    TYPE_CHOICES = [
        ('WEB_APP', _('Web Application')),
        ('MOBILE_APP', _('Mobile Application')),
        ('UI_UX', _('UI/UX Design')),
        ('API_DEV', _('API Development')),
        ('OTHER', _('Other ')),
    ]

    name = models.CharField(max_length=255, verbose_name=_('Project Name'))
    project_type = models.CharField(max_length=50, choices=TYPE_CHOICES, default='WEB_APP')    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='projects')    
    employees = models.ManyToManyField(User, related_name='assigned_projects')
    start_date = models.DateField(verbose_name=_('Start Date'))
    end_date = models.DateField(verbose_name=_('End Date'))    
    description = models.TextField(verbose_name=_('Description'))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def duration_in_days(self):
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days
        return 0

    def __str__(self):
        return f"{self.name} - {self.customer.name}"


class ProjectTask(models.Model):
    TASK_STATUS = [
        ('ON_SCHADUEL', _('On Schaduel')),
        ('IN_PROGRESS', _('In Progress')),
        ('DONE', _('Done')),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=255, help_text=_("e.g., Step 1: Meet with customer"))
    description = models.TextField(blank=True, null=True)    
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='specific_tasks')    
    status = models.CharField(max_length=20, choices=TASK_STATUS, default='ON_SCHADUEL')
    order = models.PositiveIntegerField(default=1, help_text=_("Step number  1,2,3,......")) 

    def __str__(self):
        return f"{self.project.name} - Task: {self.title}"


class ProjectComment(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='comments')    
    user = models.ForeignKey(User, on_delete=models.CASCADE)    
    content = models.TextField(verbose_name=_('Message / Comment Content'))    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.username} on {self.project.name}"