from django.urls import path
from .views import registro, iniciar_sesion, cerrar_sesion, home, welcome_view,  tourist_guides_view, contact_view, new_tourist_guide, generate_tour, legal_view, privacy_view, editar_perfil, aceptar_cookies, FAQs, guide_detail, reviews_view, download_pdf_html
from django.contrib.auth import views as auth_views
from .forms import CustomSetPasswordForm
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('', home, name='home'),  
    path('register/', registro, name='register'),
    path('login/', iniciar_sesion, name='login'),
    path('logout/', cerrar_sesion, name='logout'),
    path('welcome/', welcome_view, name='welcome_page'),
    path('tourist-guides/', tourist_guides_view, name='tourist_guides'),
    path('guide/<int:pk>/', guide_detail, name='guide_detail'),  # <- Añadido
    path('profile/', editar_perfil, name='profile'),  
    path('tourist-guides/new/', new_tourist_guide, name='new_tourist_guide'),
    path("generate-tour/", generate_tour, name="generate_tour"),
    path('reset-password/', auth_views.PasswordResetView.as_view(template_name='password_reset_form.html'), name='password_reset'),
    path('reset-password/done/', auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html',form_class=CustomSetPasswordForm  ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), name='password_reset_complete'),
    path('legal/', legal_view, name='legal'),
    path('privacy/', privacy_view, name='privacy'),
    path('contact/', contact_view, name='contact'),
    path('aceptar-cookies/', aceptar_cookies, name='aceptar_cookies'),
    path('FAQs/', FAQs, name='FAQs'),
    path('reviews/', reviews_view, name='reviews'),
    path('download-pdf/', download_pdf_html, name='download_pdf_html'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

