"""Общеупотребимые импорты"""
import os
from loguru import logger
import pickle
import datetime as dt
import random
import time
import glob


"""Импорты bd.py - для работы с базами данных"""
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, insert, update, MetaData, Table, Column, Text, TIMESTAMP
# from pydantic import BaseModel, HttpUrl

load_dotenv()

DB_NAME = os.getenv("DB_NAME")
DB_TEST = os.getenv("DB_TEST")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")

asmi = create_engine(
	f'postgresql+psycopg2://{DB_NAME}:{DB_PASS}@{DB_HOST}/{DB_NAME}', pool_pre_ping=True)
smi = create_engine(
	f'postgresql+psycopg2://{DB_TEST}:{DB_PASS}@{DB_HOST}/{DB_TEST}', pool_pre_ping=True)


"""Импорты shop.py - для работы со сбором новостей"""
from dateutil import parser
import requests
from bs4 import BeautifulSoup


"""Импорты cook.py - для работы обработкой новостей"""
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, T5ForConditionalGeneration
import fasttext as fasttext
import warnings

warnings.filterwarnings("ignore")
fasttext.FastText.eprint = lambda x: None
model_class = fasttext.load_model("models//cat_model.ftz")

tokenizer_resume = AutoTokenizer.from_pretrained("IlyaGusev/mbart_ru_sum_gazeta")
model_resume = AutoModelForSeq2SeqLM.from_pretrained("IlyaGusev/mbart_ru_sum_gazeta")

tokenizer_title = AutoTokenizer.from_pretrained("IlyaGusev/rut5_base_headline_gen_telegram")
model_title = T5ForConditionalGeneration.from_pretrained("IlyaGusev/rut5_base_headline_gen_telegram")




black_labels = \
	{
		'common_labels': (
			"ДАННОЕ СООБЩЕНИЕ (МАТЕРИАЛ) СОЗДАНО И (ИЛИ) РАСПРОСТРАНЕНО ИНОСТРАННЫМ СРЕДСТВОМ МАССОВОЙ ИНФОРМАЦИИ, "
			"ВЫПОЛНЯЮЩИМ ФУНКЦИИ ИНОСТРАННОГО АГЕНТА, И (ИЛИ) РОССИЙСКИМ ЮРИДИЧЕСКИМ ЛИЦОМ, ВЫПОЛНЯЮЩИМ ФУНКЦИИ "
			"ИНОСТРАННОГО АГЕНТА", '*Власти считают иноагентом', '*Минюст признал иноагентами'),
		'redakciya_channel': (
			'НАСТОЯЩИЙ МАТЕРИАЛ (ИНФОРМАЦИЯ) ПРОИЗВЕДЕН, РАСПРОСТРАНЕН И (ИЛИ) НАПРАВЛЕН ИНОСТРАННЫМ АГЕНТОМ ПИВОВАРОВЫМ '
			'АЛЕКСЕЕМ ВЛАДИМИРОВИЧЕМ ЛИБО КАСАЕТСЯ ДЕЯТЕЛЬНОСТИ ИНОСТРАННОГО АГЕНТА ПИВОВАРОВА АЛЕКСЕЯ ВЛАДИМИРОВИЧА',),
		'thevillagemsk': (
			' Поддержите The Village подпиской https://redefine.media/about (подробная инструкция здесь)',),
		'bbcrussian': ('@bbcrussian',),
		'interfaxonline': ('@interfaxonline',),
		'banksta': ('@banksta',),
		'thebell_io': (
			'НАСТОЯЩИЙ МАТЕРИАЛ (ИНФОРМАЦИЯ) ПРОИЗВЕДЕН И РАСПРОСТРАНЕН ИНОСТРАННЫМ АГЕНТОМ THE BELL ЛИБО КАСАЕТСЯ '
			'ДЕЯТЕЛЬНОСТИ ИНОСТРАННОГО АГЕНТА THE BELL. 18+',)
	}