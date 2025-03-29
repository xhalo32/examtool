import requests, os
headers = {
    'Accept': 'application/json',
}

generated_tag = "examtool_generated"

def is_login(response):
    return "Aalto University Login" in response.text

def is_csrf_error(response):
    return "No CSRF token found in headers" in response.text

def raise_for_status_with_body(response):
    """
    Checks the response and raises an HTTPError with the response body if the response is not OK.
    """
    try:
        response.raise_for_status()
    except requests.HTTPError as err:
        # Append the response body to the exception message
        raise requests.HTTPError(
            f"{err}: response body '{response.text}'",
            response=response
        ) from None

def handle_error_response(resp):
    if is_login(resp):
        raise requests.HTTPError("response was login page (make sure cookies are fresh)", response=resp)
    if is_csrf_error(resp):
        raise requests.HTTPError("response was CSRF error", response=resp)
    raise_for_status_with_body(resp)
    return resp


def get_exams(client):
    resp = client.get(f'https://exam.aalto.fi/app/reviewerexams', headers=headers)
    return handle_error_response(resp).json()

def get_exam(client, exam_id: int):
    resp = client.get(f'https://exam.aalto.fi/app/exams/{str(exam_id)}', headers=headers)
    return handle_error_response(resp).json()

# A successful request, returns at least `.id: int` and `.sequence_number: int`
def create_section(client, exam_id: int):
    """
    Create a new section under exam `exam_id`.
    
    Does not support name, description etc. Use `edit_section` to provide them.
    """
    resp = client.post(f'https://exam.aalto.fi/app/exams/{str(exam_id)}/sections', headers=headers)
    return handle_error_response(resp).json()

def edit_section(client, exam_id: int, section_id: int, name: str, description: str, lottery_on: bool = False, lottery_item_count: int = None):
    """
    Currently does not support leaving name and description out.
    
    Notice that the EXAM API returns `lotteryItemCount: 1` even when given a 0 as the count is 0 by default, but all validations ensure it's > 0. It also seems to support saving a higher number than there are questions in the section.
    """
    resp = client.put(f'https://exam.aalto.fi/app/exams/{str(exam_id)}/sections/{str(section_id)}', headers=headers, json={
        "name": name,
        "description": description,
        "lotteryOn": lottery_on,
        "lotteryItemCount": lottery_item_count,
        # expanded
        # optional
    })
    return handle_error_response(resp).json()

def delete_section(client, exam_id: int, section_id: int):
    resp = client.delete(f'https://exam.aalto.fi/app/exams/{str(exam_id)}/sections/{str(section_id)}', headers=headers)
    handle_error_response(resp)

# TODO handle response body: sitnet_question_already_in_section
def add_question(client, exam_id: int, section_id: int, sequence_number: int, question_id: int):
    resp = client.post(f'https://exam.aalto.fi/app/exams/{str(exam_id)}/sections/{str(section_id)}/questions', headers=headers, json={
        "sequenceNumber": sequence_number,
        "questions": str(question_id)
    })
    return handle_error_response(resp).json()

def remove_question(client, exam_id: int, section_id: int, question_id: int):
    resp = client.delete(f'https://exam.aalto.fi/app/exams/{str(exam_id)}/sections/{str(section_id)}/questions/{str(question_id)}', headers=headers)
    handle_error_response(resp)

# Deletes the question from the "question bank"
def delete_question(client, question_id: int):
    resp = client.delete(f'https://exam.aalto.fi/app/questions/{str(question_id)}', headers=headers)
    handle_error_response(resp)

# Gets all questions from the "question bank"
def get_questions(client):
    resp = client.get(f'https://exam.aalto.fi/app/questions', headers=headers)
    return handle_error_response(resp).json()

def mk_question_data(owner_id: int, default_max_score: int, question: str, options: list, tags=[]):
    template_option = {
                "correctOption": False,
                "defaultScore": 0
            }
    options = list(map(lambda op: {**template_option, **op}, options))
    assert len(options) > 1
    assert all(map(lambda op: op['defaultScore'] == 0, options)) or len(filter(lambda op: op['correctOption'] == True, options)) == 1 # TODO haven't tested whether this matches the platform behavior

    data = {
        "type": "MultipleChoiceQuestion",
        "defaultMaxScore": default_max_score,
        "question": question,
        "questionOwners": [
            {
                "id": owner_id,
            }
        ],
        "tags": [{
            "name": generated_tag
        }, *map(lambda tag: {"name": tag}, tags)],
        "options": options
    }
    return data

def edit_question(client, question_id: int, owner_id: int, default_max_score: int, question: str, options: list, tags=[]):
    """
    Unlike with `create_question`, the platform supports URI sensitive characters in the question `option` through this endpoint.

    Each option should contain the ID of the option that is being replaced.
    """
    resp = client.put(f'https://exam.aalto.fi/app/questions/{str(question_id)}', headers=headers, json=mk_question_data(owner_id, default_max_score, question, options, tags))
    return handle_error_response(resp).json()

# TODO add a tag to all questions created with examtool for automated deletion. with this the tool doesn't need to store state
def create_question(client, owner_id: int, default_max_score: int, question: str, options: list, tags=[]):
    """
    Create a new question in the "question bank".

    Currently only supports multiple choice questions.

    Options is a list of answer options. Each option must contain the string `option: str`.
    - For "single correct" set `correctOption` to True on exactly one of the options and leave `defaultScore` unset.
    - For "many correct" set `defaultScore` appropriately for each question and leave `correctOption` unset.
    
    `option` should not contain URI sensitive characters, as the platform encodes them. Use `edit_question` to fix.

    Use `tags` to define extra tags, such as exam id or section id. They are useful if you want to delete all questions in an exam.
    """
    resp = client.post(f'https://exam.aalto.fi/app/questions', headers=headers, json=mk_question_data(owner_id, default_max_score, question, options, tags))
    return handle_error_response(resp).json()
