from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group

from .forms import UserRegisterForm
from .models import MyUser


class UserAdmin(BaseUserAdmin):
    add_form = UserRegisterForm

    # , 'entrepot', 'ville','role'

    list_display = ('username', 'first_name', 'last_name', 'role')
    list_filter = ('is_admin',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Permissions', {'fields': ('is_admin',)})
    )
    search_fields = ('username', 'role')
    # , 'entrepot', 'ville'
    ordering = ('username',)

    filter_horizontal = ()


admin.site.register(MyUser, UserAdmin)

admin.site.unregister(Group)
