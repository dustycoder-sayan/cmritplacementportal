import django_filters as filters
from .models import *

class SPADFilter(filters.FilterSet):
    # Filters for Students model
    usn = filters.CharFilter(field_name='usn', lookup_expr='icontains')
    student_name = filters.CharFilter(field_name='student__name', lookup_expr='icontains')
    branch = filters.CharFilter(field_name='branch', lookup_expr='icontains')
    currentBacklogs = filters.NumberFilter(field_name='spf__currentBacklogs', lookup_expr='lte')
    degreeCgpa = filters.NumberFilter(field_name='spf__degreeCgpa', lookup_expr='gte')


    class Meta:
        model = Students
        fields = ['usn', 'student_name', 'branch', 'currentBacklogs', 'degreeCgpa']
    