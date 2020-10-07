

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--in_par_file_path",type=str,required=True)
    parser.add_argument("--out_par_file_path",type=str,required=True)
    parser.add_argument("--num_of_batches",type=int,default=50)
    parser.add_argument("--num_of_scheduling_jobs_for_nn",type=str,default="unknown")

    args = parser.parse_args()
    output_buf = list()

    with open(args.in_par_file_path) as fp:
        for i in fp:
            i = i.replace("[PENDING_NUM_OF_BATCHES]",str(args.num_of_batches))
            i = i.replace("[PENDING_NUM_OF_SCHEDULING_JOBS_FOR_NN]",str(args.num_of_scheduling_jobs_for_nn))
            output_buf.append(i)
    with open(args.out_par_file_path,'w') as wfp:
        for i in output_buf:
            wfp.write(i)