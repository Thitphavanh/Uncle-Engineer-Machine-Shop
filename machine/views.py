from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import models
from django.contrib.admin.views.decorators import staff_member_required
from .models import Machine, MachineCategory, MachineImage
from .forms import MachineForm, OrderInquiryForm


def index(request):
    machines = Machine.objects.filter(is_available=True).order_by("-id")[:6]

    context = {
        "machines": machines,
    }

    return render(request, "index.html", context)


def machines(request):
    # Get filter parameters
    category_slug = request.GET.get("category", None)
    search_query = request.GET.get("search", None)

    # Start with all available machines
    all_machines = Machine.objects.filter(is_available=True)

    # Filter by category if specified
    if category_slug:
        all_machines = all_machines.filter(category__slug=category_slug)

    # Filter by search query if specified
    if search_query:
        all_machines = all_machines.filter(
            models.Q(title__icontains=search_query)
            | models.Q(descriptions__icontains=search_query)
        )

    # Order by newest first
    all_machines = all_machines.order_by("-id")

    # Get all categories for filter
    categories = MachineCategory.objects.all().order_by("name")

    # Get selected category for display
    selected_category = None
    if category_slug:
        selected_category = MachineCategory.objects.filter(slug=category_slug).first()

    context = {
        "all_machines": all_machines,
        "categories": categories,
        "selected_category": selected_category,
        "search_query": search_query,
        "total_count": all_machines.count(),
    }
    return render(request, "machine/machines.html", context)


def machine_detail(request, slug):
    machine = get_object_or_404(Machine, slug=slug, is_available=True)
    # Get all images related to this machine
    machine_images = machine.covers_images.all().order_by("-is_primary", "id")

    context = {
        "machine": machine,
        "machine_images": machine_images,
    }
    return render(request, "machine/machine-detail.html", context)


def categories(request):
    all_categories = MachineCategory.objects.all().order_by("name")

    # Count machines for each category
    categories_with_count = []
    for category in all_categories:
        machine_count = category.machines.filter(is_available=True).count()
        categories_with_count.append({"category": category, "machine_count": machine_count})

    context = {
        "categories": categories_with_count,
    }
    return render(request, "machine/categories.html", context)


def category_detail(request, slug):
    category = get_object_or_404(MachineCategory, slug=slug)
    machines = category.machines.filter(is_available=True).order_by("-id")

    context = {
        "category": category,
        "machines": machines,
        "machine_count": machines.count(),
    }
    return render(request, "machine/category-detail.html", context)


def user_login(request):
    if request.user.is_authenticated:
        return redirect("index")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f"ยินดีต้อนรับ {user.username}!")

            # Redirect to next page if specified
            next_page = request.GET.get("next", "index")
            return redirect(next_page)
        else:
            messages.error(request, "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

    return render(request, "auth/login.html")


# Static Pages
def about(request):
    return render(request, "pages/about.html")


def contact(request):
    return render(request, "pages/contact.html")


def careers(request):
    return render(request, "pages/careers.html")


def partners(request):
    return render(request, "pages/partners.html")


def privacy_policy(request):
    return render(request, "pages/privacy-policy.html")


def terms_of_service(request):
    return render(request, "pages/terms-of-service.html")


# Cart Views
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from .cart import Cart

@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Machine, id=product_id)
    quantity = int(request.POST.get('quantity', 1))
    cart.add(product=product, quantity=quantity)

    # Check if it's an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        from django.http import JsonResponse
        return JsonResponse({
            'status': 'success',
            'message': 'เพิ่มสินค้าลงตะกร้าแล้ว',
            'cart_count': len(cart)
        })

    return redirect('cart_detail')

@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Machine, id=product_id)
    cart.remove(product)
    return redirect('cart_detail')

@require_POST
def cart_update(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Machine, id=product_id)
    quantity = int(request.POST.get('quantity', 1))
    cart.add(product=product, quantity=quantity, update_quantity=True)

    # Check if it's an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        from django.http import JsonResponse
        return JsonResponse({'status': 'success'})

    return redirect('cart_detail')

def cart_detail(request):
    cart = Cart(request)
    return render(request, 'cart/cart_detail.html', {'cart': cart})

@login_required(login_url="login")
def checkout(request):
    cart = Cart(request)

    if request.method == 'POST':
        # Get payment information
        payment_method = request.POST.get('payment_method', 'qr')
        payment_slip = request.FILES.get('payment_slip')
        note = request.POST.get('note', '')

        # Calculate total amount
        total_amount = cart.get_total_price()

        # Create Order
        from .models import Order, OrderItem
        order = Order.objects.create(
            user=request.user,
            payment_method=payment_method,
            payment_slip=payment_slip,
            note=note,
            total_amount=total_amount,
            status='pending'
        )

        # Create OrderItems
        for item in cart:
            OrderItem.objects.create(
                order=order,
                machine=item['product'],
                quantity=item['quantity'],
                price=item['price']
            )

        # Clear the cart
        cart.clear()

        messages.success(
            request,
            f"✅ สั่งซื้อเรียบร้อยแล้ว! หมายเลขคำสั่งซื้อของคุณคือ #{order.id} "
            f"{'เราได้รับสลิปโอนเงินของคุณแล้ว ' if payment_slip else ''}"
            f"ระบบจะตรวจสอบและยืนยันภายใน 24 ชั่วโมง"
        )
        return redirect('index')

    return render(request, 'cart/checkout.html', {'cart': cart})


# Admin Views - Machine Upload
@staff_member_required(login_url='login')
def machine_upload(request):
    """
    View สำหรับอัพโหลด Machine (เข้าได้เฉพาะ admin/staff เท่านั้น)
    รองรับการอัพโหลดหลายรูปภาพพร้อมกัน
    """
    if request.method == 'POST':
        form = MachineForm(request.POST, request.FILES)

        if form.is_valid():
            # บันทึก Machine ก่อน
            machine = form.save()

            # จัดการกับรูปภาพเพิ่มเติม (multiple images)
            images = request.FILES.getlist('images')

            if images:
                for index, image in enumerate(images):
                    # สร้าง MachineImage object สำหรับแต่ละรูป
                    MachineImage.objects.create(
                        machine=machine,
                        image=image,
                        alt_text=f"{machine.title} - Image {index + 1}",
                        is_primary=(index == 0)  # รูปแรกจะเป็นรูปหลัก
                    )

            messages.success(
                request,
                f'เพิ่ม Machine "{machine.title}" สำเร็จ! '
                f'อัพโหลดรูปภาพทั้งหมด {len(images)} รูป'
            )
            return redirect('machine_upload')
        else:
            messages.error(request, 'เกิดข้อผิดพลาด กรุณาตรวจสอบข้อมูลอีกครั้ง')
    else:
        form = MachineForm()

    # ดึง Machine ล่าสุด 10 รายการมาแสดง
    recent_machines = Machine.objects.all().order_by('-id')[:10]

    context = {
        'form': form,
        'recent_machines': recent_machines,
    }

    return render(request, 'admin/machine_upload.html', context)


@require_POST
def submit_inquiry(request, machine_id):
    machine = get_object_or_404(Machine, id=machine_id)
    form = OrderInquiryForm(request.POST)
    
    if form.is_valid():
        inquiry = form.save(commit=False)
        inquiry.machine = machine
        inquiry.save()
        
        return JsonResponse({
            'status': 'success', 
            'message': 'เราได้รับข้อมูลของคุณแล้ว ทางเราจะติดต่อกลับโดยเร็วที่สุด'
        })
    else:
        return JsonResponse({
            'status': 'error', 
            'errors': form.errors,
            'message': 'กรุณาตรวจสอบข้อมูลให้ถูกต้อง'
        }, status=400)
