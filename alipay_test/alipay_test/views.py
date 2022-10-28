from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
from django.conf import settings
from alipay import AliPay
from datetime import datetime
from django.http import HttpResponse

app_private_key_string = open(settings.ALIPAY_KEY_DIRS + 'app_private_key.pem').read()
alipay_public_key_string = open(settings.ALIPAY_KEY_DIRS + 'alipay_public_key.pem').read()


class MyAlipay(View):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_private_key_string=app_private_key_string,
            alipay_public_key_string=alipay_public_key_string,
            app_notify_url=None,
            sign_type='RSA2',
            debug=True  # 默认false True则将请求转发到沙箱
        )

    def get_trade_url(self, order_id, amount):
        order_str = self.alipay.api_alipay_trade_page_pay(
            # 订单标题
            subject=order_id,
            out_trade_no=order_id,
            # 总价格
            total_amount=amount,
            # 支付完毕后，将用户跳转到哪个页面
            return_url=settings.ALIPAY_RETURN_URL,
            notify_url=settings.ALIPAY_NOTIFY_URL,

        )
        return 'https://openapi.alipaydev.com/gateway.do?' + order_str

    def get_verify_result(self, data, sign):
        # 验证签名 True成功 False 失败
        return self.alipay.verify(data, sign)

    def get_trade_result(self, order_id):
        # 主动查询
        result = self.alipay.api_alipay_trade_query(order_id)
        if result.get('trade_status') == 'TRADE_SUCCESS':
            return True
        return False


class OrderView(MyAlipay):

    def get(self, request):
        return render(request, 'alipay.html')

    def post(self, request):
        # 返回支付地址
        # 接受到文章id后，生成订单 订单状态 待付款 已付款 付款失败
        order_id = datetime.now().strftime('%Y%m%d%H%M%S')
        pay_url = self.get_trade_url(order_id=order_id, amount=100000)
        return JsonResponse({'pay_url': pay_url})


class ResultView(MyAlipay):
    def post(self, request):
        # notify_url 业务逻辑
        request_data = {k: request.POST[k] for k in request.POST.keys()}
        sign = request_data.pop('sign')
        is_verify = self.get_verify_result(request_data, sign)
        if is_verify:
            trade_status = request_data.get('trade_status')
            if trade_status == 'TRADE_SUCCESS':
                print('支付成功')
                # 修改自己数据库中的订单状态
                return HttpResponse('success')
        else:
            return JsonResponse({'msg': '违法请求'})

    def get(self, request):
        # return url 业务逻辑
        order_id = request.GET.get('out_trade_no')
        # 查询订单表状态，如果还是待付款，采取B方案，主动查询支付宝 订单真实交易状态
        # 主动查询
        result = self.get_trade_result(order_id)
        if result:
            return HttpResponse('-----支付成功-----主动查询')
        return HttpResponse('----支付异常----主动查询')
