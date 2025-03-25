#!/usr/bin/env python3
import os
import re
import sys
import argparse

def create_pattern(strings, pattern_template):
    joined_strings = '|'.join(strings)
    return re.compile(pattern_template.replace('STRING_PLACEHOLDER', joined_strings))

def process_file(file_path, pattern, processor, dry_run=False):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        modified_content, count = re.subn(pattern, processor, content)
        
        if count > 0 and not dry_run:
            print(f"Updating {file_path}")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            
        return count > 0, count
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False, 0

def process_directory(dir_path, pattern, processor, extensions=['.py'], dry_run=False):
    changes = []
    
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                file_path = os.path.join(root, file)
                changed, count = process_file(file_path, pattern, processor, dry_run)
                if changed:
                    changes.append((file_path, count))
    
    return changes

def transform_match(match, transformer, group_index=1):
    groups = list(match.groups())
    
    if 0 <= group_index < len(groups) and groups[group_index] is not None:
        groups[group_index] = transformer(groups[group_index])
    
    return ''.join(g for g in groups if g is not None)

def create_quoted_string_pattern(strings):
    escaped_strings = [re.escape(s) for s in strings]
    joined_strings = '|'.join(escaped_strings)
    return re.compile(fr'(["\'])({joined_strings})(["\'])')

def main():
    parser = argparse.ArgumentParser(description='Recursively transform strings in files')
    parser.add_argument('strings', nargs='+', help='Strings to search for and transform')
    parser.add_argument('--transform', choices=['upper', 'lower', 'snake', 'camel', 'kebab'], 
                        default='upper', help='Transformation to apply')
    parser.add_argument('--pattern', help='Custom regex pattern (use STRING_PLACEHOLDER for the search strings)')
    parser.add_argument('--directories', nargs='+', default=['.'], help='Directories to process')
    parser.add_argument('--extensions', nargs='+', default=['.py'], help='File extensions to process')
    parser.add_argument('--group', type=int, default=1, help='Group index to transform in regex matches')
    parser.add_argument('--dry-run', action='store_true', help='Show changes without applying them')
    
    args = parser.parse_args()
    
    transformers = {
        'upper': str.upper,
        'lower': str.lower,
        'snake': lambda s: '_'.join(s.lower().split()),
        'camel': lambda s: ''.join(w.capitalize() if i > 0 else w.lower() 
                                  for i, w in enumerate(s.split())),
        'kebab': lambda s: '-'.join(s.lower().split())
    }
    transformer = transformers[args.transform]
    
    if args.pattern:
        pattern = create_pattern(args.strings, args.pattern)
    else:
        pattern = create_quoted_string_pattern(args.strings)
    
    processor = lambda match: transform_match(match, transformer, args.group)
    
    total_changes = []
    for directory in args.directories:
        if not os.path.isdir(directory):
            print(f"Warning: {directory} is not a valid directory. Skipping.")
            continue
        
        changes = process_directory(directory, pattern, processor, args.extensions, args.dry_run)
        total_changes.extend(changes)
    
    total_files = len(total_changes)
    total_replacements = sum(count for _, count in total_changes)
    
    print("\nSummary of changes:")
    print("==================\n")
    
    if total_files > 0:
        for directory in args.directories:
            dir_changes = [(f, c) for f, c in total_changes if f.startswith(os.path.abspath(directory))]
            if dir_changes:
                print(f"Directory: {directory}")
                for file_path, count in dir_changes:
                    rel_path = os.path.relpath(file_path, directory)
                    print(f"  {rel_path}: {count} replacements")
    
        print(f"\nTotal: {total_files} files modified, {total_replacements} replacements")
    else:
        print("No changes made.")
    
    if args.dry_run:
        print("\nThis was a dry run. No changes were made.")
        print("Run without --dry-run to apply changes.")

if __name__ == "__main__":
    main()