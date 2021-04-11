# -*- coding:utf-8 -*-
import http.server
import json
from urllib import parse
import sys
import requests
import re
import os
import pickle
import LTP_NER
import tensorflow as tf
from utils import create_model, get_logger
from model import Model
from loader import input_from_line
from train import FLAGS, load_config
from  pyltp import SentenceSplitter
if len(sys.argv) < 2:
    print("error! port number not input")
    exit(0)

PORT_NUMBER = int(sys.argv[1])

print(PORT_NUMBER,'port_number')
os.environ['CUDA_VISIBLE_DEVICES'] = '0'
#tf.app.run(main)
config = load_config(FLAGS.config_file)
logger = get_logger(FLAGS.log_file)
# limit GPU memory
tf_config = tf.ConfigProto()
tf_config.gpu_options.allow_growth = True
with open(FLAGS.map_file, "rb") as f:
    tag_to_id, id_to_tag = pickle.load(f)
sess = tf.Session(config=tf_config)
enti_model = create_model(sess, Model, FLAGS.ckpt_path, config, logger)



# 加载ltp，结合自己的模型用于实体识别
ltp = LTP_NER.LtpModelAnalysis()
senspliter=SentenceSplitter()
# 关系schema
#创始人  工作单位 研制者，研制组织，作者，毕业院校
rel_schema=[('ORG','PER'),('WJ','PER'),('PER','ORG'),('WJ','PER'),('WJ','ORG'),('BAP','PER')]


def remove_duplicated(self_results, ltp_results):
    res = []
    drop_index = set()
    drop_index1 = set()
    for i, candi1 in enumerate(self_results):
        for j, candi2 in enumerate(ltp_results):
            # 以相同下标开始的实体，选预测长度更长的那个
            #if candi1['start'] == candi2['start']:

            # 解决两实体始末下标有交叉项，取起始下标更小或者长度更长的实体
            if max(candi1['start'],candi2['start'])<=min(candi1['end'],candi2['end']):
                if len(candi1['word']) > len(candi2['word']):
                    drop_index1.add(j)
                else:
                    drop_index.add(i)

    # 删除同起始下标的冗余项实体
    for i, term in enumerate(self_results):
        if i not in drop_index:
            res.append(term)
    for j, term in enumerate(ltp_results):
        if j not in drop_index1:
            res.append(term)


    return res

map_word={
    "T":"事故类型",
    "K":"罪名",
    "D":"主次责任",
    "P":"减刑因素",
    "N":"加刑因素",
    "R":"判决结果",
    "PER": "人物"
}
# 标点符号和特殊字母
punctuation = '''，、:；（）ＸX×xa"“”,<《》'''

# This class will handles any incoming request from
# the browser
class myHandler(http.server.BaseHTTPRequestHandler):

    # Handler for the GET requests
    def do_GET(self):
        p = parse.urlparse(self.path)
        qsl = parse.parse_qsl(p.query)
        #print(qsl)
        text=None
        for (para, value) in qsl:
            if para == 'text':
                text = value


        text = text.replace(' ','')
        line1 = re.sub(u"（.*?）", "", text)  # 去除括号内注释
        line2 = re.sub("[%s]+" % punctuation, "", line1)  # 去除标点、特殊字母
        # 去除冗余词
        line3 = re.sub(
            "本院认为|违反道路交通管理法规|驾驶机动车辆|因而|违反道路交通运输管理法规|违反交通运输管理法规|缓刑考.*?计算|刑期.*?止|依照|《.*?》|第.*?条|第.*?款|的|了|其|另|已|且",
            "",
            line2)
        line4=line3.replace('\n','')
        print(line4)

        parse_result=[]
        for sen in senspliter.split(line4):
            self_results = enti_model.evaluate_line(sess, input_from_line(sen, FLAGS.max_seq_len, tag_to_id), id_to_tag)['entities']
            ltp_results=ltp.analyze(sen)

            # 编写一个函数，当bert和LTP_NER两个实体出现同起点下标同类型，取较长的那个
            results = remove_duplicated(self_results,ltp_results)
            print('合并后的实体是：',results)

            entis =[]
            entis_type=[]
            enti_pair_set=set()
            for enti in results:
                enti_word = enti['word']
                enti_type = enti['type']
                if 'WJ' in enti_type:
                    pattern='[0-9a-zA-Z\-\(\)]*'+enti_word+'[0-9a-zA-Z\-\(\)]*'
                    render_words = re.findall(pattern,text)
                    sorted_words = sorted(render_words, key=lambda x: len(x), reverse=True)
                    if len(sorted_words):
                        entis.append(sorted_words[0])
                    else:
                        entis.append(enti_word)
                else:
                    entis.append(enti_word)
                entis_type.append(enti_type)
            res = {
                'text':sen,
                'entities':list(zip(entis,entis_type))
            }
            parse_result.append(res)
        result=parse_result
        new_result={
            "text":text,
            "result":{}
        }
        for result in parse_result:
            print("result:", result)
            for each in result['entities']:
                print("each:", each)
                temp=new_result['result'].get(map_word[each[1]],[])
                temp.append(each[0])
                new_result['result'][map_word[each[1]]]=list(set(temp))
        result = json.dumps(new_result,ensure_ascii=False).encode()
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*') # CORS add by vanellope
        self.end_headers()

        self.wfile.write(result)

        # return



try:

    # Create a web server and define the handler to manage the
    # incoming request
    server = http.server.HTTPServer(('', PORT_NUMBER), myHandler)
    print('Started httpserver on port ', PORT_NUMBER)

    # Wait forever for incoming http requests
    server.serve_forever()

except KeyboardInterrupt:
    print('^C received, shutting down the web server')
    server.socket.close()
