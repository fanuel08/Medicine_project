from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import ListAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import status  # <-- Add this new import for HTTP status codes

from .models import Language, User, PaymentDeclaration, Case,  UssdMenuText
from .serializers import CaseSerializer, CurrentUserSerializer # Add CurrentUserSerializer


# --- View for the USSD Handler ---
class UssdHandlerView(APIView):
    """
    This view handles all the USSD requests from the gateway.
    It now fetches menu text dynamically from the database.
    """
    def get_menu_text(self, key, language_code='en'):
        """Helper function to get menu text from the database."""
        try:
            # Try to get the text in the user's chosen language
            menu = UssdMenuText.objects.get(menu_key=key, language__language_code=language_code)
            return menu.menu_text
        except UssdMenuText.DoesNotExist:
            # If it doesn't exist, fall back to English
            try:
                menu = UssdMenuText.objects.get(menu_key=key, language__language_code='en')
                return menu.menu_text
            except UssdMenuText.DoesNotExist:
                # If English also doesn't exist, return a default error message
                return "Error: Menu not configured. Please contact support."

    def post(self, request, *args, **kwargs):
        session_id = request.data.get('sessionId')
        phone_number = request.data.get('phoneNumber')
        text = request.data.get('text', '')

        user, created = User.objects.get_or_create(phone_number=phone_number)
        response = ""
        text_parts = text.split('*')

        # Determine the user's language preference
        lang_code = user.default_language.language_code if user.default_language else 'en'

        # --- Refactored Menu Logic ---

        if text == '':
            # Level 0: Welcome menu
            response = self.get_menu_text('welcome_menu', 'en') # Always show language choice in a common format

        elif text_parts[0] in ['1', '2'] and len(text_parts) == 1:
            # Level 1: Language selected
            lang_code = 'en' if text_parts[0] == '1' else 'sw'
            language = Language.objects.get(language_code=lang_code)
            user.default_language = language
            user.save()

            response = self.get_menu_text('payment_declaration_menu', lang_code)

        elif text_parts[0] in ['1', '2'] and len(text_parts) == 2 and text_parts[1] in ['1', '2', '3']:
            # Level 2: Payment declared
            declaration_map = {'1': 'standard', '2': 'small_fee', '3': 'cannot_pay'}
            status_code = declaration_map.get(text_parts[1])
            payment_declaration = PaymentDeclaration.objects.get(status_code=status_code)
            user.payment_declaration = payment_declaration
            user.save()

            response = self.get_menu_text('enter_symptom_menu', lang_code)

        elif text_parts[0] in ['1', '2'] and len(text_parts) == 3:
            # Level 3: Health issue submitted
            health_issue = text_parts[2]

            new_case = Case.objects.create(
                user=user,
                symptom_input=health_issue,
                case_language=user.default_language,
                case_payment_declaration=user.payment_declaration
            )

            # Format the final response message with the case ID
            final_message_template = self.get_menu_text('case_created_success', lang_code)
            response = final_message_template.format(case_id=new_case.case_id)

        else:
            # Invalid input
            response = self.get_menu_text('invalid_selection_menu', lang_code)

        return Response(response, content_type='text/plain')


# --- Agent API Views ---
class CaseListView(ListAPIView):
    queryset = Case.objects.all().order_by('-created_at')
    serializer_class = CaseSerializer
    permission_classes = [IsAuthenticated]

class CaseDetailView(RetrieveUpdateAPIView):
    queryset = Case.objects.all()
    serializer_class = CaseSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'

# --- Custom Views for Debugging Agent Login ---
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        print("\n--- Manual Authentication Check ---")
        print(f"Attempting to authenticate user: '{username}'")

        user = authenticate(username=username, password=password)

        if user is not None:
            print(">>> SUCCESS: Django authenticate() found a valid user.")
        else:
            print(">>> FAILURE: Django authenticate() returned None. Check username/password/active status.")

        print("-----------------------------------\n")

        data = super().validate(attrs)
        return data

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer



class ClaimCaseView(APIView):
    """
    This view allows a logged-in agent to assign a case to themselves.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk, *args, **kwargs):
        try:
            # Find the case by its primary key (pk)
            case_to_claim = Case.objects.get(pk=pk)
        except Case.DoesNotExist:
            # If the case doesn't exist, return a 404 Not Found error
            return Response({"detail": "Case not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check if the case is already assigned to an agent
        if case_to_claim.agent is not None:
            # If it's already assigned, return an error
            return Response(
                {"detail": f"Case already assigned to agent {case_to_claim.agent.username}."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Assign the case to the current logged-in user (who is an agent)
        # request.user is the authenticated user object from the token
        case_to_claim.agent = request.user
        case_to_claim.status = 'assigned_to_agent' # Update the status
        case_to_claim.save()

        # Return a success message
        return Response({"detail": "Case successfully claimed."}, status=status.HTTP_200_OK)

    # 3. Add this new view class at the BOTTOM of the file
class CurrentUserView(APIView):
    """
    Provides the details of the currently authenticated user (agent).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # request.user is the authenticated user instance from the token
        serializer = CurrentUserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


