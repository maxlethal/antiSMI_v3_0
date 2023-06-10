from db import *

import datetime as dt
import glob
import os
from loguru import logger

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