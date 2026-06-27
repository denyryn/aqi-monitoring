from datetime import datetime, timezone

from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Count
from django.views.decorators.csrf import csrf_exempt
from .ml import predict
from .models import PredictionRecord


def index(request):
    records = PredictionRecord.objects.all()
    recent_records = records[:10]
    dist = list(
        records.values("predicted_class")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    today = datetime.now(tz=timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    trend_qs = records.filter(created_at__gte=today)[:50]
    trend_labels = [r.created_at.strftime("%H:%M") for r in trend_qs]
    trend_conf = [r.confidence for r in trend_qs]

    top_class = dist[0]["predicted_class"] if dist else "—"

    return render(request, "dashboard/index.html", {
        "active_tab": "dashboard",
        "total": records.count(),
        "recent_records": recent_records,
        "last": records.first(),
        "top_class": top_class,
        "dist_labels": [d["predicted_class"] for d in dist],
        "dist_counts": [d["count"] for d in dist],
        "trend_labels": trend_labels,
        "trend_conf": trend_conf,
    })


@csrf_exempt
def predict_view(request):
    result = None
    error = None
    input_vals = {"no2": "", "co": "", "pm10": "", "pm25": ""}

    if request.method == "POST":
        try:
            for k in input_vals:
                input_vals[k] = request.POST.get(k, "").strip()
            no2 = float(input_vals["no2"])
            co = float(input_vals["co"])
            pm10 = float(input_vals["pm10"])
            pm25 = float(input_vals["pm25"])

            pred = predict(no2, co, pm10, pm25)

            PredictionRecord.objects.create(
                no2=no2, co=co, pm10=pm10, pm25=pm25,
                predicted_class=pred["class_name"],
                confidence=pred["confidence"],
                probabilities=pred["probabilities"],
            )

            result = pred
            result["confidence_pct"] = round(pred["confidence"] * 100, 1)
            result["probabilities_pct"] = {
                k: round(v * 100, 1) for k, v in pred["probabilities"].items()
            }
        except ValueError as e:
            error = str(e)
        except Exception as e:
            error = f"Inference error: {e}"

    return render(request, "dashboard/predict.html", {
        "active_tab": "predict",
        "result": result,
        "error": error,
        "input": input_vals,
    })


def history(request):
    records = PredictionRecord.objects.all()
    paginator = Paginator(records, 25)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "dashboard/history.html", {"active_tab": "history", "page": page})
