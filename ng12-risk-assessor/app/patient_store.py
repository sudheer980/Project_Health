import json
from typing import Optional
from app.models import Patient
from app.config import settings

class PatientStore:
    def __init__(self, path: str = settings.patients_path):
        self.path = path
        self._cache = None

    def _load(self):
        if self._cache is None:
            with open(self.path, "r", encoding="utf-8") as f:
                self._cache = json.load(f)

    def get_patient(self, patient_id: str) -> Optional[Patient]:
        self._load()
        for row in self._cache:
            if row.get("patient_id") == patient_id:
                return Patient(**row)
        return None
