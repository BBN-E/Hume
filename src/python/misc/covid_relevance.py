

def main(input_list_file_path,output_list_path):
    word_list = {"新冠","冠状病毒","冠狀病毒","疫情","抗疫","肺炎","新冠肺炎","流行病","感染","病毒","传染","傳染","疾病","聚集","消毒","隔离","隔離","口罩",
                 "体温","體溫","传播","傳播","防控","检测","檢測","医疗","醫療","确诊","確診",
                 '新冠肺炎', '新冠病毒', '疫情', '疫苗', '新冠', '冠状病毒',"冠狀病毒", '确诊', '病例', '感染', '防疫', '防控', '检测', '核酸'
                 }
    with open(input_list_file_path) as fp,open(output_list_path,'w') as wfp:
        for i in fp:
            i = i .strip()
            with open(i) as fp2:
                raw_text = fp2.read()
                for word in word_list:
                    if word in raw_text:
                        print("YES {}".format(i))
                        wfp.write("{}\n".format(i))
                        break
                else:
                    print("NO {}".format(i))

if __name__ == "__main__":
    import sys
    main(sys.argv[1],sys.argv[2])