class ChatMemory:

    def __init__(self):
        self.sessions = {}

    def add_message(self, session_id, role, message):

        if session_id not in self.sessions:
            self.sessions[session_id] = []

        self.sessions[session_id].append({
            "role": role,
            "message": message
        })

    def get_history(self, session_id):
        return self.sessions.get(session_id, [])
