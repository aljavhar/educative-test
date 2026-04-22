"""
Main URL configuration for EduTest Platform.

All API endpoints live under /api/v1/
Swagger docs available at /api/docs/
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# ─── Swagger API Documentation ───────────────────────────────────────────────────
schema_view = get_schema_view(
    openapi.Info(
        title="EduTest Platform API",
        default_version='v1',
        description="""
        Educational Testing Platform REST API.
        
        Roles:
        - **Teacher**: Create courses, groups, topics, questions. View analytics.
        - **Student**: Take tests, view results and progress.
        
        Authentication: Use JWT Bearer tokens.
        Get your token from POST /api/v1/auth/login/
        """,
        contact=openapi.Contact(email="admin@eduplatform.com"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Django admin panel
    path('admin/', admin.site.urls),

    # Web interface (browser, templates)
    path('web/', include('web.urls', namespace='web')),
    path('', lambda req: __import__('django.shortcuts', fromlist=['redirect']).redirect('/web/')),

    # API Documentation (Swagger UI)
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    # API v1 Routes
    path('api/v1/auth/', include('users.urls.auth')),
    path('api/v1/users/', include('users.urls.users')),
    path('api/v1/courses/', include('courses.urls.courses')),
    path('api/v1/groups/', include('courses.urls.groups')),
    path('api/v1/topics/', include('tests_app.urls.topics')),
    path('api/v1/questions/', include('tests_app.urls.questions')),
    path('api/v1/tests/', include('tests_app.urls.tests')),
    path('api/v1/results/', include('results.urls')),
    path('api/v1/analytics/', include('results.analytics_urls')),
    path('api/v1/ai/', include('ai_generator.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
