from users.models import Profile


def user_role(request):
    if request.user.is_authenticated:
        profile = Profile.objects.filter(user=request.user).first()
        role = profile.role if profile else None

        cart_count = 0
        if role == Profile.Role.BUYER:
            from cart.models import Cart, CartItem
            from django.db.models import Sum
            cart = Cart.objects.filter(buyer=request.user, status=Cart.Status.OPEN).first()
            if cart:
                result = CartItem.objects.filter(cart=cart).aggregate(total=Sum("quantity"))
                cart_count = result["total"] or 0

        return {"user_role": role, "cart_count": cart_count}
    return {"user_role": None, "cart_count": 0}
