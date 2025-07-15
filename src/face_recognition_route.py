import requests
from requests.exceptions import ConnectionError
from fastapi import APIRouter, UploadFile, File, HTTPException

from src.metrics import total_face_recognitions
from src.models import RecognitionResult, UserPublicProfile
from src.settings import settings

router = APIRouter(prefix="/recognise")

@router.post("/")
def handle_face_recognition(file: UploadFile = File(...)) -> RecognitionResult:  # add cashier access level later
    """
    Steps:
    1. Invoke face recognition endpoint
    2. If the face WAS NOT recognised as an existing user:
        2.1. Request a temporal user ID from user data service
        2.2. Associate the new face with the allocated ID on the face recognition endpoint side
        2.3. Return the new uid for further registration
    3. If the face WAS recognised as an existing user:
        3.1. Fetch user information
        3.2 Return the user to the frontend
    """
    file_to_send = (file.filename, file.file, file.content_type)  # establish the file format
    try:
        result = requests.post(settings.face_recognition_endpoint.encoded_string() + "/frontend/recognise",
                               files={"file": file_to_send},
                               timeout=10)
    except (ConnectionError, TimeoutError) as e:
        print("handle_face_recognition 1", e)
        raise HTTPException(status_code=550, detail="Face recognition service not available")
    total_face_recognitions.inc()
    print("after initial recognition request", result.status_code, result.text)
    recognition_result = result.json()
    if recognition_result["new"]:
        # handle new user creation
        try:
            temporal_user_response = requests.post(settings.user_endpoint.encoded_string() + "temp_user", timeout=10)
        except (ConnectionError, TimeoutError) as e:
            print("handle_face_recognition 2", e)
            raise HTTPException(status_code=550, detail="User service not available")
        jsonned_temporal_user_response = temporal_user_response.json()
        print("2.1", temporal_user_response.status_code, temporal_user_response.text)
        try:
            print(f'Transforming uid {recognition_result["uid"]} into {jsonned_temporal_user_response["uid"]}')
            result_id_update = requests.post(settings.face_recognition_endpoint.encoded_string() + "/frontend/assign_uid",
                                             json={"new_uid": jsonned_temporal_user_response["uid"],
                                         "old_uid": recognition_result["uid"]},
                                             timeout=10)
        except (ConnectionError, TimeoutError) as e:
            print("handle_face_recognition 3", e)
            raise HTTPException(status_code=550, detail="Face recognition service not available")
        print("2.2", result_id_update.status_code, result_id_update.text)
        if result_id_update.status_code != 200:
            raise HTTPException(status_code=550, detail="Face recognition service raised error")
        return RecognitionResult(assummed_new=True, uid=jsonned_temporal_user_response["uid"])
    # handle existing user
    try:
        user_details = requests.get(settings.user_endpoint.encoded_string() + f"/user/{recognition_result['uid']}",
                                    timeout=10)
    except (ConnectionError, TimeoutError) as e:
        print("handle_face_recognition 4", e)
        raise HTTPException(status_code=550, detail="User service not available")
    if user_details.status_code != 200:
        print("3.1", user_details.status_code, user_details.text)
    if user_details.status_code == 404:
        return RecognitionResult(assummed_new=True, uid=recognition_result["uid"])
    jsonned_user_details = user_details.json()
    return RecognitionResult(assummed_new=False, uid=recognition_result["uid"], user=UserPublicProfile.model_validate(jsonned_user_details))
