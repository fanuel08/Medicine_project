# In api/auto_assign.py

from .models import Agent, Case
from django.db.models import Count, Q

def auto_assign_case(case):
    """
    Finds the active agent with the fewest open cases and assigns
    the new case to them. If there's a tie, it assigns to the agent
    who was created earliest to ensure fair distribution.
    """
    try:
        # Define which statuses are considered "open" for counting workload
        open_statuses = [
            Case.CaseStatus.NEW,
            Case.CaseStatus.ASSIGNED,
            Case.CaseStatus.VIEWED,
            Case.CaseStatus.NEEDS_FOLLOW_UP
        ]

        # Get active agents and count their open cases efficiently.
        active_agents = Agent.objects.filter(user__is_active=True).annotate(
            open_cases=Count('assigned_cases', filter=Q(assigned_cases__status__in=open_statuses))
        )

        if not active_agents:
            print("AUTO-ASSIGN: No active agents available.")
            return

        # ✅ IMPROVED: First, order by the number of open cases (fewest first).
        # Then, use the agent's creation date as a tie-breaker for a fair round-robin style.
        least_busy_agent = active_agents.order_by('open_cases', 'created_at').first()

        # Assign the 'Agent' object itself to the case's agent field.
        case.agent = least_busy_agent
        case.status = Case.CaseStatus.ASSIGNED
        case.save()

        # Log the assignment for the case history
        from .models import CaseHistory
        CaseHistory.objects.create(case=case, description=f"Case automatically assigned to agent {least_busy_agent.full_name}.")

        print(f"AUTO-ASSIGN: Case {case.case_id} assigned to agent {least_busy_agent.full_name}.")

    except Exception as e:
        print(f"AUTO-ASSIGN: An error occurred during auto-assignment: {e}")