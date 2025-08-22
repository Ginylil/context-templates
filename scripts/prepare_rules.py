import os
import yaml
import re


def get_language_from_filename(filename):
    """Infers the programming language from the filename."""
    name_map = {
        "beefreesdk": "javascript",
        "clean-code": "plaintext",
        "codequality": "plaintext",
        "cpp": "cpp",
        "database": "sql",
        "fastapi": "python",
        "gitflow": "plaintext",
        "medusa": "javascript",
        "nativescript": "javascript",
        "nextjs": "javascript",
        "node-express": "javascript",
        "python": "python",
        "react": "javascript",
        "rust": "rust",
        "svelte": "javascript",
        "tailwind": "css",
        "typescript": "typescript",
        "vue": "javascript",
    }
    base_name = os.path.splitext(filename)[0].lower()
    return name_map.get(base_name, "plaintext")


def format_name(filename):
    """Formats the filename into a human-readable name."""
    name = os.path.splitext(filename)[0]
    name = re.sub(r'[-_]', ' ', name)
    return name.title()


def process_rule_file(filepath):
    """
    Processes a single .mdc rule file, adds YAML frontmatter,
    and saves it as a .yml file.
    """
    with open(filepath, 'r') as f:
        content = f.read()

    parts = content.split('---', 2)
    existing_metadata = {}
    main_content = ''

    if len(parts) >= 3:
        try:
            yaml_text = parts[1]
            # Use regex to find and quote unquoted globs values
            yaml_text = re.sub(
                r"^(globs:\s*)([!\"'].*)$", r"'\\1\\2'", yaml_text, flags=re.MULTILINE)
            existing_metadata = yaml.safe_load(yaml_text) or {}
            main_content = parts[2].strip()
        except yaml.YAMLError:
            # If frontmatter is still malformed, treat entire file as content
            main_content = content.strip()
    else:
        main_content = content.strip()

    filename = os.path.basename(filepath)

    metadata = {
        'template_type': 'rule',
        'template_subtype': 'cursor',
        'name': format_name(filename),
        'description': f'A set of rules for {format_name(filename)}.',
        'language': get_language_from_filename(filename),
        'scope': 'file',
    }

    # Merge existing metadata, giving it precedence
    metadata.update(existing_metadata)

    if 'globs' in metadata and isinstance(metadata['globs'], str):
        metadata['globs'] = [g.strip()
                             for g in metadata['globs'].split(',') if g.strip()]

    new_content_parts = [
        '---',
        yaml.dump(metadata, default_flow_style=False, sort_keys=False).strip(),
        '---',
        main_content,
        '',
        'Powered by Detailer',
    ]

    new_content = '\n'.join(new_content_parts)

    new_filepath = os.path.splitext(filepath)[0] + '.yml'
    with open(new_filepath, 'w') as f:
        f.write(new_content)

    os.remove(filepath)
    print(
        f"Processed and converted {filename} to {os.path.basename(new_filepath)}")


def main():
    """
    Main function to process all .mdc files in the cursor rules directory.
    """
    rules_dir = 'templates/rules/cursor'
    if not os.path.isdir(rules_dir):
        print(f"Directory not found: {rules_dir}")
        return

    for filename in os.listdir(rules_dir):
        if filename.endswith('.mdc'):
            filepath = os.path.join(rules_dir, filename)
            process_rule_file(filepath)


if __name__ == '__main__':
    main()
