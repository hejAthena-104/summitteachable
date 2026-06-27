from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import CopyRelationship, MasterTrader


@login_required
def traders(request):
    """Grid of active master traders available to copy."""
    traders_qs = MasterTrader.objects.filter(is_active=True)
    copied_ids = set(
        CopyRelationship.objects.filter(
            user=request.user, is_active=True
        ).values_list("master_id", flat=True)
    )
    return render(
        request,
        "copytrading/traders.html",
        {"traders": traders_qs, "copied_ids": copied_ids},
    )


@login_required
@require_POST
def copy(request, slug):
    """Start or re-activate a copy relationship."""
    master = get_object_or_404(MasterTrader, slug=slug, is_active=True)

    raw_amount = request.POST.get("allocated_demo_amount", "0")
    try:
        amount = Decimal(raw_amount)
    except (InvalidOperation, TypeError):
        amount = Decimal("0")
    if amount < 0:
        amount = Decimal("0")

    relationship, created = CopyRelationship.objects.get_or_create(
        user=request.user,
        master=master,
        is_active=True,
        defaults={"allocated_demo_amount": amount},
    )
    if not created:
        # Already copying; update the allocation.
        relationship.allocated_demo_amount = amount
        relationship.save(update_fields=["allocated_demo_amount"])

    messages.success(
        request,
        f"You're now copying {master.name}.",
    )
    return redirect("copytrading:my_copies")


@login_required
def my_copies(request):
    """List the user's active copy relationships."""
    relationships = (
        CopyRelationship.objects.filter(user=request.user, is_active=True)
        .select_related("master")
    )
    return render(
        request,
        "copytrading/my_copies.html",
        {"relationships": relationships},
    )


@login_required
@require_POST
def stop(request, pk):
    """Stop a copy relationship."""
    relationship = get_object_or_404(
        CopyRelationship, pk=pk, user=request.user, is_active=True
    )
    relationship.is_active = False
    relationship.stopped_at = timezone.now()
    relationship.save(update_fields=["is_active", "stopped_at"])
    messages.info(
        request,
        f"You've stopped copying {relationship.master.name}.",
    )
    return redirect("copytrading:my_copies")
