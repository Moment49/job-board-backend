import django_filters
from .models import JobCategory, JobPost, JobApplication


class JobPostFilter(django_filters.FilterSet):
    location = django_filters.CharFilter(method='filter_location', lookup_expr="iexact")
    work_type = django_filters.CharFilter(method='filter_work_type', lookup_expr="iexact")
    Industry = django_filters.CharFilter(method='filter_Industry', lookup_expr="iexact")

    job_title = django_filters.CharFilter(field_name="job_title", lookup_expr="iexact")
    salary = django_filters.NumberFilter(lookup_expr='exact')
    salary_gt = django_filters.NumberFilter(field_name='salary', lookup_expr='gte')
    salary_lt = django_filters.NumberFilter(field_name='salary', lookup_expr='lte')
    class Meta:
        model = JobPost
        fields = ['job_title', "salary", "salary_gt", "salary_lt", "job_category"]
    
    def filter_location(self, queryset, name, value):
        return queryset.filter(job_category__job_category_type="Location",
                               job_category__job_category_name=value)
    
    def filter_work_type(self, queryset, name, value):
        return queryset.filter(job_category__job_category_type="Work Type",
                               job_category__job_category_name=value)
    
    def filter_Industry(self, queryset, name, value):
        return queryset.filter(job_category__job_category_type="Industry",
                               job_category__job_category_name=value)

class JobApplicationFilter(django_filters.FilterSet):
    status = django_filters.CharFilter(method='filter_application_submission_status', lookup_expr='iexact')


    class Meta:
        model = JobApplication
        fields = []
    
    def filter_application_submission_status(self, queryset, name, value):
        return queryset.filter(
            job_app_submission_status__iexact=value
        )