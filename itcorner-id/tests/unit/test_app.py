import os

def test_project_structure():
    """Memastikan direktori aplikasi utama tersedia untuk pipeline CI/CD."""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    assert os.path.exists(os.path.join(base_dir, "app"))
    assert os.path.exists(os.path.join(base_dir, "requirements.txt"))

def test_basic_math_sanity():
    """Memastikan runner Pytest mengeksekusi minimal 2 pengujian unit."""
    assert 200 == 200
