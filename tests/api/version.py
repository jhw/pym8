import unittest
import tempfile
import os
from m8.api.version import M8Version
from m8.api.project import M8Project
from m8.api.instruments import M8Instrument

class TestM8Version(unittest.TestCase):
    def test_version_state(self):
        """Test that version is stored as state in both project and instruments."""
        # Create project with a specific version
        project = M8Project()
        project.version = M8Version(4, 1, 2)
        
        # Initialize instruments list
        from m8.api.instruments import M8Instruments
        project.instruments = M8Instruments()
        
        # Create instrument
        instrument = M8Instrument("wavsynth", name="TestSynth")
        
        # When adding to project, instrument should inherit project version
        slot = project.add_instrument(instrument)
        self.assertEqual(str(project.instruments[slot].version), "4.1.2")
        
        # Changing project version should not affect instrument already added
        project.version = M8Version(4, 1, 3)
        self.assertEqual(str(project.instruments[slot].version), "4.1.2")
        
        # Adding a new instrument should give it the updated version
        instrument2 = M8Instrument("macrosynth", name="Test2")
        slot2 = project.add_instrument(instrument2)
        self.assertEqual(str(project.instruments[slot2].version), "4.1.3")
        
    def test_version_validation(self):
        """Test version validation between projects and instruments."""
        # Create project with version 4.1.0
        project = M8Project()
        project.version = M8Version(4, 1, 0)
        
        # Initialize instruments list
        from m8.api.instruments import M8Instruments
        project.instruments = M8Instruments()
        
        # Add an instrument, it should inherit project version
        instrument = M8Instrument("wavsynth", name="TestSynth")
        slot = project.add_instrument(instrument)
        
        # Version validation should pass
        self.assertTrue(project.validate_versions())
        
        # Manually change instrument version
        project.instruments[slot].version = M8Version(4, 0, 1)
        
        # Now validation should fail
        self.assertFalse(project.validate_versions())
        
    def test_file_operations_with_version(self):
        """Test that version is preserved when reading/writing files."""
        # Skip this test if we don't have the template file
        try:
            # First create a proper project from template
            project = M8Project.initialise()
        except FileNotFoundError:
            self.skipTest("Template file not found - skipping file I/O test")
            
        # Set custom version
        project.version = M8Version(4, 2, 0)
        
        # Add instrument that inherits the version
        instrument = M8Instrument("wavsynth", name="TestSynth")
        slot = project.add_instrument(instrument)
        self.assertEqual(str(project.instruments[slot].version), "4.2.0")
        
        # Write project to temporary file and read it back
        with tempfile.NamedTemporaryFile(suffix='.m8s', delete=False) as tmp:
            try:
                tmp_path = tmp.name
                project.write_to_file(tmp_path)
                
                # Read it back
                read_project = M8Project.read_from_file(tmp_path)
                
                # Check version was preserved
                self.assertEqual(str(read_project.version), "4.2.0")
            finally:
                # Clean up
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                    
        # Write instrument to temporary file and read it back
        instrument = project.instruments[slot]
        with tempfile.NamedTemporaryFile(suffix='.m8i', delete=False) as tmp:
            try:
                tmp_path = tmp.name
                instrument.write_to_file(tmp_path)
                
                # Read it back
                read_instrument = M8Instrument.read_from_file(tmp_path)
                
                # Check version was preserved
                self.assertEqual(str(read_instrument.version), "4.2.0")
                
                # Try with version mismatch check
                # Should pass with matching version
                M8Instrument.read_from_file(tmp_path, expected_version=M8Version(4, 2, 0))
                
                # Should fail with non-matching version
                with self.assertRaises(ValueError):
                    M8Instrument.read_from_file(tmp_path, expected_version=M8Version(4, 0, 1))
            finally:
                # Clean up
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                    
    def test_not_serialized_to_json(self):
        """Test that version is not serialized to JSON."""
        # Create project with a specific version
        project = M8Project()
        project.version = M8Version(4, 1, 2)
        
        # Initialize all required components
        from m8.api.instruments import M8Instruments
        from m8.api.metadata import M8Metadata
        from m8.api.song import M8SongMatrix
        from m8.api.chains import M8Chains
        from m8.api.phrases import M8Phrases
        
        project.metadata = M8Metadata(name="Test Project")
        project.song = M8SongMatrix()
        project.chains = M8Chains()
        project.phrases = M8Phrases()
        project.instruments = M8Instruments()
        
        # Add an instrument
        instrument = M8Instrument("wavsynth", name="TestSynth")
        project.add_instrument(instrument)
        
        # Serialize to dict
        project_dict = project.as_dict()
        
        # Version should not be in the dict
        self.assertNotIn("version", project_dict)
        
        # Create a new project from dict
        new_project = M8Project.from_dict(project_dict)
        
        # New project should have default version, not the one from original project
        self.assertEqual(str(new_project.version), "4.0.1")  # Default version
        
        # Check instrument serialization
        instr_dict = instrument.as_dict()
        self.assertNotIn("version", instr_dict)


if __name__ == '__main__':
    unittest.main()