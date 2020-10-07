import os,tarfile


def main():
    input_root = "/nfs/raid68/u15/ears/expts/47877.092520.v1/expts/hume_test.041420.cx.v1/serialization"
    output_root = "/nfs/raid88/u10/users/hqiu/tmp/tmp"

    cnt = 0
    for root,dirs,files in os.walk(input_root):
        for file in files:
            if file.endswith("tar.gz"):
                with tarfile.open(os.path.join(root,file), 'r:gz') as tar_fp:
                    tar_fp.extractall(output_root)
                    cnt = cnt + 1
        if cnt > 500:
            break

if __name__ == "__main__":
    main()