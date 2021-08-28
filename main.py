import json

import telebot
from telebot import types
import requests
import settings



bot = telebot.TeleBot(settings.bot_token)

name = ''
surname = ''
age = 0


@bot.message_handler(content_types=['text'])
def start(message):
    if message.text.lower() == 'документы':
        get_all_approval_requests(message)
    else:
        bot.send_message(message.from_user.id, "Для вывода смиска докумендов на утверждение напиши Документы")



def login_to_sld():
    url = settings.sld_url + "/Login"

    request_body = {
        "CompanyDB": "STRATNANOTECH_17_12_2020",
        "Password": "1111",
        "UserName": "rusak"
    }

    return requests.post(url, json=request_body, verify=False)



def get_all_approval_requests(message):

    login_request = login_to_sld()

    url =  settings.sld_url + "/ApprovalRequests?$filter=Status eq 'W'"
    cookies = {"B1SESSION": login_request.json().get('SessionId')}
    header = {"Prefer": "odata.maxpagesize=0"}
    get_approval_documents = requests.get(url, verify=False, cookies=cookies, headers=header)
    documents = get_approval_documents.json().get('value')
    if len(documents) > 0:
        for document in documents:
            print(document)
            keyboard = types.InlineKeyboardMarkup()  # наша клавиатура
            document_key_approve = types.InlineKeyboardButton(text=f"Утвердить", callback_data=json.dumps(
                {"Code": document.get("Code"),
                 "Action": "Approve"}))
            document_key_deny = types.InlineKeyboardButton(text=f"Отклонить", callback_data=json.dumps(
                {"Code": document.get("Code"),
                 "Action": "Deny"}))
            keyboard.add(document_key_approve)  # добавляем кнопку в клавиатуру
            keyboard.add(document_key_deny)  # добавляем кнопку в клавиатуру
            question=f"""Документ {document.get('Code')} от {document.get('CreationDate')} {document.get('CreationTime')}\n{document.get('Remarks')}\n"""

            if len(document.get("ApprovalRequestLines")) > 0:
                question += "Этапы утверждения:\n"
                for line in document.get("ApprovalRequestLines"):
                    question += f"{line.get('StageCode')} {line.get('Status')}\n"

            bot.send_message(message.from_user.id, text=question, reply_markup=keyboard)
    else:
        bot.send_message(message.from_user.id, text='Нет документов на утверждение')


def accept_approval_request(message, document_id=None):
    login_request = login_to_sld()
    cookies = {"B1SESSION": login_request.json().get('SessionId')}
    header = {"Prefer": "odata.maxpagesize=20"}
    url = settings.sld_url + "/ApprovalRequests({document_id})"
    request_body = {
    "ApprovalRequestDecisions": [
        {
            "Status": "ardApproved",
            "Remarks": "Approved - OK"
        }
    ]
}
    approve_request = requests.patch(url, verify=False, cookies=cookies, headers=header, json=request_body)

    if approve_request.status_code == 200:
        # bot.send_message(message.from_user.id, text="Ok")
        return True
    else:
        # bot.send_message(message.from_user.id, text="Error")
        return False



def deny_approval_request(message, document_id=None):
    login_request = login_to_sld()
    cookies = {"B1SESSION": login_request.json().get('SessionId')}
    header = {"Prefer": "odata.maxpagesize=2"}
    url = settings.sld_url + "/ApprovalRequests({document_id})"
    request_body = {
        "ApprovalRequestDecisions": [
            {
                "Status": "ardNotApproved",
                "Remarks": "Approved - Rejected"
            }
        ]
    }
    approve_request = requests.patch(url, verify=False, cookies=cookies, headers=header, json=request_body)

    if approve_request.status_code == 200:
        # bot.send_message(message.from_user.id, text="Ok")
        return True
    else:
        # bot.send_message(message.from_user.id, text="Error")
        return False




@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    if call.data == 'Все документы, требующие утверждения':
        pass
    elif json.loads(call.data).get('Code') and json.loads(call.data).get("Action") == "Approve":
        print("callback", call.data)
        accept_approval_request(call.message, json.loads(call.data).get('Code'))
        bot.send_message(call.message.chat.id, 'Готово')
        # get_all_approval_requests(call.message)
    elif json.loads(call.data).get('Code') and json.loads(call.data).get("Action") == "Deny":
        print("callback", call.data)
        deny_approval_request(call.message, json.loads(call.data).get('Code'))
        bot.send_message(call.message.chat.id, 'Готово')
        # get_all_approval_requests(call.message)


bot.polling(none_stop=True, interval=0)
