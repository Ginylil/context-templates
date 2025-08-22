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
        if "---" in content:
            parts = content.split("---", 1)
            metadata = yaml.safe_load(parts[0])
            template_content = parts[1].strip()
        else:
            metadata = yaml.safe_load(content)
            template_content = content

        filename = metadata.get("filename") or os.path.basename(template_path)

        files = {
            "file": (filename, template_content, "text/plain"),
        }

        long_desc = metadata.get("long_description", "")
        if not long_desc:
            long_desc = metadata.get("description", "")

        short_desc = metadata.get("short_description", "")
        if not short_desc and long_desc:
            short_desc = long_desc.splitlines()[0]

        data = {
            "name": metadata["name"],
            "filename": filename,
            "short_description": short_desc,
            "long_description": long_desc,
            "template_type": metadata.get("template_type", ""),
        }

        headers = {"Authorization": f"Bearer {token}"}

        response = requests.post(
            api_url, headers=headers, data=data, files=files)
        response.raise_for_status()
        print(f"Successfully pushed template: {metadata['name']}")

    except Exception as e:
        print(f"Failed to push template {template_path}: {e}", file=sys.stderr)
        is_ci = os.environ.get("CI", "false").lower() == "true"
        if "response" in locals() and not is_ci:
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
    for subdir, _, files in os.walk(templates_dir):
        for filename in files:
            if (
                filename.endswith(".yml")
                and filename != "schema.yml"
                and not filename.startswith("example-")
            ):
                template_path = os.path.join(subdir, filename)
                push_template(template_path, api_url, token)


if __name__ == "__main__":
    main()
