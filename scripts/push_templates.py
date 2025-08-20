import os
import requests
import yaml
import sys


def push_template(template_path, api_url, token):
    """
    Pushes a single template to the API.
    """
    with open(template_path, "r") as f:
        content = f.read()

    try:
        parts = content.split("---", 1)
        metadata = yaml.safe_load(parts[0])
        template_content = parts[1].strip()

        files = {
            "file": (metadata["filename"], template_content, "text/plain"),
        }
        data = {
            "name": metadata["name"],
            "filename": metadata["filename"],
            "short_description": metadata.get("short_description", ""),
            "long_description": metadata.get("long_description", ""),
        }

        headers = {"Authorization": f"Bearer {token}"}

        response = requests.post(
            api_url, headers=headers, data=data, files=files)
        response.raise_for_status()
        print(f"Successfully pushed template: {metadata['name']}")

    except Exception as e:
        print(f"Failed to push template {template_path}: {e}", file=sys.stderr)
        if "response" in locals() and os.environ.get("CI", "false").lower() != "true":
            print(f"Response: {response.text}", file=sys.stderr)
        sys.exit(1)


def main():
    """
    Main function to push all templates.
    """
    api_url = os.environ.get("TEMPLATE_API_URL")
    token = os.environ.get("TEMPLATE_API_TOKEN")

    if not api_url or not token:
        print(
            "Error: TEMPLATE_API_URL and TEMPLATE_API_TOKEN "
            "environment variables must be set.",
            file=sys.stderr,
        )
        sys.exit(1)

    templates_dir = "templates"
    for filename in os.listdir(templates_dir):
        if filename.endswith(".yml"):
            template_path = os.path.join(templates_dir, filename)
            push_template(template_path, api_url, token)


if __name__ == "__main__":
    main()
