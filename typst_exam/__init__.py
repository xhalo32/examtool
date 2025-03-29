import re, markdown
from examtool.sdk import *
from examtool import init_client

def to_html(typst: str):
    """
    Currently we simply use markdown to convert typst into HTML
    """
    return markdown.markdown(typst, extensions=['fenced_code'])

def parse_typst_exam(typst_code):
    sections = []
    current_section = None
    current_question = None
    
    lines = typst_code.strip().splitlines()
    section_pattern = re.compile(r'^= (.+?)( \(lottery ([0-9]+)\))?$')
    question_pattern = re.compile(r'^==.*$')
    option_pattern = re.compile(r'^\+ (.+?)( \((correct)\))?$')

    for line in lines:
        section_match = section_pattern.match(line)
        if section_match:
            if current_section:
                if current_question:
                    current_section["questions"].append(current_question)
                    current_question = None
                sections.append(current_section)
            
            current_section = {
                # EXAM does not support HTML in name or description
                "name": section_match.group(1),
                "description": "",
                "questions": []
            }
            count = section_match.group(3)
            if count:
                current_section["lotteryOn"] = True
                current_section["lotteryItemCount"] = int(count)
            continue
        
        question_match = question_pattern.match(line)
        if question_match:
            if current_question:
                current_section["questions"].append(current_question)
                
            current_question = {
                "typst": "",
                "options": []
            }
            continue
        
        option_match = option_pattern.match(line)
        if option_match:
            option = option_match.group(1)
            correct = bool(option_match.group(3))
            current_question["options"].append({"option": option, "correctOption": correct})
            continue

        if current_question:
            current_question["typst"] += line + "\n"
        elif current_section:
            current_section["description"] += line + "\n"
    
    # Appending leftover section and question
    if current_question:
        current_section["questions"].append(current_question)
        
    if current_section:
        sections.append(current_section)
    
    for section in sections:
        for question in section['questions']:
            question['html'] = to_html(question['typst'])

    return sections

def main():
    import argparse
    from json import dumps
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="Typst EXAM file path")
    args = parser.parse_args()
    with open(args.path) as f: s = f.read()
    print(dumps(parse_typst_exam(s)))


if __name__=="__main__":
    main()