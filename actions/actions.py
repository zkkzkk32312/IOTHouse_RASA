# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

# from typing import Any, Text, Dict, List
#
# from rasa_sdk import Action, Tracker
# from rasa_sdk.executor import CollectingDispatcher
#
#
# class ActionHelloWorld(Action):
#
#     def name(self) -> Text:
#         return "action_hello_world"
#
#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#
#         dispatcher.utter_message(text="Hello World!")
#
#         return []

import requests
import os
import pprint
import pathlib
import json
import re
import pandas as pd
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet

API_BASE_URL = "https://sample-iot.zackcheng.com"
API_DEVICE_ENDPOINT = "/devices"
API_TELEMETRY_ENDPOINT = "/telemetry"

class DevicesAPI(object):
    def __init__(self):
        self.devices = None

    def fetch_devices(self):
        if self.devices is not None:
            return self.devices

        try:
            self.devices = pd.read_json("datasets/Device/Devices.json")
        except FileNotFoundError:
            print(f"Error: The file 'Devices.json' was not found.")
            return None
        except json.JSONDecodeError:
            print(f"Error parsing JSON in 'Devices.json'.")
            return None
        return self.devices

    def format_devices(self, header=True) -> str:
        if self.devices is not None:
            formatted_devices = self.devices.to_json(orient="records")
            return formatted_devices
        else:
            print("Error: Devices data was not fetched successfully.")
            return None
        
class TelemetryAPI(object):
    def __init__(self):
        self.telemetries = None

    def fetch_telemetries(self):
        if self.telemetries is not None:
            return self.telemetries
        
        dfs = {}
        for file in pathlib.Path("datasets/Telemetry/").glob("*.csv"):
            match = re.search(r'(\d+)', file.name)
            if match:
                try:
                    id = match.group(1)
                    df = pd.read_csv(file)
                    dfs[id] = df
                except FileNotFoundError as e:
                    print(f"Error: The following files were not found: {e}")
                    return None
                except pd.errors.EmptyDataError:
                    print(f"Error: The file is empty.")
                    return None
                except pd.errors.ParserError:
                    print(f"Error parsing CSV.")
                    return None
                except AttributeError:
                    print("AttributeError.")
                    return None
        self.telemetries = dfs
        return self.telemetries
    
    def format_telemetries(self, header=True) -> str:
        if self.telemetries is not None and isinstance(self.telemetries, dict) and len(self.telemetries) > 0:
            formatted_telemetries = json.dumps([self.telemetries], default=str)
            return formatted_telemetries
        else:
            print("Error: Telemetry data was not fetched successfully.")
            return None

class DeviceTelemetryAPI(object):
    def __init__(self):
        self.devices_api = DevicesAPI()
        self.telemetry_api = TelemetryAPI()
        self.deviceTelemetry = None

    def fetch_device_telemetry(self):
        if self.deviceTelemetry is not None:
            return self.deviceTelemetry
        
        devices_list = self.devices_api.fetch_devices().to_dict(orient='records')
        telemetries = self.telemetry_api.fetch_telemetries()

        for device in devices_list:
            id = device["DeviceId"]
            telemetry = telemetries.get(str(id), [])
            device["TelemetrySimulationData"] = telemetry.to_dict(orient='records')
        
        self.deviceTelemetry = json.dumps(devices_list)
        return self.deviceTelemetry

class ChatGPT(object):
    def __init__(self):
        self.url = "https://api.openai.com/v1/chat/completions"
        self.model = "gpt-3.5-turbo"
        self.headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"
        }
        self.prompt = "Answer the following question, based on the data shown. " \
            "Answer in a complete sentence and don't say anything else."

    def ask(self, data, question):
        content  = self.prompt + "\n\n" + data + "\n\n" + question
        body = {
            "model":self.model, 
            "messages":[{"role": "user", "content": content}]
        }
        print(body)
        result = requests.post(
            url=self.url,
            headers=self.headers,
            json=body,
        )
        print(result)
        return result.text #json()#["choices"][0]["message"]["content"]

class Ollama(object):
    def __init__(self):
        self.url = "http://localhost:11434/api/chat"  # Target your local Ollama instance
        self.model = "llama3.2:latest"
        self.stream = False
        self.headers={
            "Content-Type": "application/json"
        }
        self.prompt = (
            "You are a friendly and conversational assistant, designed solely to discuss information about devices and their telemetry data. "
            "It is essential that you do not, under any circumstances, provide any responses, examples, or advice related to programming, coding, technical tasks, or data manipulation. "
            "Please refrain from including any form of code snippets, scripts, or explanations about data handling or analysis techniques. "
            "The provided data is a JSON string of devices, where each device contains fields such as DeviceType, DeviceId, TelemetryNames, and TelemetrySimulationData. "
            "Each telemetry entry in TelemetrySimulationData includes only the hour and minute of the measurement time, with the data pattern repeating every day in the same sequence. "
            "Now, based on this data, answer the following question with information relevant only to the context of devices and telemetry, completely avoiding any reference to programming, coding, or data processing methods:"
        )

    def ask(self, question, data=None):
        content  = self.prompt + "\n\n" + question + "\n\n" + (data if data is not None else "")

        body = {
            "model": self.model,
            "stream": self.stream,
            "messages":[{"role": "user", "content": content}]
        }
        #print(body)
        result = requests.post(
            url=self.url,
            headers=self.headers,
            json=body,
        )
        return result.json()["message"]["content"]

devices_api = DevicesAPI()
telemetries_api = TelemetryAPI()
deviceTelemetry_api = DeviceTelemetryAPI()
chatGPT = ChatGPT()
ollama = Ollama()

class ActionGetDevices(Action):
    def name(self):
        return "action_get_devices"

    def run(self, dispatcher, tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("ActionGetDevices.run")
        devices = devices_api.fetch_devices()
        print(devices)
        devices = devices_api.format_devices(devices)
        print(devices)
        question = tracker.latest_message["text"]
        print(question)
        answer = ollama.ask(question, devices)
        dispatcher.utter_message(text = answer)

class ActionGetTelemetries(Action):
    def name(self):
        return "action_get_telemetries"

    def run(self, dispatcher, tracker, domain):
        print("ActionGetTelemetries.run")
        telemetries = telemetries_api.fetch_telemetries()
        #print(telemetries)
        pprint.pprint(dict(list(telemetries.items())[:2]))
        telemetries = telemetries_api.format_telemetries(telemetries)
        #print(telemetries)
        pprint.pprint(dict(list(telemetries.items())[:2]))
        question = tracker.latest_message["text"]
        print(question)
        answer = ollama.ask(question, telemetries)
        dispatcher.utter_message(text = answer)

#Default action
class ActionDefault(Action):
    def name(self):
        return "action_default"
    
    def run(self, dispatcher, tracker, domain):
        print("ActionDefault.run")
        question = tracker.latest_message["text"]
        print(question)
        deviceTelemetry = deviceTelemetry_api.fetch_device_telemetry()
        # print(deviceTelemetry)
        answer = ollama.ask(question, deviceTelemetry)
        dispatcher.utter_message(text = answer)