from django.db import models

class AgentLog(models.Model):
    user_input = models.TextField()
    keywords = models.JSONField()
    response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Query at {self.timestamp}"