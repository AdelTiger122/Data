import requests
from random import randint
try:
    import telebot
    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
except ModuleNotFoundError:
    input("هیچ کتابخانه لازم وجود ندارد. فرمان خط فرمان را تکمیل کنید: PIP نصب pytelegrambotapi")

url = "https://leakosintapi.com/"
bot_token = "8164126713:AAElohaeW3-IELyuBIFDC96VidZYYmGtOmw" #نشانه دریافت شده از Botfather را در اینجا وارد کنید
api_token = "6081045644:f6wM8cxz"  #نشانه دریافت شده از Leakosint را در اینجا وارد کنید
lang = "ru"
limit = 300

#در این عملکرد می توانید بررسی کنید که آیا کاربر به آن دسترسی دارد
def user_access_test(user_id):
    return(True)

#عملکرد برای تولید گزارش ها
cash_reports = {}
def generate_report(query, query_id):
    global cash_reports, url, bot_token, api_token, limit, lang
    data =  {"token":api_token, "request":query.split("\n")[0], "limit": limit, "lang":lang}
    response = requests.post(url, json=data).json()
    print(response)
    if "Error code" in response:
        print("خطا:"+response["Error code"])
        return(None)
    cash_reports[str(query_id)] = []
    for database_name in response["List"].keys():
        text = [f"<b>{database_name}</b>",""]
        text.append(response["List"][database_name]["InfoLeak"]+"\n")
        if database_name!="No results found":
            for report_data in response["List"][database_name]["Data"]:
                for column_name in report_data.keys():
                    text.append(f"<b>{column_name}</b>:  {report_data[column_name]}")
                text.append("")
        text = "\n".join(text)
        if len(text)>3500:
            text = text[:3500]+text[3500:].split("\n")[0]+"\n\nبرخی از داده ها متناسب با این پیام نبودند"
        cash_reports[str(query_id)].append(text)
    return(cash_reports[str(query_id)])

#عملکردی برای ایجاد صفحه کلید درون خطی
def create_inline_keyboard(query_id, page_id, count_page):
    markup = InlineKeyboardMarkup()
    if page_id<0:
        page_id=count_page
    elif page_id>count_page-1:
        page_id=page_id%count_page
    if count_page==1:
        return markup
    markup.row_width = 3
    markup.add(InlineKeyboardButton(text = "<<", callback_data=f"/page {query_id} {page_id-1}"),
               InlineKeyboardButton(text = f"{page_id+1}/{count_page}", callback_data="page_list"),
               InlineKeyboardButton(text = ">>", callback_data=f"/page {query_id} {page_id+1}"))
    return markup

bot = telebot.TeleBot(bot_token)
@bot.message_handler(commands=["start"])
def send_welcome(message):
    bot.reply_to(message, "سلام! من یک تلگرام بوت هستم که می تواند پایگاه داده ها را جستجو کند.", parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def echo_message(message):
    user_id = message.from_user.id
    if not(user_access_test(user_id)):
        bot.send_message(message.chat.id, "شما به ربات دسترسی ندارید")
        return()
    if message.content_type == "text":
        query_id = randint(0,9999999)
        report = generate_report(message.text,query_id)
        markup = create_inline_keyboard(query_id,0,len(report))
        if report==None:
            bot.reply_to(message, "ربات در حال حاضر کار نمی کند.", parse_mode="Markdown")
        try:
            bot.send_message(message.chat.id, report[0], parse_mode="html", reply_markup=markup) #, reply_markup=markup
        except telebot.apihelper.ApiTelegramException:
            bot.send_message(message.chat.id, text = report[0].replace("<b>","").replace("</b>",""), reply_markup=markup)
        
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call: CallbackQuery):
    global cash_reports
    if call.data.startswith("/page "):
        query_id, page_id = call.data.split(" ")[1:]
        if not(query_id in cash_reports):
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="نتایج درخواست قبلاً حذف شده است")
        else:
            report = cash_reports[query_id]
            markup = create_inline_keyboard(query_id,int(page_id),len(report))
            try:
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=report[int(page_id)], parse_mode="html", reply_markup=markup)
            except telebot.apihelper.ApiTelegramException:
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=report[int(page_id)].replace("<b>","").replace("</b>",""), reply_markup=markup)
while True:
    try:
        bot.polling()
    except:
        pass