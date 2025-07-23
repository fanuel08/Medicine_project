from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User as AuthUser

from .models import Agent, Case, Language, PaymentDeclaration, User as UssdUser, UssdMenuText

# ✅ Inline: Agent profile inside AuthUser admin
class AgentInline(admin.StackedInline):
    model = Agent
    can_delete = False
    verbose_name_plural = 'Agent Profile'
    fk_name = 'user'


# ✅ Admin Action: Bulk approve selected inactive agents
def approve_selected_users(modeladmin, request, queryset):
    updated = 0
    for user in queryset:
        if not user.is_active and hasattr(user, 'agent'):
            user.is_active = True
            user.save()
            updated += 1
    modeladmin.message_user(request, f"✅ Approved {updated} agent(s).")
approve_selected_users.short_description = "✅ Approve selected agents"


# ✅ Customized Django User Admin (includes agent info)
class CustomUserAdmin(BaseUserAdmin):
    inlines = (AgentInline,)
    list_display = ('username', 'email', 'is_staff', 'is_active', 'is_agent', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('username', 'email')
    actions = [approve_selected_users]

    def is_agent(self, obj):
        return hasattr(obj, 'agent')
    is_agent.boolean = True
    is_agent.short_description = 'Is Agent?'


# ✅ Unregister original User admin and re-register with ours
admin.site.unregister(AuthUser)
admin.site.register(AuthUser, CustomUserAdmin)


# ✅ Admins for core models
@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ('language_code', 'language_name')
    search_fields = ('language_code', 'language_name')


@admin.register(PaymentDeclaration)
class PaymentDeclarationAdmin(admin.ModelAdmin):
    list_display = ('status_code', 'description')
    search_fields = ('status_code', 'description')


@admin.register(UssdUser)
class UssdUserAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'default_language', 'payment_declaration', 'created_at')
    list_filter = ('default_language', 'payment_declaration')
    search_fields = ('phone_number',)


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ('case_id', 'user', 'agent', 'status', 'ai_urgency', 'ai_category', 'created_at')
    list_filter = ('status', 'ai_urgency', 'ai_category')
    search_fields = ('symptom_input', 'user__phone_number', 'agent__username')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(UssdMenuText)
class UssdMenuTextAdmin(admin.ModelAdmin):
    list_display = ('menu_key', 'language', 'menu_text')
    list_filter = ('language',)
    search_fields = ('menu_key', 'menu_text')


# ✅ Hide Agent from side panel (managed via User admin)
@admin.register(Agent)
class HiddenAgentAdmin(admin.ModelAdmin):
    def has_module_permission(self, request):
        return False
