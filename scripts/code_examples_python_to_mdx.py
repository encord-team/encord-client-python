import os
import subprocess
import ast

# Clone the repositories only if they don't exist
if not os.path.exists('encord-client-python'):
    subprocess.run(['git', 'clone', 'https://github.com/encord-team/encord-client-python.git'])
if not os.path.exists('encord-docs-mint'):
    subprocess.run(['git', 'clone', 'https://github.com/encord-team/encord-docs-mint.git'])

# Now set the paths
source_repo_path = 'encord-client-python'  # After cloning, the repo will be in this directory
destination_repo_path = 'encord-docs-mint'  # Same for the destination repo

# Folder paths inside the repos
source_folder = 'tests/docs'
destination_folder = 'snippets/SDKCodeExamples'

# Define the paths to the Python files in the source repo and the corresponding .mdx output in the destination repo
python_files = [
    os.path.join(source_repo_path, source_folder, file)  # All Python files in the source folder
    for file in os.listdir(os.path.join(source_repo_path, source_folder))
    if file.endswith('.py')  # Only select .py files
]

# Ensure the destination folder exists in repo2
destination_folder_path = os.path.join(destination_repo_path, destination_folder)
if not os.path.exists(destination_folder_path):
    os.makedirs(destination_folder_path)

# Function to extract the code block name from a Python file's docstring
def get_code_block_name(python_file_path):
    with open(python_file_path, 'r') as file:
        # Parse the Python file to extract the docstring using AST
        tree = ast.parse(file.read())
        if isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Str):
            return tree.body[0].value.splitlines()[0].replace("Code Block Name:", "").strip()
    return "Untitled Code Block"

# Loop through each Python file and create a corresponding .mdx file
for python_file_path in python_files:
    # Ensure the source file exists before reading it
    if not os.path.exists(python_file_path):
        print(f"Error: Python file not found at {python_file_path}")
        continue

    # Read the content of the Python file
    with open(python_file_path, 'r') as python_file:
        python_content = python_file.read()

    # Extract the code block name from the docstring
    code_block_name = get_code_block_name(python_file_path)

    # Create a corresponding .mdx file in the destination repo
    mdx_file_name = os.path.splitext(os.path.basename(python_file_path))[0] + '.mdx'  # Use the Python file name, but with .mdx extension
    mdx_file_path = os.path.join(destination_folder_path, mdx_file_name)

    # Initialize the .mdx file with the Python code inside a code block, and add the tab name from the docstring
    mdx_content = f"```python {code_block_name}\n{python_content}\n```"

    # Write the content to the corresponding .mdx file
    with open(mdx_file_path, 'w') as mdx_file:
        mdx_file.write(mdx_content)

    print(f"Python code from {python_file_path} has been successfully written to {mdx_file_path} with tab name '{code_block_name}'")
