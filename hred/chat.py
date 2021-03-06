import tensorflow as tf
import sys
import numpy as np
import math

from Dialogue import Dialogue
from model import Seq2Seq

class chatbot:
    def __init__(self, voc_path):
        self.dialogue = Dialogue(voc_path)
        self.model = Seq2Seq(self.dialogue.input_max_len, self.dialogue.output_max_len, self.dialogue.voc_size, self.dialogue.word_embedding_matrix, False)

        self.sess = tf.Session()

        # 모델 불러오기
        ckpt = tf.train.get_checkpoint_state('./model')
        self.model.saver.restore(self.sess, ckpt.model_checkpoint_path)

    def run(self):
        sys.stdout.write("> ")
        sys.stdout.flush()
        line = sys.stdin.readline()

        while line:
            print(self.get_replay(line.strip())) # 응답

            sys.stdout.write("\n> ")
            sys.stdout.flush()

            line = sys.stdin.readline()

    def _decode(self, enc_input, dec_input):
        if type(dec_input) is np.ndarray:
            dec_input = dec_input.tolist()

        enc_len = enc_input.__len__()
        dec_len = len(dec_input)

        enc_input, dec_input, _ = self.dialogue.transform(enc_input, dec_input, self.dialogue.input_max_len, self.dialogue.output_max_len)
        return self.model.predict(self.sess, [enc_input], [enc_len], [dec_input], [dec_len+1])

    # msg에 대한 응답을 반환
    def get_replay(self, msg):
        enc_input = self.dialogue.tokenizer(msg)
        enc_input = self.dialogue.tokens_to_ids(enc_input)
        dec_input = []

        outputs = self._decode(enc_input, dec_input)
        if self.dialogue.is_eos(outputs):
            reply = self.dialogue.decode([dec_input], True)
        # 디코더의 출력을 디코더의 입력으로 넣는다.
        # curr_seq = 0
        # for i in range(self.dialogue.max_seq_len):
        #     outputs = self._decode(enc_input, dec_input)
        #     if self.dialogue.is_eos(outputs[0][curr_seq]):
        #         break
        #     elif self.dialogue.is_defined(outputs[0][curr_seq]) is not True:
        #         dec_input.append(outputs[0][curr_seq])
        #         curr_seq += 1
        #
        # # 문자열로 반환
        # reply = self.dialogue.decode([dec_input], True)

        return reply

path = './data/chat.log'

def main(_):
    print("깨어나는 중 입니다. 잠시만 기다려주세요...\n")

    Chatbot = chatbot(path)
    Chatbot.run()

if __name__ == "__main__":
    tf.app.run()