from typing import List
from collections import Counter

class Vocabulary:
    """
    Vocabulary for converting tokens to indices.
    """
    
    def __init__(self, min_freq: int = 5):
        self.min_freq = min_freq
        self.word2idx = {'<PAD>': 0, '<UNK>': 1}
        self.idx2word = {0: '<PAD>', 1: '<UNK>'}
        self.word_freq = Counter()
    
    def build(self, tokenized_docs: List[List[str]]):
        """Build vocabulary from tokenized documents"""
        # Count all words
        for tokens in tokenized_docs:
            self.word_freq.update(tokens)
        
        # Add frequent words to vocab
        idx = 2  # Start after PAD and UNK
        for word, freq in self.word_freq.most_common():
            if freq >= self.min_freq:
                self.word2idx[word] = idx
                self.idx2word[idx] = word
                idx += 1
        
        return self
    
    def encode(self, tokens: List[str], max_length: int = None) -> List[int]:
        """Convert tokens to indices"""
        indices = [self.word2idx.get(t, 1) for t in tokens]  # 1 = UNK
        
        if max_length:
            if len(indices) > max_length:
                indices = indices[:max_length]
            else:
                indices = indices + [0] * (max_length - len(indices))  # Pad
        
        return indices
    
    def decode(self, indices: List[int]) -> List[str]:
        """Convert indices back to tokens"""
        return [self.idx2word.get(i, '<UNK>') for i in indices if i != 0]
    
    def __len__(self):
        return len(self.word2idx)
