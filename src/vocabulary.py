from typing import List, Optional
from collections import Counter

class Vocabulary:
    """
    Vocabulary class responsible for maintaining the mapping between raw string tokens (words)
    and their corresponding unified integer indices. This mapping is required before text can 
    be fed into the neural network's embedding layer.
    """
    
    def __init__(self, min_freq: int = 5):
        """
        Initializes the Vocabulary object.
        
        Args:
            min_freq: The minimum number of times a word must appear across all documents 
                      to be included in the vocabulary. Words appearing less frequently are 
                      treated as unknown (<UNK>) to prevent the model from overfitting on outliers.
        """
        self.min_freq = min_freq
        
        # word2idx: Dictionary mapping a string token to an integer ID.
        # Index 0 is reserved for <PAD> which is used to make all sequences the same length.
        # Index 1 is reserved for <UNK> which represents out-of-vocabulary or rare words.
        self.word2idx = {'<PAD>': 0, '<UNK>': 1}
        
        # idx2word: Reverse dictionary mapping an integer ID back to the string token.
        self.idx2word = {0: '<PAD>', 1: '<UNK>'}
        
        # Counter to keep track of word frequencies during the build phase.
        self.word_freq = Counter()
    
    def build(self, tokenized_docs: List[List[str]]):
        """
        Builds the vocabulary mapping based on a list of tokenized documents.
        
        Args:
            tokenized_docs: A list where each element is a list of string tokens representing one document.
            
        Returns:
            self: Returns the updated Vocabulary instance for method chaining.
        """
        # Iterate through all documents and tally up the occurrences of each word
        for tokens in tokenized_docs:
            self.word_freq.update(tokens)
        
        # Start assigning IDs from 2, as 0 and 1 are already taken by PAD and UNK
        idx: int = 2
        
        # most_common() returns words sorted by frequency descending.
        # This means lower IDs are given to more common words.
        for word, freq in self.word_freq.most_common():
            # Only add words that meet the frequency threshold
            if freq >= self.min_freq:
                self.word2idx[word] = idx
                self.idx2word[idx] = word
                idx = idx + 1  # type: ignore[operator]
        
        return self
    
    def encode(self, tokens: List[str], max_length: Optional[int] = None) -> List[int]:
        """
        Converts a list of string tokens into a list of integer indices based on the built vocabulary.
        
        Args:
            tokens: List of strings (words).
            max_length: Optional parameter to strictly enforce the output sequence length.
            
        Returns:
            List of integers representing the input tokens.
        """
        # Convert each token to its designated ID. If the token is not found in word2idx, 
        # it defaults to 1 (the ID for <UNK>).
        indices = [self.word2idx.get(t, 1) for t in tokens]  
        
        # If a max_length is specified, truncate or pad the sequence to fit
        if max_length:
            if len(indices) > max_length:
                # Truncate sequence if it exceeds max_length
                indices = indices[0:int(max_length)]  # type: ignore[index]
            else:
                # Pad sequence with 0s (<PAD>) if it's shorter than max_length
                indices = indices + [0] * (max_length - len(indices))  
        
        return indices
    
    def decode(self, indices: List[int]) -> List[str]:
        """
        Converts a sequence of integer IDs back into their readable string format.
        
        Args:
            indices: List of integers.
            
        Returns:
            List of string tokens.
        """
        # Map each index back to its word. 
        # Default to '<UNK>' if the index isn't found.
        # Ignore index 0 (<PAD>) to avoid cluttering the output with padding tokens.
        return [self.idx2word.get(i, '<UNK>') for i in indices if i != 0]
    
    def __len__(self):
        """
        Returns the total number of unique words currently in the vocabulary.
        This includes the special <PAD> and <UNK> tokens.
        """
        return len(self.word2idx)
