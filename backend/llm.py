"""This file is meant to handle business logic of creating and updating chats."""
import os
import enum
import uuid
import groq
import openai
import tiktoken
import retrying

import jonlog


logger = jonlog.getLogger()
openai.api_key = os.environ.get('OPENAI_KEY') or open(os.path.expanduser('~/.openai_key')).read().strip()
groq_apikey = os.environ.get('GROQ_KEY') or open(os.path.expanduser('~/.groq_apikey')).read().strip()


class ChatLLMModel(enum.Enum):
    GPT3_5 = "gpt-3.5-turbo"
    GPT4  = "gpt-4-turbo-preview"
    MIXTRAL = "mixtral-8x7b-32768"

CHAT_LLM_MAX_LENGTHS = {
    ChatLLMModel.GPT3_5.value   : 12_000,  # If fail, return to 4096
    ChatLLMModel.GPT4.value     : 12_000,  # 128k but lets limit for testing
    ChatLLMModel.MIXTRAL.value  : 12_000,  # 128k but lets limit for testing
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
        model_class = openai.OpenAI(api_key=openay.api_key)
        if model == ChatLLMModel.MIXTRAL.value:
            model_class = groq.Groq(api_key=groq_apikey)
        return model_class.chat.completions.create(
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
        logger.info(f'requesting LLM.chat {req_id=} {self._model=}...')
        resp = self._msg(**kwargs)
        logger.info(f'received LLM.chat {req_id=} {self._model=}...')
        text = resp.choices[0].message.content
        self._history.append({"role": "assistant", "content": text})
        return text

    def get_history(self):
        return self._history

