from django.urls import path
from . import views

urlpatterns = [
    # API endpoint for creating a seller
    path('create_seller_account', views.SellerCreateView.as_view(), name='createseller'),

    # API for viewing all registered sellers
    path('sellers/', views.SellerListView.as_view(), name='sellers'),

    # API endpoint for viewing a specific seller
    path('sellers/<str:pk>', views.SpecificSellerView.as_view(), name='seller'),

    # API endpoint for viewing, updating, and deleting a specific seller
    path('sellers/<str:pk>/profile', views.SpecificSellerProfileView.as_view(), name='seller_profile'),

    # API endpoint for viewing all items
    path('items', views.AllItemsListView.as_view(), name='items'),

    # API endpoint for viewing a specific item in the home page
    path('items/<int:pk>', views.SpecificItemView.as_view(), name='item_view'),

    # API endpoint for viewing items belonging to a specific seller
    path('sellers/<str:pk>/items', views.SpecificSellerItemsView.as_view(), name='seller_items'),

    # API endpoint for creating items
    path('sellers/<str:pk>/items/add_item', views.ItemCreateView.as_view(), name='add_item'),

    # API endpoint for viewing and updating a specific item in a specific seller page
    path('sellers/<str:seller_id>/items/<int:pk>', views.SpecificSellerSpecificItemView.as_view(), name='seller_specific_item'),

    # API endpoint for creating a buyer account
    path('create_buyer', views.BuyerCreateView().as_view(), name='create_buyer'),

    # API for updating a buyer
    path('buyers/<str:pk>/profile', views.SpecificBuyerProfileView.as_view(), name='buyer_profile'),

    # API for viewing a specific buyer
    path('buyers/<str:pk>', views.SpecificBuyerView.as_view(), name='buyer_profile'),

    # API endpoint for creating an order
    path('submit_order', views.OrderCreateView.as_view(), name='create_order'),

    # API for listing seller orders
    path('sellers/<str:pk>/orders', views.OrderListView.as_view(), name='orders'),

    # API for retrieving, updating, and deleting a specific order
    path('sellers/<str:seller_id>/orders/<str:pk>/edit', views.SpecificSellerSpecificOrderView.as_view(), name='orders'),

    # API for viewing a specific order
    path('sellers/<str:seller_id>/orders/<str:pk>', views.SpecificOrderView.as_view(), name='orders'),

    # API for viewing a specific order
    path('buyers/<str:pk>/orders', views.SpecificBuyerOrderView.as_view(), name='buyer_orders'),

    # API for M-Pesa payment initiation
    path('mpesa/payment/', views.MpesaPaymentView.as_view(), name='mpesa-payment'),

    # API for M-Pesa payment callback
    path('mpesa/callback/', views.MpesaCallbackView.as_view(), name='mpesa-callback'),

    path('login', views.CustomAuthToken.as_view(), name='login')
]
