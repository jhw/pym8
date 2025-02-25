from m8.api.project import M8Project

import yaml

def print_project_info(project):
    print(f"--- phrases ---")
    for i, phrase in enumerate(project.phrases):
        if not phrase.is_empty():
            print(f"Phrase {i}:")
            keys = []
            for j, step in enumerate(phrase):
                if not step.is_empty():
                    keys += [hex(fx.key) for fx in step.fx]
            print(yaml.safe_dump(keys, default_flow_style = False))
def main():    
    file_path = "dev/PYFX2.m8s"        
    project = M8Project.read_from_file(file_path)
    print_project_info(project)

if __name__ == "__main__":
    main()
