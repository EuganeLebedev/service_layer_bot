import json

import telebot
from telebot import types
import requests

bot_token = ""
channel = '192151684'


bot = telebot.TeleBot(bot_token)

name = ''
surname = ''
age = 0


@bot.message_handler(content_types=['text'])
def start(message):
    if message.text == '/reg':
        bot.send_message(message.from_user.id, "Как тебя зовут?")
        # bot.register_next_step_handler(message, get_name)  # следующий шаг – функция get_name
    elif message.text.lower() == 'tmp':
        get_all_approval_requests(message)
    else:
        bot.send_message(message.from_user.id, 'Напиши /reg')



def login_to_sld():
    url = "https://192.168.221.171:50000/b1s/v1/Login"

    request_body = {
        "CompanyDB": "",
        "Password": "1111",
        "UserName": "rusak"
    }

    return requests.post(url, json=request_body, verify=False)



def get_all_approval_requests(message):

    login_request = login_to_sld()

    url = "https://192.168.221.171:50000/b1s/v1/ApprovalRequests?$filter=Status eq 'W'"
    cookies = {"B1SESSION": login_request.json().get('SessionId')}
    header = {"Prefer": "odata.maxpagesize=2"}
    get_approval_documents = requests.get(url, verify=False, cookies=cookies, headers=header)
    for document in get_approval_documents.json().get('value'):
        keyboard = types.InlineKeyboardMarkup()  # наша клавиатура
        document_key = types.InlineKeyboardButton(text=f"Утвердить", callback_data=json.dumps(
            {"Code": document.get("Code"),
             "Action": "Approve"}))
        keyboard.add(document_key)  # добавляем кнопку в клавиатуру
        question=f"Документ {document.get('Code')} от {document.get('CreationDate')} {document.get('CreationTime')}"

        bot.send_message(message.from_user.id, text=question, reply_markup=keyboard)
        print(document)


def accept_approval_request(message, document_id=None):
    login_request = login_to_sld()
    cookies = {"B1SESSION": login_request.json().get('SessionId')}
    header = {"Prefer": "odata.maxpagesize=2"}
    url = f'https://192.168.221.171:50000/b1s/v1/ApprovalRequests({document_id})'
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
        pass
    else:
        # bot.send_message(message.from_user.id, text="Error")
        pass



def deny_approval_request(message):
    pass




@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    print(f"{call.data=}")
    if call.data == "yes": #call.data это callback_data, которую мы указали при объявлении кнопки
        pass #код сохранения данных, или их обработки
        bot.send_message(call.message.chat.id, 'Запомню : )')
    elif call.data == "no":
         pass #переспрашиваем
    elif call.data == 'Все документы, требующие утверждения':
        pass
    elif json.loads(call.data).get('Code') and json.loads(call.data).get("Action") == "Approve":
        print("callback", call.data)
        accept_approval_request(call.message, json.loads(call.data).get('Code'))

bot.polling(none_stop=True, interval=0)
