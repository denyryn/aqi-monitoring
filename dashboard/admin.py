from django.contrib import admin
from .models import PredictionRecord


@admin.register(PredictionRecord)
class PredictionRecordAdmin(admin.ModelAdmin):
    list_display = ("created_at", "predicted_class", "confidence", "no2", "co", "pm10", "pm25")
    list_filter = ("predicted_class", "created_at")
