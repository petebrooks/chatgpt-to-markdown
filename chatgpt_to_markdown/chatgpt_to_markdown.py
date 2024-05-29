import os
import re
import json
from datetime import datetime
from pathlib import Path


def sanitize_file_name(title):
    return re.sub(r'[<>:"/\\|?*\n]', " ", title).strip()


def wrap_html_tags_in_backticks(text):
    return re.sub(r"<[^>]+>", lambda match: f"`{match.group(0)}`", text)


def indent(text):
    return "".join([f"    {line}\n" for line in text.split("\n")])


def format_date(date):
    return date.strftime("%d %b %Y %I:%M %p")


def chatgpt_to_markdown(json_data, source_dir, date_format=format_date):
    if not isinstance(json_data, list):
        raise TypeError("The first argument must be a list.")
    if not isinstance(source_dir, str):
        raise TypeError("The second argument must be a string.")

    for conversation in json_data:
        sanitized_title = sanitize_file_name(conversation["title"])
        file_name = f"{sanitized_title}.md"
        file_path = Path(source_dir) / file_name
        title = f"# {wrap_html_tags_in_backticks(conversation['title'])}\n"
        metadata = (
            f"- Created: {date_format(datetime.fromtimestamp(conversation['create_time']))}\n"
            f"- Updated: {date_format(datetime.fromtimestamp(conversation['update_time']))}\n"
        )
        messages = []
        for node in conversation["mapping"].values():
            content = node["message"].get("content")
            if not content:
                continue

            body = ""
            if content["content_type"] == "text":
                body = "\n".join(content["parts"])
            elif content["content_type"] == "code":
                body = f"```{content['language']}\n{content['text']}\n```"
            elif content["content_type"] == "execution_output":
                body = f"```\n{content['text']}\n```"
            elif content["content_type"] == "multimodal_text":
                for part in content["parts"]:
                    if part["content_type"] == "image_asset_pointer":
                        body += f"Image ({part['width']}x{part['height']}): {part['metadata']['dalle']['prompt']}\n\n"
                    else:
                        body += f"{part['content_type']}\n\n"
            elif content["content_type"] == "tether_browsing_display":
                body = f"```\n{content['result']}\n```"
            elif content["content_type"] == "tether_quote":
                body = f"```\n{content['title']} ({content['url']})\n\n{content['text']}\n```"
            elif content["content_type"] == "system_error":
                body = f"{content['name']}\n\n{content['text']}\n\n"

            if not body.strip():
                continue

            author = node["message"]["author"]
            if author["role"] == "user" or (
                author["role"] == "tool"
                and not (body.startswith("```") and body.endswith("```"))
            ):
                body = indent(body)

            messages.append(
                f"## {author['role']}{' (' + author['name'] + ')' if author.get('name') else ''}\n\n{body}\n\n"
            )

        markdown_content = f"{title}\n{metadata}\n{''.join(messages)}"
        file_path.write_text(markdown_content, encoding="utf8")
        os.utime(file_path, (conversation["create_time"], conversation["update_time"]))


# Export the chatgpt_to_markdown function
if __name__ == "__main__":
    with open("input.json", "r") as f:
        data = json.load(f)
    chatgpt_to_markdown(data, "./output")
