from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

# Import all views, including the new CheckEmailView
from .views import (
    UssdHandlerView,
    CaseListView,
    CaseDetailView,
    ClaimCaseView,
    CurrentUserView,
    RegisterAgentView,
    CheckUsernameView,
    CheckEmailView,  # ADDED: Import the new view
    ApproveAgentView,
    check_approval_status,
    UserRequestLoginOTPView, # ✅ ADD THIS
    UserVerifyLoginOTPView,  # ✅ ADD THIS
    DarajaCallbackView, # ✅ ADD THIS
    InitiatePaymentView, # ✅ ADD THIS
    MyTokenObtainPairView
)

# API Routes
urlpatterns = [
    # JWT Authentication
    path('token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Your existing URLs
    path('ussd/', UssdHandlerView.as_view(), name='ussd_handler'),
    path('cases/', CaseListView.as_view(), name='case-list'),
    path('cases/<int:pk>/', CaseDetailView.as_view(), name='case-detail'),
    path('cases/<int:pk>/claim/', ClaimCaseView.as_view(), name='case-claim'),
    path('me/', CurrentUserView.as_view(), name='current-user'),
    path('register/', RegisterAgentView.as_view(), name='agent-register'),

    # Registration validation helpers
    path('check-username/', CheckUsernameView.as_view(), name='check-username'),
    path('check-email/', CheckEmailView.as_view(), name='check-email'), # ADDED: The new URL for email validation

    # Agent status URLs
    path('agents/<int:agent_id>/approve/', ApproveAgentView.as_view(), name='agent-approve'),
    path('check-approval-status/', check_approval_status, name='check-approval-status'),

     # --- Patient OTP Login URLs ---
    path('user/request-login/', UserRequestLoginOTPView.as_view(), name='user-request-login'),
    path('user/verify-login/', UserVerifyLoginOTPView.as_view(), name='user-verify-login'),

    # Registration validation helpers
    path('check-username/', CheckUsernameView.as_view(), name='check-username'),

     # ✅ ADD THIS NEW URL FOR INITIATING PAYMENTS
    path('initiate-payment/', InitiatePaymentView.as_view(), name='initiate-payment'),

     # ✅ ADD THE CALLBACK URL
    path('payments/callback/', DarajaCallbackView.as_view(), name='daraja-callback'),
]