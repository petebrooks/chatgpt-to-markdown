import os
import tempfile
import unittest
from unittest.mock import patch
from chatgpt_to_markdown import chatgpt_to_markdown, format_date


class TestChatgptToMarkdown(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="chatgpt_to_markdown-")

    def tearDown(self):
        for root, dirs, files in os.walk(self.temp_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(self.temp_dir)

    def test_should_write_markdown_file_for_each_conversation(self):
        json = [
            {
                "title": "Test Conversation",
                "create_time": 1630454400,
                "update_time": 1630458000,
                "mapping": {
                    "0": {
                        "message": {
                            "author": {"role": "user", "name": "John"},
                            "content": {"content_type": "text", "parts": ["Hello"]},
                        }
                    }
                },
            }
        ]

        chatgpt_to_markdown(json, self.temp_dir)

        file_path = os.path.join(self.temp_dir, "Test Conversation.md")
        with open(file_path, "r", encoding="utf8") as file:
            file_content = file.read()

        self.assertEqual(
            file_content,
            f"# Test Conversation\n\n- Created: {format_date(1630454400 * 1000)}\n- Updated: {format_date(1630458000 * 1000)}\n\n## user (John)\n\n    Hello\n\n",
        )

    def test_should_handle_titles_with_html_tags(self):
        json = [
            {
                "title": "<h1>Test Conversation</h1>",
                "create_time": 1630454400,
                "update_time": 1630458000,
                "mapping": {},
            }
        ]
        chatgpt_to_markdown(json, self.temp_dir)
        with open(
            os.path.join(self.temp_dir, "h1 Test Conversation h1.md"),
            "r",
            encoding="utf8",
        ) as file:
            file_content = file.read()
        self.assertIn("# `<h1>`Test Conversation`</h1>`\n", file_content)

    def test_should_sanitize_titles_with_invalid_filename_characters(self):
        json = [
            {
                "title": ":/In\\<>*valid|?",
                "create_time": 1630454400,
                "update_time": 1630458000,
                "mapping": {},
            }
        ]
        chatgpt_to_markdown(json, self.temp_dir)
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, "In valid.md")))

    def test_should_handle_custom_date_format_functions(self):
        json = [
            {
                "title": "Test Conversation",
                "create_time": 1630454400,
                "update_time": 1630458000,
                "mapping": {},
            }
        ]
        custom_date_format = lambda date: date.isoformat()
        chatgpt_to_markdown(json, self.temp_dir, {"date_format": custom_date_format})
        with open(
            os.path.join(self.temp_dir, "Test Conversation.md"), "r", encoding="utf8"
        ) as file:
            file_content = file.read()
        self.assertIn("- Created: 2021-09-01T00:00:00.000Z\n", file_content)

    def test_should_ignore_messages_with_no_content(self):
        json = [
            {
                "title": "Test Conversation",
                "create_time": 1630454400,
                "update_time": 1630458000,
                "mapping": {
                    "0": {
                        "message": {
                            # no content property
                        }
                    }
                },
            }
        ]
        chatgpt_to_markdown(json, self.temp_dir)
        with open(
            os.path.join(self.temp_dir, "Test Conversation.md"), "r", encoding="utf8"
        ) as file:
            file_content = file.read()
        self.assertNotIn("## user (John)", file_content)

    def test_should_ignore_messages_with_empty_content(self):
        json = [
            {
                "title": "Test Conversation",
                "create_time": 1630454400,
                "update_time": 1630458000,
                "mapping": {
                    "0": {"message": {"content": {"content_type": "text", "parts": []}}}
                },
            }
        ]
        chatgpt_to_markdown(json, self.temp_dir)
        with open(
            os.path.join(self.temp_dir, "Test Conversation.md"), "r", encoding="utf8"
        ) as file:
            file_content = file.read()
        self.assertNotIn("## user (John)", file_content)

    def test_should_handle_tether_browsing_display_content(self):
        json = [
            {
                "title": "Test Conversation",
                "create_time": 1630454400,
                "update_time": 1630458000,
                "mapping": {
                    "0": {
                        "message": {
                            "author": {"role": "tool", "name": "browser"},
                            "content": {
                                "content_type": "tether_browsing_display",
                                "result": "L0: x",
                            },
                        }
                    }
                },
            }
        ]
        chatgpt_to_markdown(json, self.temp_dir)
        with open(
            os.path.join(self.temp_dir, "Test Conversation.md"), "r", encoding="utf8"
        ) as file:
            file_content = file.read()
        self.assertIn("```\nL0: x\n```", file_content)

    def test_should_handle_tether_quote_content(self):
        json = [
            {
                "title": "Test Conversation",
                "create_time": 1630454400,
                "update_time": 1630458000,
                "mapping": {
                    "0": {
                        "message": {
                            "author": {"role": "tool", "name": "browser"},
                            "content": {
                                "content_type": "tether_quote",
                                "url": "x.com",
                                "domain": "x.com",
                                "title": "T",
                                "text": "X",
                            },
                        }
                    }
                },
            }
        ]
        chatgpt_to_markdown(json, self.temp_dir)
        with open(
            os.path.join(self.temp_dir, "Test Conversation.md"), "r", encoding="utf8"
        ) as file:
            file_content = file.read()
        self.assertIn("```\nT (x.com)\n\nX\n```", file_content)

    def test_should_handle_multimodal_text_content(self):
        json = [
            {
                "title": "Test Conversation",
                "create_time": 1630454400,
                "update_time": 1630458000,
                "mapping": {
                    "0": {
                        "message": {
                            "author": {"role": "tool", "name": "dalle.text2im"},
                            "content": {
                                "content_type": "multimodal_text",
                                "parts": [
                                    {
                                        "content_type": "image_asset_pointer",
                                        "width": 1024,
                                        "height": 1024,
                                        "metadata": {"dalle": {"prompt": "Photo"}},
                                    },
                                    {
                                        "content_type": "image_asset_pointer",
                                        "width": 1024,
                                        "height": 1024,
                                    },
                                    {"content_type": "some_other_type"},
                                ],
                            },
                        }
                    }
                },
            }
        ]
        chatgpt_to_markdown(json, self.temp_dir)
        with open(
            os.path.join(self.temp_dir, "Test Conversation.md"), "r", encoding="utf8"
        ) as file:
            file_content = file.read()
        self.assertIn("Image (1024x1024): Photo\n", file_content)
        self.assertIn("some_other_type\n", file_content)

    def test_should_indent_messages_with_tool_role_that_contain_fenced_code_blocks(
        self,
    ):
        json = [
            {
                "title": "Test Conversation",
                "create_time": 1630454400,
                "update_time": 1630458000,
                "mapping": {
                    "0": {
                        "message": {
                            "author": {"role": "tool"},
                            "content": {
                                "content_type": "code",
                                "language": "javascript",
                                "text": 'console.log("Hello, world!");',
                            },
                        }
                    }
                },
            }
        ]
        chatgpt_to_markdown(json, self.temp_dir)
        with open(
            os.path.join(self.temp_dir, "Test Conversation.md"), "r", encoding="utf8"
        ) as file:
            file_content = file.read()
        self.assertIn(
            '```javascript\nconsole.log("Hello, world!");\n```\n', file_content
        )


if __name__ == "__main__":
    unittest.main()
