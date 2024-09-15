from django.shortcuts import render
from .serializers import *
from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveUpdateDestroyAPIView
from .models import *
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from . permissions import *
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response


import requests
from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Transaction, Seller
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
import base64
from datetime import datetime

class MpesaPaymentView(APIView):
    """Handle M-Pesa STK Push"""
    permission_classes = [IsAuthenticated]  # Ensure the user is authenticated

    def post(self, request):
        phone_number = request.data.get('phone_number')
        amount = request.data.get('amount')
        seller_id = request.data.get('seller_id')

        print(phone_number, amount, seller_id)

        if not seller_id:
            return Response({"error": "Seller ID is required"}, status=400)

        try:
            # Retrieve the seller's phone number from the database
            seller = Seller.objects.get(id=seller_id)
            seller_phone_number = seller.phone_number
            print(seller_phone_number)
        except Seller.DoesNotExist:
            return Response({"error": "Seller not found"}, status=404)
        

        # Safaricom API credentials and URLs
        consumer_key = settings.MPESA_CONSUMER_KEY
        consumer_secret = settings.MPESA_CONSUMER_SECRET
        business_short_code = settings.MPESA_SHORTCODE
        lipa_na_mpesa_online_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
        callback_url = "https://precious-adversely-prawn.ngrok-free.app/mpesa/callback/"  # Replace with your callback URL

        # Step 1: Get access token
        auth_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
        response = requests.get(auth_url, auth=(consumer_key, consumer_secret))
        access_token = response.json().get('access_token')

        # Step 2: Generate password for M-Pesa STK push
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password = base64.b64encode(f"{business_short_code}{settings.MPESA_PASSKEY}{timestamp}".encode()).decode()

        # Step 3: Generate STK push payload
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        stk_push_payload = {
            "BusinessShortCode": business_short_code,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone_number,  # Phone number initiating the payment
            "PartyB": business_short_code,
            "PhoneNumber": seller_phone_number,  # Seller's phone number
            "CallBackURL": callback_url,
            "AccountReference": "JengaBay",
            "TransactionDesc": "Payment for order"
        }

        # Step 4: Make STK push request
        mpesa_response = requests.post(lipa_na_mpesa_online_url, json=stk_push_payload, headers=headers)
        print(mpesa_response.json())
        # Step 5: Handle response from Safaricom
        mpesa_response_data = mpesa_response.json()
        if mpesa_response_data.get('ResponseCode') == "0":
            # Payment initiated successfully, create a transaction record
            transaction = Transaction.objects.create(
                transaction_mode="m-pesa",
                amount=amount,
                payer=request.user.buyer,  # assuming the logged-in user is the buyer
                recipient=Seller.objects.get(id=seller_id),
                phone_number=phone_number,
                merchant_request_id=mpesa_response_data.get('MerchantRequestID'),
                checkout_request_id=mpesa_response_data.get('CheckoutRequestID'),
                payment_status="Pending"
            )
            return Response({"message": "STK push initiated", "transaction_id": transaction.id})
        else:
            return Response({"error": "Failed to initiate payment"}, status=400)


class MpesaCallbackView(APIView):
    """Handle M-Pesa payment callback from Safaricom"""

    def post(self, request):
        # Process callback data
        callback_data = request.data.get('Body').get('stkCallback')

        merchant_request_id = callback_data.get('MerchantRequestID')
        result_code = callback_data.get('ResultCode')
        transaction_code = None

        if result_code == 0:
            # Payment successful
            transaction_code = callback_data.get('CallbackMetadata').get('Item')[1].get('Value')
            Transaction.objects.filter(merchant_request_id=merchant_request_id).update(
                payment_status="Completed", transaction_code=transaction_code, completed_at=timezone.now()
            )
        else:
            # Payment failed
            Transaction.objects.filter(merchant_request_id=merchant_request_id).update(payment_status="Failed")

        return Response({"message": "Callback received"}, status=200)

class SellerCreateView(CreateAPIView):
    """api for creating new sellers"""

    serializer_class = SellerProfileSerializer
    queryset = Seller.objects.all()

class SellerListView(ListAPIView):
    """api for listing all sellers"""

    serializer_class = SellerSerializer
    queryset = Seller.objects.all().filter(profile__is_active=True)


class SpecificSellerProfileView(RetrieveUpdateDestroyAPIView):
    """api used to get, update and delete a specific seller
    must be logged in as a seller"""
    permission_classes = [permissions.IsAuthenticated, IsAccountOwner]
    serializer_class = SellerProfileUpdateSerializer
    queryset = Seller.objects.all()

class SpecificSellerView(ListAPIView):
    """api used to get a specific seller"""

    serializer_class = SellerSerializer

    def get_queryset(self):
        return Seller.objects.all().filter(id=self.kwargs['pk'])

class SpecificItemView(ListAPIView):
    """api used to get a specific item"""

    serializer_class = ItemViewSerializer
    
    def get_queryset(self):
        return Item.objects.all().filter(id=self.kwargs['pk'])

class SpecificSellerSpecificItemView(RetrieveUpdateDestroyAPIView):
    """api used to get, update and delete a specific item in a specific seller page
    must be logged in as the item seller"""
    serializer_class = ItemSerializer
    queryset = Item.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsItemSeller]

class AllItemsListView(ListAPIView):
    """api listing all items in the database"""

    serializer_class = ItemViewSerializer
    queryset = Item.objects.all()
    filter_backends = [filters.SearchFilter, DjangoFilterBackend,]
    search_fields = [
        'item_seller__business_name', 'item_seller__sub_county__subcounty_name',
        'item_seller__sub_county__county__county_name', 'item_seller__local_area_name',
        'item_seller__town', 'item_seller__building', 'item_seller__street',
        'item_name', 'item_description', 'category',]
        
    filterset_fields = ['category',]

class SpecificSellerItemsView(ListAPIView):
    """api for listing items belonging to a specific seller"""

    serializer_class = ItemSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend,]
    search_fields = ['item_name', 'item_description', 'category',]
    filterset_fields = ['category',]


    def get_queryset(self):
        return Item.objects.all().filter(item_seller=self.kwargs['pk'])


class ItemCreateView(CreateAPIView):
    """api for creating items via a seller account
    must be logged in as a seller"""

    permission_classes = [permissions.IsAuthenticated, HasAddItemPermission]
    serializer_class = ItemCreateSerializer
    queryset = Item.objects.all()

class BuyerCreateView(CreateAPIView):
    """api for creating new buyers"""

    serializer_class = BuyerProfileSerializer
    queryset = Buyer.objects.all()

class BuyerListView(ListAPIView):
    """api for listing all buyers"""

    serializer_class = BuyerSerializer
    queryset = Buyer.objects.all().filter(profile__is_active=True)


class SpecificBuyerProfileView(RetrieveUpdateDestroyAPIView):
    """api used to get, update and delete a specific Buyer
    must be logged in as a buyer"""
    permission_classes = [permissions.IsAuthenticated, IsAccountOwner]
    serializer_class = BuyerProfileUpdateSerializer
    queryset = Buyer.objects.all()

class SpecificBuyerView(ListAPIView):
    """api used to get a specific Buyer"""

    serializer_class = BuyerSerializer

    def get_queryset(self):
        return Seller.objects.all().filter(id=self.kwargs['pk'])

class OrderCreateView(CreateAPIView):
    """api for creating a new order
    must be logged in as a buyer"""
    permission_classes = [permissions.IsAuthenticated, IsABuyer]
    serializer_class = OrderSerializer
    queryset = Order.objects.all()

class OrderListView(ListAPIView):
    """api for listing all orders for a specific seller
    must be logged in as a seller"""
    permission_classes = [permissions.IsAuthenticated, HasSellerPermission]
    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.all().filter(payment_transaction__recipient=self.kwargs['pk'])


class SpecificSellerSpecificOrderView(RetrieveUpdateDestroyAPIView):
    """api used to get, update and delete a specific Order
    must be logged in as a seller"""
    permission_classes = [permissions.IsAuthenticated, HasSellerPermission]
    serializer_class = OrderSerializer
    queryset = Order.objects.all()

class SpecificOrderView(ListAPIView):
    """api used to view a specific order by a seller or a buyer
    must be logged in as the seller or buyer involved in the order"""
    permission_classes = [permissions.IsAuthenticated, HasSellerPermission or HasBuyerOrderPermission]

    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.all().filter(id=self.kwargs['pk'])

class SpecificBuyerOrderView(ListAPIView):
    """api used to view all orders made by a buyer
    must be logged in as the buyer involved in the orders"""
    permission_classes = [permissions.IsAuthenticated, HasBuyerOrderPermission]

    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.all().filter(payment_transaction__payer=self.kwargs['pk'])


class TransactionCreateView(CreateAPIView):
    """api for creating a new Transaction"""
    permission_classes = [permissions.IsAuthenticated, IsABuyer]
    serializer_class = TransactionSerializer
    queryset = Transaction.objects.all()

class TransactionListView(ListAPIView):
    """this api allows a specific seller to view all the transactions they are involved in"""
    permission_classes = [permissions.IsAuthenticated, HasTransactionViewPermission]
    serializer_class = TransactionSerializer

    def get_queryset(self):
        return Transaction.objects.all().filter(recipient=self.kwargs['pk'])


class SpecificSellerSpecificTransactionView(RetrieveUpdateDestroyAPIView):
    """api used to get, update and delete a specific Transaction"""
    permission_classes = [permissions.IsAuthenticated, HasTransactionViewPermission]
    serializer_class = TransactionSerializer
    queryset = Transaction.objects.all()

class SpecificTransactionView(ListAPIView):
    """This api allows a buyer and a seller to view a specific transaction involving both of them"""
    permission_classes = [permissions.IsAuthenticated, HasTransactionViewPermission, IsABuyer]

    serializer_class = TransactionSerializer

    def get_queryset(self):
        return Transaction.objects.all().filter(id=self.kwargs['pk'])

class CustomAuthToken(ObtainAuthToken):
    """A Custom authentication class that creates an expiring authentication token
    for a user who logs in"""

    def post(self, request, *args, **kwargs):
        """An override of the post method that takes a login request, verifies
        the login credentials and creates an expiring token once the user is verified"""
        
        # Validate the login request
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        # Create or retrieve the authentication token
        token, created = Token.objects.get_or_create(user=user)
        if not created:
            # Update the token's creation time to keep it valid
            token.created = datetime.utcnow()
            token.save()

        # Check if the user is a Seller or Buyer and assign account_id and session_status
        if Seller.objects.filter(profile=user).exists():
            account_id = Seller.objects.get(profile=user).id
            session_status = 'seller'
        elif Buyer.objects.filter(profile=user).exists():
            account_id = Buyer.objects.get(profile=user).id  # Fix this to retrieve Buyer's ID
            session_status = 'buyer'
        else:
            account_id = None
            session_status = None

        # Return the token and user details
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'email': user.email,
            'session_status': session_status,
            'account_id': account_id
        })