cat +batch_file+ | \
(for i in `awk -F'/' '{print $NF}' | sed 's/\(\(\.xml\)\|\(\.sgm\)\|\(\.serifxml\)\)\+\$//'`;
do
  grep $i +bias_metadata+ \
  | awk '{system("ssh +bias_host+ \"curl localhost:5000/credibility/"$7"\" > +batch_output_dir+/"$1".json")}' \
; done)