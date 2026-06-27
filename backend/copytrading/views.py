from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import CopyRelationship, MasterTrader


@login_required
def traders(request):
    """Grid of active demo master traders available to copy (simulated)."""
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
    """
    Start (or re-activate) a SIMULATED copy relationship.

    HARD CONSTRAINT: this only stores a demo allocation. No real balance is
    moved — request.user.balance is never touched.
    """
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
        # Already copying — just update the simulated allocation.
        relationship.allocated_demo_amount = amount
        relationship.save(update_fields=["allocated_demo_amount"])

    messages.success(
        request,
        f"You're now copying {master.name} on your DEMO account (simulated). "
        f"No real money has been moved.",
    )
    return redirect("copytrading:my_copies")


@login_required
def my_copies(request):
    """List the user's active simulated copy relationships."""
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
    """Stop a simulated copy relationship. No real funds involved."""
    relationship = get_object_or_404(
        CopyRelationship, pk=pk, user=request.user, is_active=True
    )
    relationship.is_active = False
    relationship.stopped_at = timezone.now()
    relationship.save(update_fields=["is_active", "stopped_at"])
    messages.info(
        request,
        f"You've stopped copying {relationship.master.name} (demo).",
    )
    return redirect("copytrading:my_copies")
