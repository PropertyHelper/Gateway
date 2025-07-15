from prometheus_client import Counter

total_face_recognitions = Counter(
    "face_recognitions",
    "Total number of face recognition requests"
)

total_merged_recognitions = Counter(
    "merged_recognitions",
    "Number of recognitions when a known user was classified as new"
)

total_confused_recognitions = Counter(
    "confused_recognitions",
    "Number of recognitions when one user was confused with another existing user"
)
