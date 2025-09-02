import pytest
import tempfile
import os
import json
from typer.testing import CliRunner
from app.cli import app

runner = CliRunner()

def test_subjects_load():
    """Test loading subjects from CSV"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test CSV
        csv_content = """type,value
email,test@example.com
username,testuser
phone,+1234567890
"""
        csv_file = os.path.join(temp_dir, "subjects.csv")
        with open(csv_file, 'w') as f:
            f.write(csv_content)
        
        # Create data directory
        data_dir = os.path.join(temp_dir, "data")
        os.makedirs(data_dir, exist_ok=True)
        
        # Change to temp directory and run command
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            result = runner.invoke(app, ["subjects-load", "--path", csv_file])
            assert result.exit_code == 0
            
            # Check that subjects.json was created
            subjects_file = os.path.join(data_dir, "subjects.json")
            assert os.path.exists(subjects_file)
            
            # Check that enrichment files were created
            enrichment_dir = os.path.join(data_dir, "enrichment")
            assert os.path.exists(os.path.join(enrichment_dir, "email_test@example.com.json"))
            assert os.path.exists(os.path.join(enrichment_dir, "username_testuser.json"))
            
        finally:
            os.chdir(original_cwd)

def test_search_messages_no_data():
    """Test search command with no data"""
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            result = runner.invoke(app, ["search-messages", "--by", "user", "--value", "testuser"])
            # Should not crash even with no data
            assert result.exit_code == 0
        finally:
            os.chdir(original_cwd)