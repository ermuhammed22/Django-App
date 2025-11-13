import time
from django.http import HttpRequest, JsonResponse
from django.utils.deprecation import MiddlewareMixin

THROTTLE_TIME = 5

request_log = {}


def set_useragent_on_request_middleware(get_response):
    print('initial call')

    def middleware(request: HttpRequest):
        print('before get response')
        # Безопасное получение заголовка HTTP_USER_AGENT
        request.user_agent = request.META.get('HTTP_USER_AGENT', 'unknown')
        response = get_response(request)
        print('after get response')
        return response

    return middleware


class CountRequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.request_count = 0
        self.responses_count = 0
        self.exceptions_count = 0

    def __call__(self, request: HttpRequest):
        self.request_count += 1
        print('requests count: ', self.request_count)
        response = self.get_response(request)
        self.responses_count += 1
        print('responses count: ', self.responses_count)
        return response

    def process_exception(self, request: HttpRequest, exception: Exception):
        self.exceptions_count += 1
        print('got: ', self.exceptions_count, 'exceptions so far')


class ThrottlingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        user_ip = self.get_client_ip(request)
        current_time = time.time()

        if user_ip in request_log:
            last_request_time = request_log[user_ip]
            if current_time - last_request_time < THROTTLE_TIME:
                return JsonResponse({'error': 'Too many requests. Please wait before trying again.'}, status=429)

        request_log[user_ip] = current_time

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

