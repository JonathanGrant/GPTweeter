import argparse
import os
import re
import yaml
import json
from flask import Flask, render_template, request, send_from_directory, Response, jsonify
from flask_cors import CORS
from flask_restx import Api, Resource, reqparse, fields, Namespace

import jonlog
import llm


logger = jonlog.getLogger()
parser = argparse.ArgumentParser()
parser.add_argument('--env', default='dev')
args = parser.parse_args()
logger.info(f'Starting with {args=}')

# Create the Flask application
app = Flask(__name__, static_folder='/users/jong/Documents/ftwitter/frontend/build')
CORS(app)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

# Setup Flask-Restx and Swagger
api = Api(
    app,
    version='1.0',
    title='ChatWithMenu API',
    doc='/apidocs',
    description='A simple API for ChatWithMenu'
)
api_namespace = Namespace('api', description='API operations', path='/api')


@api_namespace.route('/tweets/<topic>')
class TweetResource(Resource):
    def get(self, topic):
        # TODO: Get topic from random file stuff
        chat = llm.ChatLLM(
            system="""You are DankTweeterGPT.
Write only in this tweet like format (Example):
```{"tweets": [
    {
        "user_id": "@robinhanson",
        "user_name": "Robin Hanson",
        "datetime": "1h ago",
        "text": "**Demanding Job Joke:**\n\"If you don't come in to work on Saturday, don't bother to come in on Sunday.\""
    },
    {
        "user_id": "@MorningBrew",
        "user_name": "Morning Brew",
        "datetime": "19h ago",
        "text": "You merely adopted the McDonald's. I was born in it, molded by it.\n🍔 MCDO"
    },
    {
        "user_id": "@Noahpinion",
        "user_name": "Noah Smith",
        "datetime": "12 minutes ago",
        "text": "Every time I hang out with a bunch of friends, I need to take a break from Twitter. It's so brutal coming right back to this place and watching a bunch of strangers trying to be an asshole to other strangers over political stuff that they probably don't even really care about."
    },
    {
        "user_id": "@TeRDOS",
        "user_name": "Terminally Online Engineer",
        "datetime": "Now",
        "text": "Me breaking prod:\n*No further details provided.*"
    }
]}
```
When writing threads, always do "1/n" so you don't need to commit to a thread length.
Return only this JSON format.
""",
            model=llm.ChatLLMModel.GPT3_5.value,
        )
        resp = chat.message(f"Give me five informative tweets about {topic}.")
        if resp.startswith('```'):
            resp = resp[3:-3]
        return jsonify(json.loads(resp))
        # # TODO: Limit 5 in query params?
        # return jsonify({
        #     "tweets": [
        #         {
        #             "user_id": "@DuckEvolve",
        #             "user_name": "Dr. Quack Evolutionary Tales",
        #             "datetime": "Just now",
        #             "text": "Duck Bill Evolution 101: Ducks evolved bills as a versatile tool for feeding. Whether it's sifting through water for plants, catching insects, or preying on small fish, their bills are perfectly adapted. Nature's Swiss Army knife for our feathery friends! 🦆💡 #Evolution #DuckFacts"
        #         },
        #         {
        #             "user_id": "@FeatheredFacts",
        #             "user_name": "BirdWatcher Supreme",
        #             "datetime": "Just now",
        #             "text": "Fascinating how evolution shapes creatures for survival. Ducks' bills are a prime example of adaptability and efficiency in the animal kingdom. 🌿🦆 #NatureIsAmazing"
        #         },
        #         {
        #             "user_id": "@PondThoughts",
        #             "user_name": "Pond Philosopher",
        #             "datetime": "Just now",
        #             "text": "Ever noticed how ducks can filter water and mud right through their bills to find food? It's like having a built-in spaghetti strainer. Evolution is wild! 🍝🦆"
        #         },
        #         {
        #             "user_id": "@WildlifeWonders",
        #             "user_name": "Nature's Marvels",
        #             "datetime": "Just now",
        #             "text": "The variety in bill shapes even among ducks is a testament to evolutionary adaptation. From broad bills to narrow ones, each is tailored to their specific diet and habitat. #Biodiversity"
        #         },
        #         {
        #             "user_id": "@DuckLore",
        #             "user_name": "The Quacken",
        #             "datetime": "Just now",
        #             "text": "Ducks also use their bills for grooming and to regulate their temperature, showing just how important this tool is beyond just feeding. It's their multi-purpose gadget! 🌡️🛁"
        #         },
        #     ]
        # })

api.add_namespace(api_namespace)

# Start the Flask application
if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
    # c = llm.Chat(db, 0, 0)
    # import IPython; IPython.embed(colors='linux')