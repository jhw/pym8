import unittest
from m8.api.project import M8Project


class TestFXMapping(unittest.TestCase):
    """
    Test that FX values from M8S files get correctly mapped when read
    into Python objects. This test focuses on validating FX processing
    with different effect types and values.
    """
    
    def setUp(self):
        # Load the M8S file with the FX structure we want to test
        self.project = M8Project.read_from_file("tests/examples/fixtures/GENBASS.m8s")
        # Get the first chain and its referenced phrases
        self.chain = self.project.chains[0]
        self.chain_dict = self.chain.as_dict()
        self.phrase = self.project.phrases[0] 
        self.phrase_dict = self.phrase.as_dict()
    
    def test_chain_structure(self):
        """Verify the chain has the expected structure"""
        # Chain should have one step referencing phrase 0
        self.assertEqual(len(self.chain_dict['steps']), 1, 
                         "Chain should have exactly one step")
        
        # The step should reference phrase 0 with no transpose
        step = self.chain_dict['steps'][0]
        self.assertEqual(step['phrase'], 0, 
                         "The step in chain should reference phrase 0")
        self.assertEqual(step['transpose'], 0, 
                         "The step in chain should have no transpose")
    
    def test_phrase_structure(self):
        """Verify the phrase has the expected structure with 5 steps"""
        # Phrase should have 5 specific steps
        steps = self.phrase_dict['steps']
        self.assertEqual(len(steps), 5, 
                         "Phrase should have exactly 5 steps")
        
        # First step should be C_3 note with instrument 0
        self.assertEqual(steps[0]['note'], 'C_3', 
                         "First step should have C_3 note")
        self.assertEqual(steps[0]['velocity'], 100, 
                         "First step should have velocity 100")
        self.assertEqual(steps[0]['instrument'], 0, 
                         "First step should reference instrument 0")
        
        # Other steps should have empty notes but with FX
        # With our sparse representation, empty fields shouldn't be in the dict
        for i in range(1, 5):
            self.assertNotIn('note', steps[i], 
                             f"Step {i} should not have 'note' field when empty")
            self.assertNotIn('velocity', steps[i], 
                             f"Step {i} should not have 'velocity' field when empty")
            self.assertNotIn('instrument', steps[i], 
                             f"Step {i} should not have 'instrument' field when empty")
            # But should have FX
            self.assertIn('fx', steps[i], 
                          f"Step {i} should have 'fx' field")
    
    def test_fx_in_first_step(self):
        """Verify the first step has the expected FX"""
        step_fx = self.phrase_dict['steps'][0]['fx']
        self.assertEqual(len(step_fx), 3, 
                         "First step should have 3 FX")
        
        # Check the first effect - RNL with value 96 (0x60)
        if isinstance(step_fx[0]['key'], str):
            self.assertEqual(step_fx[0]['key'], 'RNL', 
                             "First effect should be RNL")
        else:
            self.assertEqual(step_fx[0]['key'], 7, 
                             "First effect should be RNL (numeric value 7)")
        self.assertEqual(step_fx[0]['value'], 96, 
                         "RNL effect should have value 96 (0x60)")
        self.assertEqual(step_fx[0]['index'], 0, 
                         "RNL effect should be at index 0")
        
        # Check the second effect - CHA with value 143 (0x8F)
        if isinstance(step_fx[1]['key'], str):
            self.assertEqual(step_fx[1]['key'], 'CHA', 
                             "Second effect should be CHA")
        else:
            self.assertEqual(step_fx[1]['key'], 1, 
                             "Second effect should be CHA (numeric value 1)")
        self.assertEqual(step_fx[1]['value'], 143, 
                         "CHA effect should have value 143 (0x8F)")
        self.assertEqual(step_fx[1]['index'], 1, 
                         "CHA effect should be at index 1")
        
        # Check the third effect - PSL with value 5 (0x05)
        if isinstance(step_fx[2]['key'], str):
            self.assertEqual(step_fx[2]['key'], 'PSL', 
                             "Third effect should be PSL")
        else:
            self.assertEqual(step_fx[2]['key'], 12, 
                             "Third effect should be PSL (numeric value 12)")
        self.assertEqual(step_fx[2]['value'], 5, 
                         "PSL effect should have value 5 (0x05)")
        self.assertEqual(step_fx[2]['index'], 2, 
                         "PSL effect should be at index 2")
    
    def test_fx_in_subsequent_steps(self):
        """Verify the subsequent steps have the expected FX"""
        steps = self.phrase_dict['steps']
        
        # Check step 1 FX (using numeric values for comparison since serialization is not consistent)
        step1_fx = steps[1]['fx']
        self.assertEqual(len(step1_fx), 2, "Step 1 should have 2 FX")
        # Here we need to handle the possibility that key might be numeric or string
        if isinstance(step1_fx[0]['key'], str):
            self.assertEqual(step1_fx[0]['key'], 'HOP', "First effect should be HOP")
        else:
            self.assertEqual(step1_fx[0]['key'], 4, "First effect should be HOP (numeric value 4)")
        self.assertEqual(step1_fx[0]['value'], 0, "HOP value should be 0")
        
        if isinstance(step1_fx[1]['key'], str):
            self.assertEqual(step1_fx[1]['key'], 'CHA', "Second effect should be CHA")
        else:
            self.assertEqual(step1_fx[1]['key'], 1, "Second effect should be CHA (numeric value 1)")
        self.assertEqual(step1_fx[1]['value'], 128, "CHA value should be 128 (0x80)")
        
        # Check step 2 FX
        step2_fx = steps[2]['fx']
        self.assertEqual(len(step2_fx), 2, "Step 2 should have 2 FX")
        if isinstance(step2_fx[0]['key'], str):
            self.assertEqual(step2_fx[0]['key'], 'HOP', "First effect should be HOP")
        else:
            self.assertEqual(step2_fx[0]['key'], 4, "First effect should be HOP (numeric value 4)")
        self.assertEqual(step2_fx[0]['value'], 0, "HOP value should be 0")
        
        if isinstance(step2_fx[1]['key'], str):
            self.assertEqual(step2_fx[1]['key'], 'CHA', "Second effect should be CHA")
        else:
            self.assertEqual(step2_fx[1]['key'], 1, "Second effect should be CHA (numeric value 1)")
        self.assertEqual(step2_fx[1]['value'], 64, "CHA value should be 64 (0x40)")
        
        # Check step 3 FX
        step3_fx = steps[3]['fx']
        self.assertEqual(len(step3_fx), 2, "Step 3 should have 2 FX")
        if isinstance(step3_fx[0]['key'], str):
            self.assertEqual(step3_fx[0]['key'], 'HOP', "First effect should be HOP")
        else:
            self.assertEqual(step3_fx[0]['key'], 4, "First effect should be HOP (numeric value 4)")
        self.assertEqual(step3_fx[0]['value'], 0, "HOP value should be 0")
        
        if isinstance(step3_fx[1]['key'], str):
            self.assertEqual(step3_fx[1]['key'], 'CHA', "Second effect should be CHA")
        else:
            self.assertEqual(step3_fx[1]['key'], 1, "Second effect should be CHA (numeric value 1)")
        self.assertEqual(step3_fx[1]['value'], 64, "CHA value should be 64 (0x40)")
        
        # Check step 4 FX - only HOP
        step4_fx = steps[4]['fx']
        self.assertEqual(len(step4_fx), 1, "Step 4 should have 1 FX")
        if isinstance(step4_fx[0]['key'], str):
            self.assertEqual(step4_fx[0]['key'], 'HOP', "Effect should be HOP")
        else:
            self.assertEqual(step4_fx[0]['key'], 4, "Effect should be HOP (numeric value 4)")
        self.assertEqual(step4_fx[0]['value'], 0, "HOP value should be 0")
    
    def test_fx_throughout_phrase(self):
        """Test the FX distribution throughout the phrase"""
        steps = self.phrase_dict['steps']
        
        # Helper function to check for FX by name or numeric id
        def has_fx(fx_list, fx_name, fx_id):
            return any((isinstance(fx['key'], str) and fx['key'] == fx_name) or 
                      (isinstance(fx['key'], int) and fx['key'] == fx_id) 
                      for fx in fx_list)
        
        # Verify all empty steps have HOP effect (string 'HOP' or numeric 4)
        for i in range(1, 5):
            step_fx = steps[i]['fx']
            self.assertTrue(has_fx(step_fx, 'HOP', 4),
                            f"Step {i} should have a HOP effect")
        
        # Verify CHA effect is present in first 4 steps but not in step 4
        cha_steps = [i for i, step in enumerate(steps) 
                     if has_fx(step['fx'], 'CHA', 1)]
        self.assertEqual(cha_steps, [0, 1, 2, 3], 
                         "CHA effect should be in steps 0, 1, 2, 3 but not 4")
        
        # Verify PSL effect is only in the first step
        psl_steps = [i for i, step in enumerate(steps) 
                     if has_fx(step['fx'], 'PSL', 12)]
        self.assertEqual(psl_steps, [0], 
                         "PSL effect should only be in step 0")
        
        # Verify RNL effect is only in the first step
        rnl_steps = [i for i, step in enumerate(steps) 
                     if has_fx(step['fx'], 'RNL', 7)]
        self.assertEqual(rnl_steps, [0], 
                         "RNL effect should only be in step 0")


if __name__ == '__main__':
    unittest.main()