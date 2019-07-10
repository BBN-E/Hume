import sys,re



def main(input_file):
    with open(input_file,'r') as fp:
        script = fp.read()
    pattern = re.compile(r'\d+\.?\d?G')
    processed_script = pattern.sub('6G',script)
    with open(input_file,'w') as fp:
        fp.write(processed_script)


if __name__ == "__main__":
    main(sys.argv[1])
