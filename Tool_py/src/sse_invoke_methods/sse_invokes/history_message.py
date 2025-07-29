import os
import json

HISTORY_FILE = "chatglm_history.json"

class HistoryMessage:
    def __init__(self):
        self.history_file_path = HISTORY_FILE
        # self.create_history_file_if_not_exists(self.history_file_path)

    @staticmethod
    def create_history_file_if_not_exists(file_path):
        if not os.path.exists(file_path):
            try:
                with open(file_path, 'w') as f:
                    pass
            except Exception as err:
                print(f"Failed to create history file: {err}")

    def add_history_to_file(self, role, content):
        json_data = self.create_json(role, content)
        try:
            with open(self.history_file_path, 'a',encoding='utf-8') as file:
                file.write(f"{json_data},\n")
        except Exception as err:
            print(f"Failed to write to history file: {err}")
        return json_data

    def create_json(self, role, content):
        history = {
            "role": role,
            "content": content
        }
        return json.dumps(history, ensure_ascii=False)

    def load_history_from_file(self):
        try:
            with open(self.history_file_path, 'r',encoding='utf-8') as file:
                lines = file.readlines()
                return ''.join(line for line in lines)
        except Exception as err:
            print(f"Failed to open history file for reading: {err}")
            return ""