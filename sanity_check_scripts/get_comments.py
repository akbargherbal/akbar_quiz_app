import tokenize
import os
def extract_comments(filepath):
    comments = []
    with open(filepath, 'rb') as f:
        tokens = tokenize.tokenize(f.readline)
        for toknum, tokval, *_ in tokens:
            if toknum == tokenize.COMMENT:
                comments.append(tokval.strip())
    return comments

if __name__ == "__main__":
    # Example usage:
    list_python_files = []
    dir_path = input("Enter path to directory: ")
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            if file.endswith(".py"):
                list_python_files.append(os.path.join(root, file))
    
    dict_comments_files = {}
    for file in list_python_files:
        comments = extract_comments(file)
        if comments:
            dict_comments_files[file] = comments
    
    with open('./comments_scripts.txt', mode='w', encoding='utf-8') as f:
        for file, comments in dict_comments_files.items():
            for comment in comments:
                f.write(f"""
{file.replace(os.sep, '/')}
{comment}
{'-'*20}

""")
    for k,v in dict_comments_files.items():
        if sum([len(i) for i in v]) > 2000:
            print(f"{k} has {len(v)} comments; {sum([len(i) for i in v]) } characters")



