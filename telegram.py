import os

from telebot import TeleBot

TG_BOT_TOKEN = os.environ["TG_BOT_TOKEN"]
TG_GROUP_ID = os.environ["TG_GROUP_ID"]


def TgSendDocuments(issue: dict, documents: dict[str, bytes]):
    """
    Высылает документы в телеграм группу
    """
    bot = TeleBot(TG_BOT_TOKEN)
    for filename, document in documents.items():
        bot.send_document(
            TG_GROUP_ID,
            document,
            visible_file_name=f"{issue['tg_document_filename_prefix']}{filename}",
            caption=issue["tg_caption_md"],
            parse_mode="markdown",
        )
