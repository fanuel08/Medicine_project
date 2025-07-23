from django.db import models
from django.contrib.auth.models import User as AuthUser
from django.utils import timezone


# --- Lookup Tables (No changes here) ---

class Language(models.Model):
    """Stores supported languages for the system."""
    language_code = models.CharField(max_length=5, unique=True, help_text='e.g., en, sw')
    language_name = models.CharField(max_length=50, help_text='e.g., English, Swahili')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.language_name

class PaymentDeclaration(models.Model):
    """Stores the different payment declaration statuses."""
    status_code = models.CharField(max_length=20, unique=True, help_text='e.g., standard, small_fee, cannot_pay')
    description = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.description

# --- Core Application Models ---

class User(models.Model):
    """Represents the end-users (patients) interacting via USSD."""
    user_id = models.AutoField(primary_key=True)
    phone_number = models.CharField(max_length=20, unique=True, help_text='User phone number, primary identifier from USSD')
    default_language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True, blank=True)
    payment_declaration = models.ForeignKey(PaymentDeclaration, on_delete=models.SET_NULL, null=True, blank=True)
    otp = models.CharField(max_length=6, null=True, blank=True)
    otp_expiry = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.phone_number

class Agent(models.Model):
    """
    Represents the community agents who handle cases. Linked to a Django AuthUser.
    """
    user = models.OneToOneField(AuthUser, on_delete=models.CASCADE, primary_key=True, related_name='agent')
    full_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.full_name

class Case(models.Model):
    """Represents a single health case initiated by a User."""

    class CaseStatus(models.TextChoices):
        NEW = 'new', 'New'
        ASSIGNED = 'assigned_to_agent', 'Assigned to Agent'
        VIEWED = 'agent_viewed', 'Viewed by Agent'
        PAYMENT_PENDING = 'payment_pending', 'Payment Pending'
        PAID = 'paid', 'Paid'
        ACTION_TAKEN = 'agent_action_taken', 'Action Taken'
        REFERRED = 'referred', 'Referred'
        RESOLVED = 'resolved', 'Resolved'
        CLOSED = 'closed', 'Closed'
        FOLLOW_UP = 'needs_follow_up', 'Needs Follow-up'

    case_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cases')
    agent = models.ForeignKey(
        Agent,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_cases'
    )
    symptom_input = models.TextField(help_text='Raw text input from user via USSD')
    case_language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True, blank=True)
    case_payment_declaration = models.ForeignKey(PaymentDeclaration, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=CaseStatus.choices,
        default=CaseStatus.NEW
    )
    agent_notes = models.TextField(blank=True, null=True, help_text='Notes added by the agent via dashboard')
    checkout_request_id = models.CharField(max_length=100, blank=True, null=True)
    ai_summary = models.TextField(blank=True, null=True, help_text='AI-generated summary of symptoms')
    ai_urgency = models.CharField(max_length=20, blank=True, null=True, help_text='AI-assigned urgency label')
    ai_category = models.CharField(max_length=50, blank=True, null=True, help_text='AI-assigned health category')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Case {self.case_id} for {self.user.phone_number}"

# --- NEW MODELS FOR DASHBOARD FEATURES ---

class Payment(models.Model):
    """
    Stores a record of each successful M-Pesa transaction.
    """
    payment_id = models.AutoField(primary_key=True)
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    mpesa_receipt_number = models.CharField(max_length=50, unique=True)
    transaction_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.mpesa_receipt_number} for Case {self.case.case_id}"

class CaseHistory(models.Model):
    """
    Creates a timestamped log of all significant actions taken on a case.
    """
    history_id = models.AutoField(primary_key=True)
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='history')
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=255, help_text='A description of the event that occurred.')

    class Meta:
        ordering = ['-timestamp'] # Show the most recent events first

    def __str__(self):
        return f"{self.case.case_id} at {self.timestamp}: {self.description}"


class UssdMenuText(models.Model):
    """
    Stores the text for different USSD menu screens in multiple languages.
    """
    menu_key = models.CharField(max_length=50, help_text='A unique key for a menu, e.g., "welcome_menu"')
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    menu_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('menu_key', 'language')

    def __str__(self):
        return f"{self.menu_key} ({self.language.language_code})"