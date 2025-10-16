import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(BASE_DIR, "templates")

print("Templates folder:", templates_dir)
print("Contents:", os.listdir(templates_dir))
