"""
URL configuration for NutriBite project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
# urls.py
from django.contrib import admin
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import NutriBiteLoginView
from .views import MyLogoutView, toggle_favourite
from .views import nutrition_info

urlpatterns = [
    path('admin/', admin.site.urls),

    # Public pages
    path('', views.dashboard, name='home'),  
    path('dashboard/', views.dashboard, name='dashboard'),

    # Registration
    path('sign-up/', views.sign_up, name='sign_up'),

    # Authentication
    path(
        'sign-out/',
        auth_views.LogoutView.as_view(
            next_page='sign_in'
        ),
        name='sign_out'
    ),
    path('sign-in/', NutriBiteLoginView.as_view(), name='sign_in'),
    path('logout/', MyLogoutView.as_view(), name='logout'),
    # ...

    path("browseRecipes/", views.browse_recipes, name="browse_recipes"),

    path('add-recipe/', views.add_recipe, name='add_recipe'),
    path('edit-recipe/<int:pk>/', views.edit_recipe, name='edit_recipe'),
    path('delete-recipe/<int:pk>/', views.delete_recipe, name='delete_recipe'),

     path("nutrition-info/", nutrition_info, name="nutrition_info"),

    path("recipe/<int:mealdb_id>/", views.view_recipe, name="view_recipe"),
    path('browseRecipes/favourite/', views.toggle_favourite, name='toggle_favourite'),
]
