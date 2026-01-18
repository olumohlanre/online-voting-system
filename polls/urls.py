from django.urls import path
from django.contrib.auth import views as auth_views
from .views import index, vote, results, register, create_poll, detail

urlpatterns = [
    path('', index, name='index'),
    path('vote/<int:poll_id>/', vote, name='vote'),
    path('results/<int:poll_id>/', results, name='results'),
    path('login', auth_views.LoginView.as_view(template_name='registration/login.html', next_page='index'), name='login'),
    path('register', register, name='register'),
    path('logout', auth_views.LogoutView.as_view(), name='logout'),
    path('create/', create_poll, name='create'),
    path('deatil/', detail, name='detail'),
]