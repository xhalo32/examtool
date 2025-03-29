from .sdk import *
import argparse, json
from requests import Session

def mitmproxy_session():
    s = requests.Session()
    s.proxies.update({"https": "https://localhost:8080"})
    s.verify = False
    return s

def cookies_from_env(env_name):
    cookies = {}
    for cookie in os.environ.get(env_name, "").split(';'):
        if '=' in cookie:
            key, value = cookie.strip().split('=', 1)
            cookies[key] = value
    return cookies    

def init_client(client):
    cookies = cookies_from_env("EXAM_COOKIE")
    for key, value in cookies.items():
        client.cookies.set(key, value)
    client.headers.update({"X-XSRF-TOKEN": cookies.get("XSRF-TOKEN", "")})
    return client

def print_json(data):
    print(json.dumps(data))

def add_exam_id_argument(subparser):
    subparser.add_argument('exam_id', type=int, help='This can be found from the URL of the webpage when editing an exam.')

def add_section_id_argument(subparser):
    subparser.add_argument('section_id', type=int, help='This is the ID of the section (aihealue) in an exam. This can be found under `examSections` whe getting an exam.')

def add_question_id_argument(subparser):
    subparser.add_argument('question_id', type=int, help='This is the ID of the question in a section.')

def add_owner_id_argument(subparser):
    subparser.add_argument('owner_id', type=int, help='This is the ID of the owner of the exercise. This can be found by e.g. getting all exams.')

# Exam import

def validate_exam(exam):
    for section in exam:
        # check that lotteryOn and lotteryItemCount are either both present or both not
        assert ('lotteryOn' in section) == ('lotteryItemCount' in section)

        # check that lotteryItemCount is at most the number of questions
        if 'lotteryItemCount' in section:
            assert 'lotteryOn' in section and section['lotteryOn']
            assert section['lotteryItemCount'] <= len(section['questions']), f"lotteryItemCount > number of questions: {section}"

        # check that all questions have at least 2 options and at least one correct
        for question in section['questions']:
            assert len(question['options']) > 1, f"number of options < 2: {question}"
            assert any(map(lambda op: op['correctOption'], question['options'])), f"missing correct: {question}"

def delete_exam_questions(client, exam_id):
    """
    Deletes all questions with both tags 'examtool_generated' and 'examtool_<exam_id>'
    """
    for question in get_questions(client):
        tags = map(lambda tag: tag["name"], question["tags"])
        if "examtool_generated" in tags and f"examtool_{exam_id}" in tags:
            id = question["id"]
            print(f"Deleting question {id}")
            delete_question(client, id)

def delete_sections(client, exam_id):
    print(f"Deleting all sections from exam {exam_id}")
    exam = get_exam(client, exam_id)
    for section in exam["examSections"]:
        delete_section(client, exam_id, section["id"])

def main():
    client = init_client(Session())
    # client = init_client(mitmproxy_session())

    parser = argparse.ArgumentParser(description='Exam Manager CLI')
    subparsers = parser.add_subparsers(dest='verb', required=True)

    # Subparsers for 'get'
    parser_get = subparsers.add_parser('get', help='Get information about an EXAM object, or objects.')
    get_subparsers = parser_get.add_subparsers(dest='subject', required=True)
    
    parser_get_exams = get_subparsers.add_parser('exams')

    parser_get_exam = get_subparsers.add_parser('exam')
    add_exam_id_argument(parser_get_exam)
    
    parser_get_questions = get_subparsers.add_parser('questions')

    # Subparsers for 'add'
    parser_add = subparsers.add_parser('add', help='Add objects to an exam. Use the remove subcommand to remove them.')
    add_subparsers = parser_add.add_subparsers(dest='subject', required=True)
    
    parser_add_question = add_subparsers.add_parser('question')
    add_exam_id_argument(parser_add_question)
    add_section_id_argument(parser_add_question)
    parser_add_question.add_argument('sequence_number', type=int)
    add_question_id_argument(parser_add_question)

    # Subparsers for 'edit'
    parser_edit = subparsers.add_parser('edit', help='Edit an EXAM object. Usually completely replaces the old object with the new information.')
    edit_subparsers = parser_edit.add_subparsers(dest='subject', required=True)
    
    parser_edit_section = edit_subparsers.add_parser('section')
    add_exam_id_argument(parser_edit_section)
    add_section_id_argument(parser_edit_section)
    parser_edit_section.add_argument('name', type=str)
    parser_edit_section.add_argument('description', type=str)
    parser_edit_section.add_argument('--lottery-on', action='store_true')
    parser_edit_section.add_argument('--lottery-item-count', type=int, required=False)

    parser_edit_question = edit_subparsers.add_parser('question')
    add_question_id_argument(parser_edit_question)
    add_owner_id_argument(parser_edit_question)
    parser_edit_question.add_argument('default_max_score', type=int)
    parser_edit_question.add_argument('question', type=str)
    parser_edit_question.add_argument('options', type=json.loads)
    parser_edit_question.add_argument('--tags', type=json.loads, required=False, default=[])

    # Subparsers for 'remove'
    parser_remove = subparsers.add_parser('remove', help='Remove an object from an exam. Removing differs from deleting as it does not delete the information in the object, but "unlinks" it instead.')
    remove_subparsers = parser_remove.add_subparsers(dest='subject', required=True)

    parser_remove_question = remove_subparsers.add_parser('question')
    add_exam_id_argument(parser_remove_question)
    add_section_id_argument(parser_remove_question)
    add_question_id_argument(parser_remove_question)

    # Subparsers for 'delete'
    parser_delete = subparsers.add_parser('delete', help='Permanently delete an object. Deleting differs from removing as it deletes the object and removes it from all assoaciated objects too.')
    delete_subparsers = parser_delete.add_subparsers(dest='subject', required=True)

    parser_delete_section = delete_subparsers.add_parser('section')
    add_exam_id_argument(parser_delete_section)
    add_section_id_argument(parser_delete_section)

    parser_delete_question = delete_subparsers.add_parser('question')
    add_question_id_argument(parser_delete_question)

    # Subparser for 'create'
    parser_create = subparsers.add_parser('create', help='Create new objects. Use the delete subcommand to permanently delete them.')
    create_subparsers = parser_create.add_subparsers(dest='subject', required=True)

    parser_create_section = create_subparsers.add_parser('section')
    add_exam_id_argument(parser_create_section)

    parser_create_question = create_subparsers.add_parser('question')
    add_owner_id_argument(parser_create_question)
    parser_create_question.add_argument('default_max_score', type=int)
    parser_create_question.add_argument('question', type=str)
    parser_create_question.add_argument('options', type=json.loads)
    parser_create_question.add_argument('--tags', type=json.loads, required=False, default=[])

    # Subparser for 'import'
    parser_import = subparsers.add_parser('import', help='Import an exam from a JSON file. This will **nuke** the exam first! Lottery is disabled and questions score 1 point by default. Notice that lottery is available only if all points within a section are equal.')
    add_exam_id_argument(parser_import)
    add_owner_id_argument(parser_import)
    parser_import.add_argument('file', type=str)

    args = parser.parse_args()

    kwargs = vars(args)
    verb = kwargs.pop('verb')
    if verb == None:
        parser.print_help()

    elif verb == 'import':
        with open(args.file) as f: exam = json.load(f)
        validate_exam(exam)
        
        exam_id = args.exam_id
        delete_exam_questions(client, exam_id)
        delete_sections(client, exam_id)
        num_sections = len(exam)
        for i, section in enumerate(exam):
            print(f"Creating section {i + 1}/{num_sections}")
            section_id = create_section(client, exam_id)['id']
            edit_section(client, exam_id, section_id, name=section["name"], description=section["description"], lottery_on=section.get("lotteryOn", False), lottery_item_count=section.get("lotteryItemCount", None))

            num_questions = len(section["questions"])
            for i, question in enumerate(section["questions"]):
                print(f"Creating question {i + 1}/{num_questions}")
                # print(question["options"])
                default_max_score=question.get("points", 1)
                html=question["html"]
                options=question["options"]
                tags=[f"examtool_{exam_id}"]
                question = create_question(client, args.owner_id, default_max_score, html, options, tags)
                option_ids = map(lambda op: op['id'], question["options"])

                # HACK: workaround to support URI sensitive characters in question options.
                # We edit each question with "no change" except that we provide the option ids the previous query returned.
                # No need to maintain the correct order of ids, we are anyways overwriting the options with new ones.
                new_options = list([{"id": id, **opt} for id, opt in zip(option_ids, options)])
                edit_question(client, question['id'], args.owner_id, default_max_score, html, new_options, tags)

                add_question(client, exam_id, section_id, 0, question['id'])
        return
    
    subject = kwargs.pop('subject')
    if subject == None:
        parser.print_help()

    if verb == 'get':
        if subject == 'exams':
            print_json(get_exams(client))
        elif subject == 'exam':
            print_json(get_exam(client, args.exam_id))
        elif subject == 'questions':
            print_json(get_questions(client))

    elif verb == 'add':
        if subject == 'question':
            print_json(add_question(client, **kwargs))

    elif verb == 'create':
        if subject == 'section':
            print_json(create_section(client, **kwargs))
        elif subject == 'question':
            print_json(create_question(client, **kwargs))

    elif verb == 'edit':
        if subject == 'section':
            print_json(edit_section(client, **kwargs))
        elif subject == 'question':
            print_json(edit_question(client, **kwargs))

    elif verb == 'remove':
        if subject == 'question':
            remove_question(client, **kwargs)

    elif verb == 'delete':
        if subject == 'section':
            delete_section(client, **kwargs)
        elif subject == 'question':
            delete_question(client, **kwargs)

if __name__ == '__main__':
    main()