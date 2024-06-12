from django.urls import path
from . import views

urlpatterns = [
    path('getLibraryDetails/', views.get_library_details, name='get-library-details'),
    path('bookSearch/', views.book_search, name='book-search'),
]