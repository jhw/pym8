#!/usr/bin/env python

import re
import datetime

def parse_date(date_str):
    # Match patterns like 25/03/25, 25/03/2025, 03/25/25, 03/25/2025
    patterns = [
        r"(\d{1,2})/(\d{1,2})/(\d{2,4})",  # dd/mm/yy or dd/mm/yyyy
        r"(\d{1,2})/(\d{1,2})/(\d{2,4})"   # mm/dd/yy or mm/dd/yyyy
    ]
    
    for pattern in patterns:
        match = re.search(pattern, date_str)
        if match:
            day_or_month1, day_or_month2, year = match.groups()
            
            # Convert 2-digit year to 4-digit year
            if len(year) == 2:
                year = int("20" + year)
            else:
                year = int(year)
            
            # Try both dd/mm and mm/dd formats
            try:
                # Try as dd/mm/yyyy
                return datetime.datetime(year, int(day_or_month2), int(day_or_month1))
            except ValueError:
                try:
                    # Try as mm/dd/yyyy
                    return datetime.datetime(year, int(day_or_month1), int(day_or_month2))
                except ValueError:
                    continue
    
    return None

def main():
    # Read the content of NOTES.md
    with open("/Users/jhw/work/pym8/NOTES.md", "r") as f:
        content = f.read()
    
    # Split the content into sections based on markdown headers
    sections = []
    current_section = []
    current_header = None
    current_date = None
    
    for line in content.splitlines():
        # Check if line is a header with hash
        if line.startswith("#"):
            # If we have a current section, save it
            if current_header is not None:
                sections.append({
                    "header": current_header,
                    "date": current_date,
                    "content": "\n".join(current_section)
                })
            
            # Start a new section
            current_header = line
            current_section = [line]
            
            # Try to find a date in the header line
            date_match = re.search(r"\((\d{1,2}/\d{1,2}/(?:\d{2}|\d{4}))\)", line)
            if date_match:
                date_str = date_match.group(1)
                current_date = parse_date(date_str)
            else:
                current_date = None
        else:
            # Check if the line might contain a date in parentheses
            if current_date is None:
                date_match = re.search(r"\((\d{1,2}/\d{1,2}/(?:\d{2}|\d{4}))\)", line)
                if date_match:
                    date_str = date_match.group(1)
                    current_date = parse_date(date_str)
            
            # Add the line to the current section
            current_section.append(line)
    
    # Add the last section
    if current_header is not None:
        sections.append({
            "header": current_header,
            "date": current_date,
            "content": "\n".join(current_section)
        })
    
    # Sort sections by date
    dated_sections = [s for s in sections if s["date"] is not None]
    undated_sections = [s for s in sections if s["date"] is None]
    
    dated_sections.sort(key=lambda x: x["date"], reverse=True)
    
    # Combine the sections back together
    sorted_content = "\n\n".join([s["content"] for s in dated_sections + undated_sections])
    
    # Write the content back to NOTES.md
    with open("../NOTES.md", "w") as f:
        f.write(sorted_content)
    
    print(f"Reordered {len(dated_sections)} dated sections from newest to oldest")
    print(f"Kept {len(undated_sections)} undated sections at the end")

if __name__ == "__main__":
    main()