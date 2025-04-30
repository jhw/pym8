#!/usr/bin/env python3

import os
import struct
from pathlib import Path
from pydub import AudioSegment
from m8.tools.wav_slicer import WAVSlicer

class ChainBuilder:
    def __init__(self, duration_ms, fade_ms, packs_dir=None):
        self.duration_ms = duration_ms
        self.fade_ms = fade_ms
        self.packs_dir = Path(packs_dir) if packs_dir else Path("tmp/packs")
        
    def build_chain_from_files(self, file_paths):
        samples = []
        for file_path in file_paths:
            path = Path(file_path)
            pack_name = path.parent.name
            file_name = path.name
            sample = {
                'pack_name': pack_name,
                'file_name': file_name,
                'name': f"{pack_name}/{file_name}",
                'full_path': file_path
            }
            samples.append(sample)
            
        return self.build_chain(samples)
    
    def build_chain(self, samples):
        # Sort samples alphabetically for deterministic order
        samples = sorted(samples, key=lambda x: x['name'])
        
        sample_segments = []
        name_to_index = {}
        index_to_name = {}
        
        # Always use 44.1kHz for consistent sample chains
        frame_rate = 44100
        print(f"Using consistent frame rate of {frame_rate}Hz for all samples")
        
        # Pass 1: Load all audio segments and create index mapping
        for current_index, sample in enumerate(samples):
            # Use full_path if provided, otherwise construct from packs_dir
            if 'full_path' in sample:
                file_path = Path(sample['full_path'])
            else:
                file_path = self.packs_dir / sample['pack_name'] / sample['file_name']
                
            segment = AudioSegment.from_wav(file_path)
            
            # Resample to target frame rate if needed
            if segment.frame_rate != frame_rate:
                segment = segment.set_frame_rate(frame_rate)
            
            # Truncate to duration
            segment = segment[:self.duration_ms]
            
            # Pad with silence if needed to ensure consistent duration
            if len(segment) < self.duration_ms:
                silence = AudioSegment.silent(duration=self.duration_ms - len(segment), frame_rate=frame_rate)
                segment = segment + silence
            
            # Apply fade in and fade out to avoid clicks at slice boundaries
            segment = segment.fade_in(self.fade_ms).fade_out(self.fade_ms)
            
            # Store the segment and update index mappings
            sample_segments.append(segment)
            name_to_index[sample['name']] = current_index
            index_to_name[current_index] = sample['name']
        
        if not sample_segments:
            raise ValueError("No valid samples found for chain")
        
        # Check if we have too many samples (M8 limitation)
        if len(sample_segments) > 255:
            raise ValueError(f"Chain has {len(sample_segments)} samples, which exceeds the M8 limit of 255")
        
        # Calculate exact slice positions and buffer size
        sample_count = len(sample_segments)
        samples_per_segment = int(self.duration_ms * frame_rate / 1000)
        
        # Create slice points at the start of each segment
        # We'll also log the fade durations in samples for context
        fade_samples = int(self.fade_ms * frame_rate / 1000)
        print(f"Sample parameters: {sample_count} segments, {samples_per_segment} samples per segment, {fade_samples} fade samples")
        
        # Using sample_count + 1 gives us one extra slice point at the end of the chain
        # This helps with calculating the proper duration of the last sample
        slice_positions = [i * samples_per_segment for i in range(sample_count + 1)]
        
        # Create a silent buffer for the entire chain
        total_duration_ms = self.duration_ms * sample_count
        chain = AudioSegment.silent(duration=total_duration_ms, frame_rate=frame_rate)
        print(f"Created silent chain buffer: {total_duration_ms}ms duration at {frame_rate}Hz frame rate")
        
        # Insert each segment at its precise position
        for i, segment in enumerate(sample_segments):
            position_ms = i * self.duration_ms
            chain = chain.overlay(segment, position=position_ms)
        
        return chain, name_to_index, slice_positions
    
    def add_slice_points(self, file_path, slice_positions):
        print(f"\nAdding slice points to {file_path}")
        num_samples = len(slice_positions) - 1 if len(slice_positions) > 1 else len(slice_positions)
        print(f"Total samples in chain: {num_samples}")
        
        # The last slice position is the end boundary, not a slice itself
        # M8 expects slice points at the start of each sample, not at the end
        filtered_slice_positions = slice_positions[:-1] if len(slice_positions) > 1 else slice_positions
        print(f"Using {len(filtered_slice_positions)} slice markers (removed end boundary)")
        
        # Use a temporary file for adding slice points
        temp_file = str(file_path) + ".tmp"
        
        # Copy original file to temporary location
        with open(file_path, 'rb') as src, open(temp_file, 'wb') as dst:
            dst.write(src.read())
        
        # Create a WAVSlicer and add custom slice points
        slicer = WAVSlicer()
        
        # Read the file
        with open(temp_file, 'rb') as file:
            data = file.read()
        
        # Create standard cue chunk with the filtered slice positions
        standard_cue_chunk = slicer.create_standard_cue_chunk(filtered_slice_positions)
        
        # Find proper position to insert standard cue chunk
        fmt_pos = data.find(b'fmt ')
        if fmt_pos < 0:
            raise ValueError(f"Could not find 'fmt ' chunk in {temp_file}")
        
        # Get the size of the fmt chunk and calculate end position
        fmt_chunk_size = struct.unpack('<I', data[fmt_pos+4:fmt_pos+8])[0]
        fmt_end = fmt_pos + 8 + fmt_chunk_size
        if fmt_chunk_size % 2:
            fmt_end += 1
        
        # Insert standard cue chunk after fmt chunk
        print("Adding standard cue chunk after fmt chunk")
        new_data = data[:fmt_end] + standard_cue_chunk + data[fmt_end:]
        
        # Create M8-specific atad cue chunk
        m8_cue_chunk = slicer.create_m8_atad_cue_chunk(filtered_slice_positions)
        
        # Add M8-specific cue chunk at the end
        print("Adding M8-specific 'atad' cue chunk at the end")
        new_data = new_data + m8_cue_chunk
        
        # Update the RIFF size
        riff_size = len(new_data) - 8  # Total size minus RIFF header
        new_data = new_data[:4] + struct.pack('<I', riff_size) + new_data[8:]
        
        # Write the new file
        with open(file_path, 'wb') as file:
            file.write(new_data)
        
        # Remove temporary file
        os.remove(temp_file)
        
    def create_chain(self, file_paths, output_path):
        if not file_paths:
            raise ValueError("No file paths provided")
            
        # Build the chain from provided file paths
        chain, name_to_index, slice_positions = self.build_chain_from_files(file_paths)
        
        # Create output directory if needed
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # Export the chain
        chain.export(output_path, format="wav")
        
        # Add slice points
        self.add_slice_points(output_path, slice_positions)
        
        return output_path, name_to_index, slice_positions