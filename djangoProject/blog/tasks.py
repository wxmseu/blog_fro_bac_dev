from utils.sms import YunTongXin
from djangoProject.celery import app


@app.task
def send_msm_c(phone, code):
    config = {
        "accountSid": "8a216da883c633c601840e80788a0c86",
        "accountToken": "acd67f7521874bc48641196cda1eb89d",
        "appId": "8a216da883c633c601840e80795c0c8d",
        "templateId": "1"
    }

    yun = YunTongXin(**config)
    res = yun.run(phone, code)
    return res

