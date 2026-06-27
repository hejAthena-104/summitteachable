def education_unlocked(user):
    """Academy access is gated behind a DEMO deposit (play money). Any approved
    demo deposit unlocks every course."""
    return bool(user.is_authenticated and user.total_deposited > 0)
