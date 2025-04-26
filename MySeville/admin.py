from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, TouristPlace, TouristGuide, ContactMessage
from .models import Review  
from django.utils.html import format_html



class CustomUserAdmin(UserAdmin):
    model = CustomUser

    list_display = ('username', 'email', 'first_name', 'last_name', 'date_of_birth', 'address', 'nationality', 'is_staff', 'is_superuser')

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'date_of_birth', 'address', 'nationality')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'first_name', 'last_name', 'date_of_birth', 'address', 'nationality')}
        ),
    )

admin.site.register(CustomUser, CustomUserAdmin)

@admin.register(TouristPlace)
class TouristPlaceAdmin(admin.ModelAdmin):
    list_display = ("name", "activity_type", "visit_duration", "cost", "image_tag", "city")
    search_fields = ("name",)
    list_filter = ("activity_type",)

    def image_tag(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 50px;"/>', obj.image.url)
        return "-"
    image_tag.short_description = 'Image'


from django.contrib import admin
from .models import TouristGuide

@admin.register(TouristGuide)
class TouristGuideAdmin(admin.ModelAdmin):
    fields = (
        'user', 'guide_title', 'tour_date', 'available_time',
        'starting_point', 'ending_point', 'interests',
        'travel_type', 'tour_budget', 'city'
    )

    def get_changeform_initial_data(self, request):
        """
        When you click ‘Add’, this sets the form’s initial values.
        """
        return {'user': request.user}

    def save_model(self, request, obj, form, change):
        """
        Ensure the user is saved correctly if they weren’t already defined.
        """
        if not obj.user:
            obj.user = request.user
        super().save_model(request, obj, form, change)



admin.site.register(ContactMessage) 

admin.site.register(Review)


