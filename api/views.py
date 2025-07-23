# Add these imports for OTP logic
import random
from datetime import timedelta
from django.utils import timezone
from django.shortcuts import render
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import RetrieveUpdateAPIView, ListCreateAPIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import status, generics
from django.contrib.auth.models import User as AuthUser
from django.http import JsonResponse
from rest_framework import serializers
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view

from .daraja_service import initiate_stk_push
# MODIFIED: Import the new models and serializers
from .models import Language, User, PaymentDeclaration, Case, UssdMenuText, Agent, Payment, CaseHistory
from .serializers import CaseSerializer, CurrentUserSerializer, AgentRegisterSerializer, PaymentSerializer, CaseHistorySerializer


# --- View for the USSD Handler ---
class UssdHandlerView(APIView):
    """
    This view handles all the USSD requests from the gateway.
    """
    def get_menu_text(self, key, language_code='en'):
        try:
            menu = UssdMenuText.objects.get(menu_key=key, language__language_code=language_code)
            return menu.menu_text
        except UssdMenuText.DoesNotExist:
            try:
                menu = UssdMenuText.objects.get(menu_key=key, language__language_code='en')
                return menu.menu_text
            except UssdMenuText.DoesNotExist:
                return "Error: Menu not configured. Please contact support."

    def post(self, request, *args, **kwargs):
        session_id = request.data.get('sessionId')
        phone_number = request.data.get('phoneNumber')
        text = request.data.get('text', '')
        user, created = User.objects.get_or_create(phone_number=phone_number)
        response = ""
        text_parts = text.split('*')
        lang_code = user.default_language.language_code if user.default_language else 'en'
        if text == '':
            response = self.get_menu_text('welcome_menu', 'en')
        elif text_parts[0] in ['1', '2'] and len(text_parts) == 1:
            lang_code = 'en' if text_parts[0] == '1' else 'sw'
            language = Language.objects.get(language_code=lang_code)
            user.default_language = language
            user.save()
            response = self.get_menu_text('payment_declaration_menu', lang_code)
        elif text_parts[0] in ['1', '2'] and len(text_parts) == 2 and text_parts[1] in ['1', '2', '3']:
            declaration_map = {'1': 'standard', '2': 'small_fee', '3': 'cannot_pay'}
            status_code = declaration_map.get(text_parts[1])
            payment_declaration = PaymentDeclaration.objects.get(status_code=status_code)
            user.payment_declaration = payment_declaration
            user.save()
            response = self.get_menu_text('enter_symptom_menu', lang_code)
        elif text_parts[0] in ['1', '2'] and len(text_parts) == 3:
            health_issue = text_parts[2]
            new_case = Case.objects.create(user=user, symptom_input=health_issue, case_language=user.default_language, case_payment_declaration=user.payment_declaration)
            # Log the creation event
            CaseHistory.objects.create(case=new_case, description="Case created via USSD.")
            final_message_template = self.get_menu_text('case_created_success', lang_code)
            response = final_message_template.format(case_id=new_case.case_id)
        else:
            response = self.get_menu_text('invalid_selection_menu', lang_code)
        return Response(response, content_type='text/plain')


# --- Token Authentication Views ---
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        if not self.user.is_active:
            raise serializers.ValidationError("Account is not active. Please wait for admin approval.")
        return data

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


# --- Main API Views ---
class CaseListView(generics.ListCreateAPIView):
    serializer_class = CaseSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Case.objects.all().order_by('-created_at')
        try:
            patient_profile = User.objects.get(phone_number=user.username)
            return Case.objects.filter(user=patient_profile).order_by('-created_at')
        except User.DoesNotExist:
            return Case.objects.none()

    def perform_create(self, serializer):
        auth_user = self.request.user
        try:
            patient_profile = User.objects.get(phone_number=auth_user.username)
            # Save the case and log the creation event
            case = serializer.save(user=patient_profile)
            CaseHistory.objects.create(case=case, description="Case created via web dashboard.")
        except User.DoesNotExist:
            raise serializers.ValidationError("Could not find a patient profile for this user.")

class CaseDetailView(generics.RetrieveUpdateAPIView):
    queryset = Case.objects.all()
    serializer_class = CaseSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'

    def perform_update(self, serializer):
        # Log when an agent updates the case
        case = serializer.instance
        agent_name = self.request.user.agent.full_name if hasattr(self.request.user, 'agent') else 'Admin'
        CaseHistory.objects.create(case=case, description=f"Case updated by agent {agent_name}.")
        serializer.save()

class ClaimCaseView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, pk, *args, **kwargs):
        try:
            case_to_claim = Case.objects.get(pk=pk)
        except Case.DoesNotExist:
            return Response({"detail": "Case not found."}, status=status.HTTP_404_NOT_FOUND)
        if case_to_claim.agent is not None:
            return Response({"detail": f"Case already assigned to agent {case_to_claim.agent.user.username}."}, status=status.HTTP_400_BAD_REQUEST)

        agent_profile = request.user.agent
        case_to_claim.agent = agent_profile
        case_to_claim.status = 'assigned_to_agent'
        case_to_claim.save()
        # Log the claim event
        CaseHistory.objects.create(case=case_to_claim, description=f"Case claimed by agent {agent_profile.full_name}.")
        return Response({"detail": "Case successfully claimed."}, status=status.HTTP_200_OK)

class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        serializer = CurrentUserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


# --- Registration and Helper Views ---
class RegisterAgentView(generics.CreateAPIView):
    serializer_class = AgentRegisterSerializer
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Agent registered successfully. Awaiting approval."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CheckUsernameView(APIView):
    def get(self, request):
        username = request.GET.get('username', '').strip()
        if not username:
            return Response({'error': 'Username is required.'}, status=status.HTTP_400_BAD_REQUEST)
        exists = AuthUser.objects.filter(username__iexact=username).exists()
        return Response({'exists': exists})

class CheckEmailView(APIView):
    def get(self, request):
        email = request.GET.get('email', '').strip()
        if not email:
            return Response({'error': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)
        exists = AuthUser.objects.filter(email__iexact=email).exists()
        return Response({'exists': exists})

class ApproveAgentView(APIView):
    permission_classes = [IsAdminUser]
    def post(self, request, agent_id, *args, **kwargs):
        agent = get_object_or_404(Agent, pk=agent_id)
        auth_user = agent.user
        if auth_user.is_active:
            return Response({"message": "Agent already approved."}, status=status.HTTP_200_OK)
        auth_user.is_active = True
        auth_user.save()
        return Response({"message": f"Agent '{agent.full_name}' approved."}, status=status.HTTP_200_OK)

@api_view(['GET'])
def check_approval_status(request):
    username = request.GET.get('username', '').strip()
    try:
        user = AuthUser.objects.get(username=username)
        return Response({'exists': True, 'is_active': user.is_active})
    except AuthUser.DoesNotExist:
        return Response({'exists': False, 'is_active': False})


# --- Patient OTP Login Views ---
class UserRequestLoginOTPView(APIView):
    def post(self, request, *args, **kwargs):
        phone_number = request.data.get('phone_number')
        try:
            user = User.objects.get(phone_number=phone_number)
            otp_code = str(random.randint(100000, 999999))
            user.otp = otp_code
            user.otp_expiry = timezone.now() + timedelta(minutes=5)
            user.save()
            print(f"--- OTP for {phone_number}: {otp_code} ---")
            return Response({"message": "OTP has been generated for testing."}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "User with this phone number not found."}, status=status.HTTP_404_NOT_FOUND)

class UserVerifyLoginOTPView(APIView):
    def post(self, request, *args, **kwargs):
        phone_number = request.data.get('phone_number')
        otp_code = request.data.get('otp')
        try:
            user = User.objects.get(phone_number=phone_number)
            if user.otp != otp_code or user.otp_expiry < timezone.now():
                return Response({"error": "Invalid or expired OTP."}, status=status.HTTP_400_BAD_REQUEST)
            auth_user, created = AuthUser.objects.get_or_create(username=user.phone_number)
            if created:
                auth_user.set_unusable_password()
                auth_user.save()
            user.otp = None
            user.otp_expiry = None
            user.save()
            refresh = RefreshToken.for_user(auth_user)
            return Response({'refresh': str(refresh), 'access': str(refresh.access_token)})
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)


# --- Daraja Payment Views ---
class InitiatePaymentView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, *args, **kwargs):
        case_id = request.data.get('case_id')
        if not case_id:
            return Response({"error": "Case ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            case = Case.objects.get(pk=case_id)
            amount = 1
            phone_number = case.user.phone_number
            account_reference = f"AFYLNK{case.case_id}"
            transaction_desc = f"Payment for Case #{case.case_id}"
            daraja_response = initiate_stk_push(
                case=case, phone_number=phone_number, amount=amount,
                account_reference=account_reference, transaction_desc=transaction_desc
            )
            if daraja_response.get("ResponseCode") == "0":
                case.status = Case.CaseStatus.PAYMENT_PENDING
                case.save()
                CaseHistory.objects.create(case=case, description="Payment requested from patient.")
            return Response(daraja_response)
        except Case.DoesNotExist:
            return Response({"error": "Case not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@method_decorator(csrf_exempt, name='dispatch')
class DarajaCallbackView(APIView):
    def post(self, request, *args, **kwargs):
        print("✅ DARAJA CALLBACK: Received a callback.")
        stk_callback_response = request.data.get('Body', {}).get('stkCallback', {})
        print(stk_callback_response)
        result_code = stk_callback_response.get('ResultCode')
        checkout_request_id = stk_callback_response.get('CheckoutRequestID')

        try:
            case = Case.objects.get(checkout_request_id=checkout_request_id)
            if result_code == 0:
                print(f"✅ Payment successful for CheckoutRequestID: {checkout_request_id}")
                case.status = Case.CaseStatus.PAID
                case.save()
                CaseHistory.objects.create(case=case, description="Payment confirmed successfully.")

                # Create a permanent Payment record
                metadata = stk_callback_response.get('CallbackMetadata', {}).get('Item', [])
                amount = next((item['Value'] for item in metadata if item['Name'] == 'Amount'), None)
                receipt_number = next((item['Value'] for item in metadata if item['Name'] == 'MpesaReceiptNumber'), None)
                transaction_date_str = next((item['Value'] for item in metadata if item['Name'] == 'TransactionDate'), None)

                if amount and receipt_number and transaction_date_str:
                    transaction_date = timezone.make_aware(datetime.strptime(str(transaction_date_str), '%Y%m%d%H%M%S'))
                    Payment.objects.create(
                        case=case,
                        amount=amount,
                        mpesa_receipt_number=receipt_number,
                        transaction_date=transaction_date
                    )
            else:
                result_desc = stk_callback_response.get('ResultDesc')
                print(f"❌ Payment failed for CheckoutRequestID: {checkout_request_id}. Reason: {result_desc}")
                CaseHistory.objects.create(case=case, description=f"Payment failed: {result_desc}")

        except Case.DoesNotExist:
            print(f"❌ Case with CheckoutRequestID {checkout_request_id} not found.")

        return Response({"ResultCode": 0, "ResultDesc": "Accepted"}, status=status.HTTP_200_OK)


# --- NEW VIEWS FOR DASHBOARD FEATURES ---

class PaymentHistoryView(generics.ListAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        try:
            patient_profile = User.objects.get(phone_number=self.request.user.username)
            return Payment.objects.filter(case__user=patient_profile).order_by('-transaction_date')
        except User.DoesNotExist:
            return Payment.objects.none()

class CaseHistoryView(generics.ListAPIView):
    serializer_class = CaseHistorySerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        case_id = self.kwargs.get('case_id')
        return CaseHistory.objects.filter(case__pk=case_id)

def frontend_home(request):
    return render(request, 'index.html')



# --- Database Test View ---
class DatabaseTestView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            user_count = AuthUser.objects.count()
            message = f"SUCCESS: Database connection is working. Found {user_count} user(s)."
            return Response({"status": "OK", "message": message}, status=status.HTTP_200_OK)
        except Exception as e:
            message = f"FAILURE: Could not connect to the database. Error: {e}"
            return Response({"status": "Error", "message": message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)