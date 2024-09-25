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
from rasa_sdk import Action, Tracker

API_BASE_URL = "https://sample-iot.zackcheng.com"
API_DEVICE_ENDPOINT = "/devices"
API_TELEMETRY_ENDPOINT = "/telemetry"

class ActionGetDevices(Action):
    def name(self):
        return "action_get_devices"

    def run(self, dispatcher, tracker, domain):
        device_id = tracker.get_slot("device_id")
        devices = self.get_devices(dispatcher, domain, device_id)
        dispatcher.utter_message(f"Device info for ID {device_id}: {devices}")

    def get_devices(self, dispatcher, domain, device_id):
        api_url = f"{API_BASE_URL}{API_DEVICE_ENDPOINT}/{device_id}"
        print(device_id)
        print(api_url)

        response = requests.get(api_url)
        if response.status_code == 200:
            return response.json()
        else:
            dispatcher.utter_message(f"Error retrieving device information: {response.status_code}")
            return None

class ActionGetTelemetries(Action):
    def name(self):
        return "action_get_telemetries"

    def run(self, dispatcher, tracker, domain):
        device_id = tracker.get_slot("device_id")
        telemetry_data = self.get_telemetries(dispatcher, domain, device_id)
        dispatcher.utter_message(f"Telemetry data for device {device_id}: {telemetry_data}")

    def get_telemetries(self, dispatcher, domain, device_id):
        api_url = f"{API_BASE_URL}{API_TELEMETRY_ENDPOINT}/{device_id}"
        print(device_id)
        print(api_url)

        response = requests.get(api_url)
        if response.status_code == 200:
            return response.json()
        else:
            dispatcher.utter_message(f"Error retrieving telemetry data: {response.status_code}")
            return None
