import json
import os
from base64 import b64decode
from datetime import datetime
from zoneinfo import ZoneInfo

import dotenv
import yaml
from jinja2 import Template

dotenv.load_dotenv(dotenv.find_dotenv())

from documents import DocxFillTemplate  # noqa: E402
from telegram import TgSendDocuments  # noqa: E402


def handler(event: dict, _: dict):
    """
    Основной обработчик событий - внешних http запросов
    """
    body = (
        b64decode(event["body"]).decode("utf-8")
        if event["isBase64Encoded"]
        else event["body"]
    )
    form_answer: dict = json.loads(body)
    print(f"FORM ANSWER:\n{json.dumps(form_answer)}")

    with open("substitute.yaml", "r") as substitute_file:
        substitute: dict = yaml.safe_load(substitute_file)

    form_data: dict = form_answer["answer"]["data"]

    ###################################
    # Подготовка данных
    ###################################
    issue = (
        {
            "form_name": form_answer["form_name"],
            "created": datetime.fromisoformat(
                form_answer["answer"]["created"]
            ).astimezone(ZoneInfo("Europe/Moscow")),
        }
        | {
            key: _safe_form_value(key, value)
            for key, value in form_data.items()
            if not _key_is_answer_group(key)
        }
        | {
            answer_goup_key: {
                "length": len(answer_goup_value["value"]),
                "values": [
                    {
                        key: _safe_form_value(key, value)
                        for key, value in answer_group_fields.items()
                    }
                    for answer_group_fields in answer_goup_value["value"]
                ],
            }
            for answer_goup_key, answer_goup_value in form_data.items()
            if _key_is_answer_group(answer_goup_key)
        }
    )

    ###################################
    # Подстановка данных из файла substitute.yaml
    ###################################
    for key, value in substitute.items():
        issue[key] = Template(value).render(issue)

    ###################################
    # Дебаг вывод значений
    ###################################
    if os.environ.get("DEBUG") in ["True", "true", "yes"]:
        print(f"DEBUG ISSUE:\n{issue}")

    ###################################
    # Генерация и высылка документов
    ###################################
    variables = {
        f"{'{'}{'{'} {key} {'}'}{'}'}": f"{value}" for key, value in issue.items()
    }
    documents = {
        filename: DocxFillTemplate(f"templates/{filename}", variables)
        for filename in os.listdir("templates")
        if filename.endswith(".docx")
    }
    TgSendDocuments(issue, documents)


def _key_is_answer_group(key: str) -> bool:
    """
    Проверка того, что заданный ключ является группой ответов
    """
    return key.startswith("answer_group")


YA_DATE_FROMAT = "%Y-%m-%d"


def _to_date_ru(vaule: str) -> str:
    return datetime.strptime(vaule, YA_DATE_FROMAT).strftime("%d.%m.%Y")


def _safe_form_value(key: str, value: dict) -> str | int | dict:
    """
    Безопасное получение данных формы - получает данные по формату и меняет формат записи даты
    """
    if key.endswith("date"):
        return _to_date_ru(value["value"])
    if key.endswith("int"):
        return int(value["value"])
    if key.endswith("dates"):
        duration = datetime.strptime(
            value["value"]["end"], YA_DATE_FROMAT
        ) - datetime.strptime(value["value"]["begin"], YA_DATE_FROMAT)
        return {
            "begin": _to_date_ru(value["value"]["begin"]),
            "end": _to_date_ru(value["value"]["end"]),
            "duration": duration,
        }
    return value["value"]
