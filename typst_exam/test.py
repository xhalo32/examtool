from unittest import TestCase
from typst_exam import *

example_typst_code="""
= h (lottery 1)
a
== q
p
+ a1 (correct)
+ a2
"""

def test_example():
    assert parse_typst_exam(example_typst_code) == [
        {
            "name": "h",
            "description": "a\n",
            "lotteryOn": True,
            "lotteryItemCount": 1,
            "questions": [
                {
                    "typst": "p\n",
                    "options": [
                        {"option": "a1", "correctOption": True},
                        {"option": "a2", "correctOption": False}
                    ],
                    "html": "<p>p</p>"
                }
            ]
        }
    ]