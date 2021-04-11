# coding=utf-8
import importlib, sys
importlib.reload(sys)
import os
from pyltp import SentenceSplitter, Segmentor, Postagger, NamedEntityRecognizer, Parser, SementicRoleLabeller, \
    CustomizedSegmentor
import jiagu

def sentence_split(text):
    sents = SentenceSplitter.split(text)  # 分句


self_nertag={
    'Ns':'LOC',
    'Nh':'PER',
    'Ni':'ORG'
}

class LtpModelAnalysis(object):
    def __init__(self, model_dir='/Users/wangshanshan/Desktop/ltp_data_v3.4.0'):
        #jiagu.load_userdict(config.lexicon_path)

        self.postagger = Postagger()
        self.postagger.load(os.path.join(model_dir, "pos.model"))  # 加载词性标注模型

        self.recognizer = NamedEntityRecognizer()
        self.recognizer.load(os.path.join(model_dir, "ner.model"))  # 加载命名实体识别模型

        self.parser = Parser()
        self.parser.load(os.path.join(model_dir, "parser.model"))  # 加载依存句法分析模型

    def analyze(self, text):
        # 分词
        #words = self.segmentor.segment(text)
        temp=zip(list(text),range(len(text)))
        print(list(temp))
        words=jiagu.seg(text)
        print(words)
        # 词性标注
        postags = self.postagger.postag(words)


        # 命名实体识别
        netags = self.recognizer.recognize(words, postags)  # 命名实体识别
        print(list(netags))
        ner_words=[]

        netags=list(netags)
        length = len(netags)
        start,end=0,0
        for i ,netag in enumerate(netags):
            if 'B-' in netag:
                if i==length-1:

                    start = len(''.join(words[:i]))
                    end=start+len(words[i])-1
                    ner_words.append({'word': words[i], 'start': start, 'end': end+1, 'type': self_nertag[netag[2:]]})
                    break
                start = len(''.join(words[:i]))
                type = netag[2:]
            elif 'E-' in netag:

                end = len(''.join(words[:i]))+len(words[i])-1
                ner_words.append({'word': ''.join(words)[start:end+1], 'start': start, 'end': end+1, 'type': self_nertag[type]})
                start=end
            elif 'S-' in netag:
                start=len(''.join(words[:i]))
                end = start+len(words[i])-1
                ner_words.append({'word': ''.join(words[i]), 'start': start, 'end': end+1, 'type': self_nertag[netag[2:]]})
                start=end
            else:
                continue


        return ner_words



    def release_model(self):
        # 释放模型
        #self.segmentor.release()
        self.postagger.release()
        self.recognizer.release()
        self.parser.release()
        #self.labeller.release()


if __name__ == '__main__':

    ltp = LtpModelAnalysis()
    # [{'word': '巧手教育', 'start': 2, 'end': 6, 'type': 'WJ'}]
    while True:
        text=input('请输入句子')
        ner_words = ltp.analyze(text)
        print(ner_words)
    ltp.release_model()



