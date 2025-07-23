from rest_framework import serializers
# MODIFIED: Import the new models
from .models import Case, User, Agent, Payment, CaseHistory
from .auto_assign import auto_assign_case
from django.contrib.auth.models import User as AuthUser
from .ai_service import get_ai_triage_for_symptoms


# --- User Serializer ---
class UserSerializer(serializers.ModelSerializer):
    """Serializer to represent the User model (for USSD users)."""
    class Meta:
        model = User
        fields = ['phone_number', 'default_language']


# --- Agent Serializer ---
class AgentSerializer(serializers.ModelSerializer):
    """Serializer to represent the Agent model."""
    class Meta:
        model = Agent
        fields = ['full_name', 'phone_number']


# In api/serializers.py

class CaseSerializer(serializers.ModelSerializer):
    """
    Serializer to represent the Case model. Now handles creation from the web correctly.
    """
    # This field will be populated by the view during creation
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    agent = serializers.StringRelatedField(read_only=True)
    case_language = serializers.StringRelatedField(read_only=True)
    case_payment_declaration = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Case
        fields = [
            'case_id', 'user', 'agent', 'symptom_input', 'case_language',
            'case_payment_declaration', 'status', 'agent_notes', 'created_at',
            'updated_at',
            'ai_urgency', 'ai_category', 'ai_summary',
        ]
        # 'user' is now handled by the view, so we don't need it in read_only_fields
        read_only_fields = [
            'case_id', 'agent', 'case_language',
            'case_payment_declaration', 'created_at', 'updated_at', 'ai_urgency',
            'ai_category', 'ai_summary',
        ]

    def create(self, validated_data):
        """
        Creates the case, then calls the AI service to generate triage data,
        and finally calls the auto-assign function.
        """
        # First, create the case object
        case = super().create(validated_data)

        # ✅ NEW: Call the AI service with the symptom input
        if case.symptom_input:
            ai_data = get_ai_triage_for_symptoms(case.symptom_input)
            case.ai_urgency = ai_data.get("ai_urgency")
            case.ai_category = ai_data.get("ai_category")
            case.ai_summary = ai_data.get("ai_summary")
            case.save()

        # Then, auto-assign the case to an agent
        auto_assign_case(case)
        return case
# --- Current User Serializer ---
class CurrentUserSerializer(serializers.ModelSerializer):
    """
    Serializer for the current user. Safely includes agent-specific details.
    """
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = AuthUser
        fields = ['id', 'username', 'email', 'full_name', 'is_active', 'is_staff']

    def get_full_name(self, obj):
        if hasattr(obj, 'agent'):
            return obj.agent.full_name
        return obj.username


# --- Agent Registration Serializer ---
class AgentRegisterSerializer(serializers.ModelSerializer):
    """Handles new agent registration, including the new phone_number field."""
    full_name = serializers.CharField(write_only=True, required=True)
    phone_number = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(required=True)

    class Meta:
        model = AuthUser
        fields = ['username', 'password', 'full_name', 'email', 'phone_number']
        extra_kwargs = {'password': {'write_only': True}}

    def validate_email(self, value):
        """Check that the email is not already in use (case-insensitive)."""
        if AuthUser.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def create(self, validated_data):
        """Creates the AuthUser and the linked Agent profile."""
        print("✅ REGISTRATION DATA RECEIVED BY SERVER:", validated_data)

        try:
            full_name = validated_data.pop('full_name')
            phone_number = validated_data.pop('phone_number')
        except KeyError as e:
            raise serializers.ValidationError({str(e): "This field is required."})

        user = AuthUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            is_active=False
        )

        Agent.objects.create(user=user, full_name=full_name, phone_number=phone_number)
        return user

# --- NEW SERIALIZERS FOR DASHBOARD FEATURES ---

class PaymentSerializer(serializers.ModelSerializer):
    """
    Serializer for the Payment model, for the payment history tab.
    """
    class Meta:
        model = Payment
        fields = ['case', 'amount', 'mpesa_receipt_number', 'transaction_date']

class CaseHistorySerializer(serializers.ModelSerializer):
    """
    Serializer for the CaseHistory model, for the case timeline feature.
    """
    class Meta:
        model = CaseHistory
        fields = ['timestamp', 'description']