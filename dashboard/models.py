from django.db import models


class PredictionRecord(models.Model):
    no2 = models.FloatField(verbose_name="NO₂ (ppm)")
    co = models.FloatField(verbose_name="CO (ppm)")
    pm10 = models.FloatField(verbose_name="PM₁₀ (µg/m³)")
    pm25 = models.FloatField(verbose_name="PM₂.₅ (µg/m³)")

    predicted_class = models.CharField(max_length=64)
    confidence = models.FloatField()
    probabilities = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.predicted_class} @ {self.created_at:%Y-%m-%d %H:%M}"
