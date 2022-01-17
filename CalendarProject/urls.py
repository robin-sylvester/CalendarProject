"""CalendarProject URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import include, path
from django.views.generic.base import TemplateView

from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from authentication.views import SignUpView
from apartman.views import ApartmanIcsView, ApartmanUrlView, ExportApartman, ExportApartmanByID, EmptyDatabase, Schedule, get_dynamic_data

urlpatterns = [
    #path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('register/', SignUpView.as_view(), name='signup'),
    path('import-calendar', ApartmanIcsView.as_view(), name='import-calendar'),
    path('import-from-url', ApartmanUrlView.as_view(), name='import-from-url'),
    path('export', ExportApartman.as_view(), name='export'),
    path('export/<int:pk>', ExportApartmanByID.as_view(), name='export_by_id'),
    path('empty/', EmptyDatabase.as_view(), name='empty'),
    path('calendars/', get_dynamic_data, name='get_dynamic_data'),
    path('schedule/', Schedule.as_view(), name='schedule'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    urlpatterns += staticfiles_urlpatterns()
