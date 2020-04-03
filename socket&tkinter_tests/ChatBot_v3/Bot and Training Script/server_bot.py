# -*- coding: utf-8 -*-
"""
Created on Mon Mar  2 23:38:43 2020

    Prototype 6 - Refactored - ONLY BOT No Training
    
        Somewhat overly refactored in places - this is because it is a copy of the training script.
        Essentially the same script as the training script except only chatting functionality based on models loaded in.
        See training script for in depth annotation on functionality and training functions.
    
        Next up:
            Potentially include Lemmatization / Named Entity Recognition etc (?)
            
            Include some of the previous data set for variety?
            There is a question intent ! 
            If we can get the intent thing to work and it recognizes those
            prompts like "Can I ask a question?" etc
            It would be awesome to draw upon that second data set to answer questions!

@author: tpvan
"""

"""
--------------------------------------------------------------------------------------------------
Basic Imports:
    
    Keras: Library used to build the ANN/RNN. Requires the keras libary to be installed.
    
    Spacy: Requires the spacy library to be installed.
           NLP library - Not used for alot beyond tokenization during the building
           of the vocabulary.
    
    Pickle : Used for serializing and deserializing python objects.
    
    Pandas : Library for reading in csv files or tsv files.
    
    Numpy : Python Math library, contains functions for processing large matrices
            As well as other fancy pants mathematical functions.
    
    Tkinter : Simple GUI.
    
    Listener : Multiprocessing module that allows us to create a listener on a server port.
            
--------------------------------------------------------------------------------------------------
"""
from multiprocessing.connection import Listener
from tkinter import *
from tkinter import scrolledtext, INSERT, Button, Label, Entry, END, Tk
from PIL import ImageTk, Image
import pickle
import numpy as np
import spacy
import os
import string
import random
nlp = spacy.load('en_core_web_sm')


# Get previous directory
this_dir = os.path.dirname(os.path.dirname(__file__))
print(this_dir)
split_dir = this_dir.split('\\')
prev_dir = ""
for i in range(len(split_dir)):
    prev_dir = prev_dir + split_dir[i] + '/'
    if split_dir[i] == 'ChatBot_v2':
        break


# Global Variables for convenience
model_load_name = prev_dir + 'data/chat_bot_experiment_5000_128_dialogue_dropout_validated_on_train_v2.h5'
intents_model_load_name = prev_dir + 'data/chat_bot_experiment_5000_128_dialogue_dropout_validated_on_train_INTENTS.h5'
data_frame_load_name = prev_dir + 'data/qa_df.txt'
train_data_frame_load_name = prev_dir + 'data/qa_train_df_v2.txt'
test_data_frame_load_name = prev_dir + 'data/qa_test_df_v2.txt'
indexed_ans_list_load_name = prev_dir + 'data/qa_indexed_ans_v2.txt'
tokenizer_load_name = prev_dir + 'data/dialogue_tokenizer_v2.txt'
vocab_load_name = prev_dir + 'data/dialogue_vocab_v2.txt'
images_path = prev_dir + 'Images/'


"""
------------------------------------------------------------------------------------------------
Step 1: Load in all data
    
    The data frame's format is [([int:idx], [intent], [question], [answer])]
    The indexed answers list is just [(int:idx, [answer])] - Used to print answers at run time.
------------------------------------------------------------------------------------------------
"""

def load_data_frames():
    # full data frame
    with open(data_frame_load_name, 'rb') as f:
        all_data = pickle.load(f)
            
    return all_data;


def load_idx_ans_list():
    # list of all indexed the answers used to print out answer at run time.
    with open(indexed_ans_list_load_name, 'rb') as f:
        idx_ans_list = pickle.load(f)
        
        return idx_ans_list
    
# Seperates punctuation, to lowercase and tokenizes input.
def seperate_punct_doc(doc):
    return [token.text.lower() for token in doc if token.text not in '\n\n \n\n\n--!"#$%&()*+,-./:;<=>?@[\\]^_`{|}~\t\n']

 
"""
------------------------------------------------------------------------------------------------
Step 2: Load in the generated vocabulary our model learned on.
    
    The vocab in this case serves as a means of checking the words exist in the vocab the model was trained on.
    The tokenizer is loaded because it was used to index the vocab the model was trained on.
    
------------------------------------------------------------------------------------------------
"""

# imports for Tokenizer and padding
from keras.preprocessing.sequence import pad_sequences
from keras.preprocessing.text import Tokenizer

# Alternative to creating new vocab -- load in previously created vocab set.
def load_vocab(filename):
    print("Loading Vocab ...")
    with open(filename, 'rb') as fp:
            vocab = pickle.load(fp)
    
    return vocab

# Adds padding to the length of the vocab.
def vocab_len(vocab):
    return len(vocab) + 1

# Alternative to creating a new tokenizer, previously used tokenizer can be loaded in.
def load_tokenizer():
    with open(tokenizer_load_name, 'rb') as fp:
              tokenizer =  pickle.load(fp)     
              
              return tokenizer
             

"""
------------------------------------------------------------------------------------------------
Step 3: Vectorizing the data - No differences here - Could be refactored.
    
    For the model to understand any of the text data we have to vectorize the intents, answers and questions.
    Using our unique set of words called vocab we give each word its own unique index.
    We then use these indexes to represent the sentences as vectors whocse components consist
    of the corresponding index values.
    
    Because we don't have identical size intent, questions and answers we need to determine the
    largest of each and pad every other vector with 0's to match that size.
    
------------------------------------------------------------------------------------------------
"""

# The following method actually performs the vectorization FOR the intent, answers and questions.
def vectorize_qa_data(data, word_index, max_intent_len, max_question_len):
    
    # intent
    X=[]    
    # Questions
    Xq =[]
    # Correct Answers
    Y = []
    
    # Creating vectors of all the indexes created above
    for index, intent, question, answer in data:
        
        # For each word in intent, Question and Answer find their corresponding index, 
        # use list comprehension to create a vector of each index.
        x = [word_index[word.lower()] for word in intent]
        xq = [word_index[word.lower()] for word in question]
        
        # create a vector of all 0's and 1 one at answers index
        y = np.zeros(len(word_index)+1)
        y[word_index[str(answer[0])]] = 1
       
        # Then add that vector to the corresponding main list.
        X.append(x)
        Xq.append(xq)
        Y.append(y)
    
        # return a tuple that can be unpacked - and pad each of the sequences!
    return (pad_sequences(X, maxlen=max_intent_len), pad_sequences(Xq, maxlen=max_question_len), np.array(Y))


# Vectorization FOR the questions and intents only - Somewhat redundant considering above function.
def vectorize_intents_data(data, word_index, max_question_len):
    
    # Questions
    X =[]
    # Correct Answers - intents
    Y = []
    
    # Creating vectors of all the indexes created above
    for index, intent, question, answer in data:
        
        # For each word in Question and Answer find their corresponding index, 
        # use list comprehension to create a vector of each index.
        x = [word_index[word.lower()] for word in question]
        
        # create a vector of all 0's and 1 one at answers index - intent is one word - i.e. smalltalk.agent.beautiful
        y = np.zeros(len(word_index)+1)
        y[word_index[str(intent[0])]] = 1
       
        # Then add that vector to the corresponding main list.
        X.append(x)
        Y.append(y)
    
        # return a tuple that can be unpacked - and pad each of the sequences!
    return (pad_sequences(X, maxlen=max_question_len), np.array(Y))

"""
-----------------------------------------------------------------
Step 4 : Loading Models

    No training models in this script just the loading of the models trained using the
    training script.
    
-----------------------------------------------------------------
"""

from tensorflow.keras.models import load_model

# Loads a previously trained model
def load_prev_model(filename):
    print("Loading Model ...")
    model = load_model(filename)
    
    return model

"""
-----------------------------------------------------------------
Step 5: Setup Function

    Setup function refactored into several more concise functions:
    For convenience in main method still used as a collection point for the other method calls.
    
-----------------------------------------------------------------
"""

# The max lengths of all inputs and outputs are required to pad the sequences appropriately (See vectorize data function.)
def determine_max_lengths(all_data):
       # longest intent Name
    all_intent_lengths = [len(data[0]) for data in all_data]
    # max length 
    max_intent_len = max(all_intent_lengths)
    # max question length
    max_question_len = max([len(data[1]) for data in all_data])
    # max answer length
    max_answer_len = max([len(data[2]) for data in all_data])
    
    return all_intent_lengths, max_intent_len, max_question_len, max_answer_len


# loads previously created vocab, tokenizer and determine the vocab length
def retrieve_vocab():
    vocab = load_vocab(vocab_load_name)
    tokenizer = load_tokenizer()   
    vocab_length = vocab_len(vocab)
        
    return vocab, tokenizer, vocab_length

# loads previous model - model name at top of script
def retrieve_qa_model():
    return load_prev_model(model_load_name)

# loads previous model - model name at top of script
def retrieve_intents_model():
    return load_prev_model(intents_model_load_name)
          

# Collection point for the above functions used to set up the data required to run the model.
def setup():
    
    # The data loaded depends on what data was processed and saved by the conversion script
    all_data = load_data_frames()

    # Same with the indexed answers' list
    idx_ans_list = load_idx_ans_list()
    
    # Retrieve Vocab and tokenizer
    vocab, tokenizer, vocab_length = retrieve_vocab()
    
    # Retrive all the maximum lenghts of the arguments for the model - used to pad sequences.
    all_intent_lengths, max_intent_len, max_question_len, max_answer_len = determine_max_lengths(all_data)
    
    model = retrieve_qa_model()
    intents_model = retrieve_intents_model()
      
    return model, intents_model, vocab, tokenizer, idx_ans_list, max_intent_len, max_question_len

"""
-----------------------------------------------------------------
Step 11: GUI - 

    Ian I've done my best to refactor it into concise methods with
    one or two functions - I can only get it to print as it should
    with the funky function def going on in the main method rn.
    Feel free to undo all the refactoring on the GUI of course, I was
    not as confident in all its functionality as with the code I wrote obviously.
    
-----------------------------------------------------------------
"""

def get_intent_prediction(intents_model, my_question, tokenizer, max_question_len):
    
    # Strange format is because the same vectorization method from training is used - which takes all four arguments.
    my_intent_data = [(['0'], my_question, my_question, ['work'])]
    my_intent_question, my_intent_answer = vectorize_intents_data(my_intent_data, tokenizer.word_index, max_question_len)
    
    # Predict the most likley intent based on question
    pred_results = intents_model.predict(([my_intent_question, my_intent_question]))
    val_max = np.argmax(pred_results[0])
    
    # retrieve the value
    for key, val in tokenizer.word_index.items():
        if val == val_max:
            k = key
    
    # k is a string - this converts it back to the same format used in training.
    my_intent = seperate_punct_doc(nlp(k))
    
    return my_intent

   
def get_bot_answer(model, my_intent, my_question, tokenizer, max_intent_len, max_question_len):
     
    my_data = [(['0'], my_intent, my_question, ['work'])]
    my_intent, my_question, my_answer = vectorize_qa_data(my_data, tokenizer.word_index, max_intent_len, max_question_len)
    
    pred_results = model.predict(([my_intent, my_question]))
    val_max = np.argmax(pred_results[0])
    
    for key, val in tokenizer.word_index.items():
        if val == val_max:
            k = key
    
    return k

def print_bot_answer(bot_answer, idx_ans_list):
    if(str(bot_answer).isdigit()):
        #response.configure(text = ' '.join(idx_ans_list[int(bot_answer)-1][1]))
        #hst.insert(INSERT, "Chatbot: " + ' '.join(idx_ans_list[int(bot_answer)-1][1]) + "\n")
        #response.configure(text = ' '.join(idx_ans_list[int(bot_answer)][1][1:]))
        conn.send("" + ' '.join(idx_ans_list[int(bot_answer)][1][1:]) + "\n")
       
# Similar to set up function this function servers as a collection point for the other method calls.
def generate_answer(rst, model, intents_model, vocab, tokenizer, idx_ans_list, max_intent_len, max_question_len):
                
    # Retrieve text from text box
    global my_intent
    my_question_text = rst
                
    # Tokenize and remove punctuation
    my_question = seperate_punct_doc(nlp(my_question_text))
            
    
    
    """
    The following line works as advertised but in the case that the final question contains 0 words in vocab 
    an index out of bounds error is thrown in vectorizing the data - b/c question / intent will be empty list.
    This is a prime spot to implement either an intent to print "Can't answer that question" or straight up print it.
    The program does not break - the index out of bounds is handled by the GUI, it simply does not say anything back rn
    for example try saying "sassy" to the bot.
    """
    
    # Remove words not currently in vocab -
    my_question = [word for word in my_question if word in vocab]

    # Insert user's original question text in chat window.
    # Send the user's original question text back to the client chat bot to display
    #conn.send("Client: " + my_question_text + "\n")

    # If no vocab is found
    if not my_question:

        unknown_answers = ["Don't know.",  "What??", "I don't understand what you're trying to say.", "Let's talk about something else.", "Was that English?", "Can you try wording that differently?", "I'm not sure what that means."]

        random_index = random.randint(0, len(unknown_answers) - 1)

        conn.send(unknown_answers[random_index] + "\n")
    
    else:
    
        # Predict the Intent based on the question
        my_intent = get_intent_prediction(intents_model, my_question, tokenizer, max_question_len)

        # Update the bot image according to the intent
        #set_bot_img(my_intent, img_panel)
     
        # Predict the Answer based on predicted intent and question / prompt
        bot_answer = get_bot_answer(model, my_intent, my_question, tokenizer, max_intent_len, max_question_len)
           
        print_bot_answer(bot_answer, idx_ans_list)        

def process_input(rst):
        generate_answer(rst, model, intents_model, vocab, tokenizer, idx_ans_list, max_intent_len, max_question_len)
        
"""
---------------------------------------------------------------------------------
Main Program Loop
---------------------------------------------------------------------------------
"""
if __name__ == '__main__':
   
    # Initialize model and GUI
    model, intents_model, vocab, tokenizer, idx_ans_list, max_intent_len, max_question_len = setup()  
    
    '''
    ---------------------------------------------------------------------------------
    Socket Listener Setup
    
        I didn't feel like there was a need to create a GUI for the listener chat bot. 
        All it needs to do is wait for a connection, then repeatedly recieve and respond
        to input from the client chat bot. To do that, I used a while True loop that has 
        the option to break out of the loop and close the connection if the stop keyword 
        is given
    ---------------------------------------------------------------------------------
    '''
    
    #Family is deduced to be 'AF_INET' from the host given
    address = ('localhost', 7000)
    
    #Random greeting list
    randGreeting = ["Lovely to see you.","How are you?","hope your day is going well", "hope you re having a pleasant evening", "how your day is going"]
    
    #Wrapper for socket referred to by address
    with Listener(address) as listener:
        print('Waiting for connection ...')
        #Returns a Connection object
        with listener.accept() as conn:
            print('Connection accepted from', listener.last_accepted)
            
            #This will hold the last recieved query.
            lastRst = ''
            
            try:
                conn.send(random.choice(randGreeting))
                while True:       
                    
                    rst = conn.recv()
                    
                    #This will handle conversational loops
                    if (rst == lastRst):
                        random_prompt = ["What was your day like?",  "How is your day?", "How are you going?", "Let's talk about something else.", "Good to see you", "How are you getting on?", "Good, what's up?"]
                        random_index = random.randint(0, len(random_prompt) - 1)
                        conn.send(random_prompt[random_index])
                        continue
                    
                    if (rst == 'stop'):
                        conn.send('stop')
                        print('Closed connection with client chatbot')
                        break
                    
                    lastRst = rst
                    process_input(rst)
                    
            except (ConnectionResetError, ConnectionAbortedError):
                print('Connection to the client was closed.')
        
        
        
