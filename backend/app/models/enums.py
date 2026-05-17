import enum


class UserRole(str, enum.Enum):
    Parent = "Parent"
    Teacher = "Teacher"
    Manager = "Manager"


class IncidentCategory(str, enum.Enum):
    Critical = "Critical"
    Warning = "Warning"


class IncidentType(str, enum.Enum):
    Fall = "Fall"
    Violence = "Violence"


class CameraStatus(str, enum.Enum):
    Active = "Active"
    Offline = "Offline"
    Maintenance = "Maintenance"
