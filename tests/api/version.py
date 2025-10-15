import unittest
import tempfile
import os
from m8.api.version import M8Version
from m8.api.project import M8Project
from m8.api.sampler import M8Sampler

class TestM8Version(unittest.TestCase):
    def test_version_state(self):
        """Test that version is stored as state in both project and instruments."""
        # Create project with a specific version
        project = M8Project()
        project.version = M8Version(4, 1, 2)
        
        # Initialize instruments list
        from m8.api.instrument import M8Instruments
        project.instruments = M8Instruments()

        # Create sampler and directly assign to slot
        sampler = M8Sampler(name="TestSynth")
        sampler.version = project.version
        slot = 0
        project.instruments[slot] = sampler
        self.assertEqual(str(project.instruments[slot].version), "4.1.2")

        # Changing project version should not affect sampler already added
        project.version = M8Version(4, 1, 3)
        self.assertEqual(str(project.instruments[slot].version), "4.1.2")

        # Adding a new sampler with updated version
        sampler2 = M8Sampler(name="Test2")
        sampler2.version = project.version
        slot2 = 1
        project.instruments[slot2] = sampler2
        self.assertEqual(str(project.instruments[slot2].version), "4.1.3")
        
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

        # Add sampler with the version
        sampler = M8Sampler(name="TestSynth")
        sampler.version = project.version
        slot = 0
        project.instruments[slot] = sampler
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


if __name__ == '__main__':
    unittest.main()