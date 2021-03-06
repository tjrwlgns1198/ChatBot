import re
import numpy as np
import math
import tensorflow as tf

class Dialogue:

    def __init__(self, path):
        self.PRE_DEFINED = ['_P_', '_S_', '_E_', '_U_']
        self.sentences = self.load_data(path)
        self.voc_arr = self.PRE_DEFINED + self.make_voc()
        self.voc_dict = {voc: i for i, voc in enumerate(self.voc_arr)}
        self.voc_size = len(self.voc_dict)
        self.seq_data = self.make_seq_data()
        self.input_max_len = max([len(self.seq_data[i]) for i in range(0, len(self.seq_data), 2)])+1
        self.output_max_len = max([len(self.seq_data[i+1]) for i in range(0, len(self.seq_data), 2)])+1

        self.word_embedding_matrix = self.make_word_embedding_matrix()
        self.index_in_epoch = 0

    # 파일로부터 문장을 읽어온다.
    def load_data(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            sentences = [line.strip() for line in f]
        return sentences

    # 단어용 벡터 맥트릭스
    def make_word_embedding_matrix(self, embedding_dims=20):
        init_width = 1/embedding_dims
        word_embedding_matrix = tf.Variable(
            tf.random_uniform([self.voc_size, embedding_dims], -init_width, init_width, dtype=tf.float32),
            name="embeddings",
            dtype=tf.float32)
        return word_embedding_matrix

    # 문자열로 바꾸어준다.
    def decode(self, indices, string=False):
        tokens = [[self.voc_arr[i] for i in dec] for dec in indices]

        if string:
            return self._decode_to_string(tokens[0])
        else:
            return tokens

    def _decode_to_string(self, tokens):
        text = ' '.join(tokens)
        return text.strip()

    # E 가 있는 전까지 반환
    def cut_eos(self, indices):
        eos_idx = indices.index('_E_')
        return indices[:eos_idx]

    # E 인지 아닌지 검사
    def is_eos(self, voc_id):
        return voc_id == 2

    # 미리 정의한 (E, U, S, P)인지 검사
    def is_defined(self, voc_id):
        return voc_id in self.PRE_DEFINED

    # 정규화식에서 빼고 띄워쓰기 기준으로 자른다.
    def tokenizer(self, sentence):
        sentence = re.sub("[.,!?\"':;)(]", ' ', sentence)
        tokens = sentence.split()
        return tokens

    # 토큰을 id로 바꿔 반환한다.
    def tokens_to_ids(self, tokens):
        ids = [self.voc_dict[token] if token in self.voc_arr else self.voc_dict['_U_'] for token in tokens]
        return ids

    # id를 토큰으로 바꿔 반환한다.
    def ids_to_tokens(self, ids):
        tokens = [self.voc_arr[id] for id in ids]
        return tokens

    # max_len 만큼 패딩 추가.
    def pad(self, seq, max_len, start=None, eos=None):
        if start:
            padded_seq = [1] + seq  # 1은 시작 심볼
        elif eos:
            padded_seq = seq + [2]  # 2는 끝 심볼
        else:
            padded_seq = seq

        if len(padded_seq) < max_len:
            return padded_seq + ([0] * (max_len - len(padded_seq))) # 0은 패딩 심볼
        else:
            return padded_seq

    # 사전을 만든다.
    def make_voc(self):
        voc_set = set()
        for sentence in self.sentences:
            voc_set.update(self.tokenizer(sentence))
        return list(voc_set)

    # 문자열을 숫자(index) 배열로 만든다.
    def make_seq_data(self):
        seq_data = [self.tokens_to_ids(self.tokenizer(sentence)) for sentence in self.sentences]

        return seq_data

    # batct_size만큼 입력데이터를 반환
    def next_batch(self, batch_size):
        enc_batch = []
        dec_batch = []
        target_batch = []
        enc_length = []
        dec_length = []

        start = self.index_in_epoch

        if self.index_in_epoch + batch_size < len(self.seq_data) - 1:
            self.index_in_epoch = self.index_in_epoch + batch_size
        else:
            self.index_in_epoch = 0

        batch_set = self.seq_data[start:start + batch_size]
        for i in range(0, len(batch_set) - 1, 2):
            enc, dec, tar = self.transform(batch_set[i], batch_set[i+1], self.input_max_len, self.output_max_len)

            enc_batch.append(enc)
            dec_batch.append(dec)
            target_batch.append(tar)
            enc_length.append(len(batch_set[i]))
            dec_length.append(len(batch_set[i+1])+1)

        return enc_batch, enc_length, dec_batch, dec_length, target_batch, len(batch_set)

    # 입력과 출력을 변환
    def transform(self, input, output, max_len_input, max_len_output):

        # 각각의 길이만큼 심볼 추가
        enc_input = self.pad(input, max_len_input)
        dec_input = self.pad(output, max_len_output, start=True)
        target = self.pad(output, max_len_output, eos=True)

        return enc_input, dec_input, target

