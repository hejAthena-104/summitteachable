def education_unlocked(user):
    """Academy access is gated behind an approved deposit."""
    return bool(user.is_authenticated and user.total_deposited > 0)
