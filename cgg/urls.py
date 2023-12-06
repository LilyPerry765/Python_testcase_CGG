"""cgg URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URL conf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.utils.translation import gettext as _

from cgg.apps.basic import (
    api_urls as basic_api_urls,
    web_urls as basic_web_urls,
)
from cgg.apps.finance import (
    api_urls as finance_api_urls,
    web_urls as finance_web_urls,
)

admin.site.site_header = _("CGG Admin Panel")
admin.site.site_title = "CGG"
admin.site.index_title = "CGG"

urlpatterns = [
    path('health-check/', include('health_check.urls')),
    path('admin/', admin.site.urls),
    path('api/finance/', include(finance_api_urls)),
    path('web/finance/', include(finance_web_urls)),
    path('api/basic/', include(basic_api_urls)),
    path('web/basic/', include(basic_web_urls)),
]
