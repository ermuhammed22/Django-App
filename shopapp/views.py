import csv
import logging

from timeit import default_timer

from django.contrib.auth.models import Group, User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import permission_required
from django.contrib.syndication.views import Feed

from django.utils.decorators import method_decorator
from django.http import HttpResponse, HttpRequest, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.core.cache import cache

from django.views import View
from django.views.decorators.cache import cache_page
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView

from .forms import ProductForm, OrderForm, GroupForm
from .models import Product, Order, ProductImage
from .serializers import OrderSerializer


log = logging.getLogger(__name__)


class ShopIndexView(View):

    # @method_decorator(cache_page(60 * 2))
    def get(self, request: HttpRequest) -> HttpResponse:
        products = [
            ('Laptop', 10000),
            ('Desktop', 20000),
            ('Smartphone', 15000),
        ]
        context = {
            'time_running': default_timer(),
            'products': products,
            'items': 2,
        }
        log.debug('Products for shop index: %s', products)
        log.info('Rendering shop index')
        print("shop index context", context)
        return render(request, 'shopapp/shop-index.html', context=context)


class GroupsListView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        context = {
            'form': GroupForm(),
            'groups': Group.objects.prefetch_related('permissions').all(),
        }
        return render(request, 'shopapp/groups-list.html', context=context)

    def post(self, request: HttpRequest):
        form = GroupForm(request.POST)
        if form.is_valid():
            form.save()

        return redirect(request.path)


class ProductDetailsView(DetailView):
    template_name = 'shopapp/product-details.html'
    # model = Product
    queryset = Product.objects.prefetch_related('images')
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = context['product']
        context['images_count'] = product.images.count() if hasattr(product, 'images') else 0
        return context


class ProductsListView(ListView):
    template_name = 'shopapp/products-list.html'
    # model = Product
    context_object_name = 'products'
    queryset = Product.objects.filter(archived=False)


class ProductCreateView(UserPassesTestMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'shopapp/product_form.html'
    success_url = reverse_lazy('shopapp:products_list')
    permission_required = 'shopapp.add_product'

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def test_func(self):
        # return self.request.user.groups.filter(name="secret-group").exists()
        return self.request.user.is_superuser

    def form_valid(self, form):
        response = super().form_valid(form)
        for image in self.request.FILES.getlist('images'):
            ProductImage.objects.create(product=self.object, image=image)
        return response


class ProductUpdateView(PermissionRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Product
    # fields = 'name', 'price', 'description', 'discount', 'preview'
    form_class = ProductForm
    template_name_suffix = '_update_form'
    permission_required = 'shopapp.change_product'

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs)

    def get_success_url(self):
        return reverse('shopapp:product_details', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        response = super().form_valid(form)
        for image in self.request.FILES.getlist('images'):
            ProductImage.objects.create(product=self.object, image=image)
        return response


# class ProductImagesUploadView(View):
#     template_name = 'shopapp/upload_files.html'
#
#     def get(self, request):
#         form = ProductMultipleForm()
#         return render(request, self.template_name, {'form': form})
#
#     def post(self, request):
#         if request.method == 'POST':
#             form = ProductMultipleForm(request.POST, request.FILES)
#             if form.is_valid():
#                 files = request.FILES.getlist('images')
#                 if not files:
#                     form.add_error('images', 'Не выбраны файлы для загрузки.')
#                 else:
#                     for file in files:
#                         ProductImage.objects.create(image=file)
#                     return redirect('shopapp:products_list')
#                 form.save()
#             return render(request, self.template_name, {'form': form})

    def test_func(self):
        product = self.get_object()
        return self.request.user.is_superuser or product.created_by == self.request.user


class ProductDeleteView(DeleteView):
    model = Product
    success_url = reverse_lazy('shopapp:products_list')

    def form_valid(self, form):
        success_url = self.get_success_url()
        self.object.archived = True
        self.object.save()
        return HttpResponseRedirect(success_url)


@method_decorator(login_required, name='dispatch')
class OrdersListView(LoginRequiredMixin, ListView):
    queryset = (
        Order.objects
        .select_related('user')
        .prefetch_related('products')
        .all()
    )


class OrderDetailView(DetailView):
    model = Order
    template_name = 'shopapp/order_detail.html'
    context_object_name = 'order'

    def get_queryset(self):
        return Order.objects.select_related('user').prefetch_related('products')


class OrderCreateView(CreateView):
    model = Order
    fields = 'user', 'products', 'promocode', 'delivery_address'
    template_name = 'shopapp/order_form.html'
    success_url = reverse_lazy('shopapp:orders_list')


class OrderUpdateView(UpdateView):
    model = Order
    fields = 'user', 'products', 'promocode', 'delivery_address'
    template_name = 'shopapp/order_update_form.html'

    def get_success_url(self):
        return reverse('shopapp:order_details', kwargs={'pk': self.object.pk})


class OrderDeleteView(DeleteView):
    model = Order
    template_name = 'shopapp/order_confirm_delete.html'
    success_url = reverse_lazy('shopapp:orders_list')


class OrdersExportView(View):
    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="orders.csv"'

        writer = csv.writer(response)
        writer.writerow(['ID', 'User', 'Created At'])

        for order in Order.objects.all():
            writer.writerow([order.id, order.user.username, order.created_at])

        return response


class ProductsDataExportView(View):
    def get(self, request: HttpRequest) -> JsonResponse:
        cache_key = "products_data_export"
        products_data = cache.get(cache_key)
        if products_data is None:
            products = Product.objects.order_by("pk").all()
            products_data = [
                {
                    "pk": product.pk,
                    "name": product.name,
                    "price": product.price,
                    "archived": product.archived,
                }
                for product in products
            ]
            elem = products_data[0]
            name = elem["name"]
            print("name:", name)
            cache.set(cache_key, products_data, 300)
        return JsonResponse({"products": products_data})


class LatestProductsFeed(Feed):
    title = "Shop products (latest)"
    description = "Updates on new products in the shop."
    link = reverse_lazy("shopapp:products_list")

    def items(self):
        return (
            Product.objects
            .filter(archived=False)
            .order_by("-created_at")[:5]
        )

    def item_title(self, item: Product):
        return item.name

    def item_description(self, item: Product):
        return item.description[:200]


class UserOrdersListView(LoginRequiredMixin, ListView):
    """
    Представление для отображения списка заказов конкретного пользователя.
    Доступно только авторизованным пользователям.
    """
    template_name = 'shopapp/user_orders_list.html'
    context_object_name = 'orders'

    def dispatch(self, request, *args, **kwargs):
        # Получаем пользователя (владельца заказов) по user_id из URL
        # и сохраняем его в self.owner, чтобы использовать в других методах
        # get_object_or_404 сам вызовет Http404, если пользователь не найден
        self.owner = get_object_or_404(User, pk=self.kwargs.get('user_id'))
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        # Фильтруем заказы по пользователю,
        # которого мы получили в методе dispatch
        return Order.objects.filter(user=self.owner).prefetch_related('products')

    def get_context_data(self, **kwargs):
        # Добавляем self.owner (владельца заказов) в контекст,
        # чтобы использовать его в шаблоне
        context = super().get_context_data(**kwargs)
        context['owner'] = self.owner
        return context


class UserOrdersExportView(View):
    """
    Представление для экспорта заказов пользователя в JSON
    с низкоуровневым кешированием.
    """
    def get(self, request: HttpRequest, user_id: int) -> JsonResponse:
        # 1. Генерируем уникальный ключ кеша
        cache_key = f"user_orders_export_{user_id}"

        # 2. Пытаемся получить данные из кеша
        orders_data = cache.get(cache_key)

        # 3. Если в кеше нет (None), то генерируем данные
        if orders_data is None:
            print(f"--- ЗАПРОС К БАЗЕ И ГЕНЕРАЦИЯ КЕША ДЛЯ USER {user_id} ---")
            # Ищем пользователя, или 404
            user = get_object_or_404(User, pk=user_id)

            # Загружаем заказы, сортируем по PK (как в задании)
            orders = Order.objects.filter(user=user).order_by('pk')

            # Сериализуем данные
            serializer = OrderSerializer(orders, many=True)
            orders_data = serializer.data

            # 4. Сохраняем данные в кеш на 3 минуты (180 секунд)
            cache.set(cache_key, orders_data, 180)

        # 5. Возвращаем данные (из кеша или свежесгенерированные)
        return JsonResponse({"orders": orders_data})
