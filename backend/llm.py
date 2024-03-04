"""This file is meant to handle business logic of creating and updating chats."""
import os
import time
import enum
import uuid
import base64
import openai
import requests
import tiktoken
import retrying
import functools

import jonlog


logger = jonlog.getLogger()
openai.api_key = os.environ.get('OPENAI_KEY') or open(os.path.expanduser('~/.openai_key')).read().strip()
replicate_api_key = os.environ.get('REPLICATE_KEY') or open(os.path.expanduser('~/.replicate_apikey')).read().strip()


class ChatLLMModel(enum.Enum):
    GPT3_5 = "gpt-3.5-turbo"
    GPT4  = "gpt-4-turbo-preview"

CHAT_LLM_MAX_LENGTHS = {
    ChatLLMModel.GPT3_5.value: 12_000,  # If fail, return to 4096
    ChatLLMModel.GPT4.value  : 12_000,  # 128k but lets limit for testing
}

class ChatLLM:

    def __init__(self, system, model=ChatLLMModel.GPT4.value):
        self._system = system
        self._model = model
        self._max_length = CHAT_LLM_MAX_LENGTHS[self._model]
        self._history = [
            {"role": "system", "content": self._system},
        ]
        logger.debug(f"Created ChatLLM instance with {self._model=} {self._max_length=} {system=}")

    @classmethod
    def from_hist(cls, hist, **kwargs):
        chat = ChatLLM(hist[0]["content"])
        chat._history = hist
        return chat

    @classmethod
    def num_tokens_from_text(cls, text, model=ChatLLMModel.GPT4.value):
        """Returns the number of tokens used by some text."""
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    
    @classmethod
    def num_tokens_from_messages(cls, messages, model=ChatLLMModel.GPT4.value):
        """Returns the number of tokens used by a list of messages."""
        encoding = tiktoken.encoding_for_model(model)
        num_tokens = 0
        for message in messages:
            num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
            for key, value in message.items():
                num_tokens += len(encoding.encode(value))
                if key == "name":  # if there's a name, the role is omitted
                    num_tokens += -1  # role is always required and always 1 token
        num_tokens += 2  # every reply is primed with <im_start>assistant
        return num_tokens

    @retrying.retry(stop_max_attempt_number=5, wait_fixed=2000)
    def _msg(self, *args, model=None, **kwargs):
        if model is None:
            model = self._model
        return openai.OpenAI(api_key=openai.api_key).chat.completions.create(
            *args, model=model, messages=self._history, **kwargs
        )
    
    def message(self, msg=None, role='user', no_resp=False, **kwargs):
        while len(self._history) > 1 and self.num_tokens_from_messages(self._history) > self._max_length:
            logger.info(f'Popping message: {self._history.pop(1)}')
        if msg is not None:
            self._history.append({"role": role, "content": msg})
        if no_resp:
            return None

        req_id = str(uuid.uuid4())[:16]
        logger.info(f'requesting openai.chat {req_id=} {self._model=}...')
        resp = self._msg(**kwargs)
        logger.info(f'received openai.chat {req_id=} {self._model=}...')
        text = resp.choices[0].message.content
        self._history.append({"role": "assistant", "content": text})
        return text

    def get_history(self):
        return self._history


class Image:
    SIZE = {
        "DALLE2_SMALL": "256x256",
        "DALLE2_MEDIUM": "512x512",
        "DALLE2_LARGE": "1024x1024",
        "DALLE3_SQUARE": "1024x1024",
        "DALLE3_HORIZONTAL": "1024x1024",
        "FOFR_MEDIUM": "512x512",
        "FOFR_HORIZONTAL": "960x480",
    }
    MODEL = {
        "2": "dall-e-2",
        "3": "dall-e-3",
        "fofr": "fofr",
    }

    @classmethod
    def create(cls, prompt, n=1, response_format="url", model=MODEL["fofr"], size=SIZE["FOFR_MEDIUM"]):
        logger.info(f'requesting Image with prompt={prompt}, n={n}, response_format={response_format}, model={model}, size={size}...')
        if model.startswith("dall-e"):
            resp = openai.OpenAI(api_key=openai.api_key).images.generate(prompt=prompt, n=n, size=size, model=model, response_format=response_format, timeout=45)
            resp = resp.data
        else:
            width, height = size.split('x')
            width, height = int(width), int(height)
            resp = requests.post(
                "https://api.replicate.com/v1/predictions",
                headers={"Content-Type": "application/json", "Authorization": f"Token {replicate_api_key}"},
                json={"version": "a83d4056c205f4f62ae2d19f73b04881db59ce8b81154d314dd34ab7babaa0f1", "input": {
                    "prompt": prompt,
                    "width": width, "height": height,
                    "num_images": n,
                }},
            )
            resp = resp.json()
            sleeps = 0
            while resp.get("status", "fail").lower() not in {"fail", "succeeded"}:
                if sleeps >= 10:
                    raise Exception('Error generating image', resp)
                logger.info(f"Sleeping 1...")
                time.sleep(1)
                sleeps += 1
                resp = requests.get(f"https://api.replicate.com/v1/predictions/{resp['id']}", headers={"Content-Type": "application/json", "Authorization": f"Token {replicate_api_key}"})
                resp = resp.json()
                
        logger.info('received Image...')
        return resp
class FastImage:

    @classmethod
    def generate(cls, prompt, size='768x512', **kwargs):
        data = Image.create(prompt, model='fofr', size=size, **kwargs)
        url = data['output'][0]
        # Get the MIME type of the image (e.g., 'image/jpeg', 'image/png')
        mime_type = f"image/{url.rsplit('.', 1)[-1]}"
        # Encode to base64 and format as a data URI
        return f"data:{mime_type};base64," + base64.b64encode(requests.get(url).content).decode()

    @classmethod
    @functools.lru_cache(maxsize=120)
    def generate_food(cls, dish_name, prompt_template='DSLR photo of {dish_name} served in a restaurant, award-winning, realistic, delicious, 8k resolution'):
        return cls.generate(prompt_template.format(dish_name=dish_name))
