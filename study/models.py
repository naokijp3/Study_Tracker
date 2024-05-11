# study/models.py

from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class StudyLog(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)

    def duration_in_minutes(self):
        if self.end_time:
            duration = (self.end_time - self.start_time).total_seconds() / 60
            return round(duration, 2)
        return None

    def __str__(self):
        return f'{self.category} - {self.start_time} to {self.end_time}'

class StudyGoal(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    target_minutes = models.FloatField()

    def __str__(self):
        return f'{self.category} - {self.target_minutes} 分'