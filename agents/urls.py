from django.urls import path


from .views import run_agent

urlpatterns = [
    path('', run_agent),
]