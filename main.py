#imports
#library for linking pyhton and HTML
from flask import Flask, render_template, request, url_for, jsonify

#for accessing the folders
import os
os.environ["TF_CPP_MIN_LOG_LEVEL"]="3"
import csv

# for data cleaning
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem.isri import ISRIStemmer
import re
import string

#to access data structure
import pickle
import random

#path to laod Artificial lawyer data structer
pickleDataPath="C:\\Users\\TOSHIBA\\Desktop\\ArtificialLawyerChatbot\\ArtificialLawyerDataStructure"
#path to acess to responses directory
responsesFolderPath="C:\\Users\\TOSHIBA\\Desktop\\ArtificialLawyerChatbot\\Response"
#loading the data from pickle
data = pickle.load(open( pickleDataPath, "rb" ))
keywords = data['keywords']
cleaned_keywords_Dic = data['cleaned_keywords_Dic']
keywords_patterns_dic = data['keywords_patterns_dic']
matching_counter_dic = data['matching_counter_dic']
#greating dictionary
greeting_dic={'السلام عليكم ورحمه الله وبركاته':'وعليكم السلام ورحمة الله وبركاتة', 'السلام عليكم':'وعليكم السلام', 'مرحبا':'اهلا و سهلا', 'هلا':'مرحبا', 'اهلين':'مرحبتين', 'اهلا وسهلا':'هلا', 'مرحبتين':'أهلين', 'اهلا':'هلا'}
#replacement dictionary to replace undesirable word
replacments ={'مسئول':'صاحب العمل' ,'مسؤول':'صاحب العمل' ,'مدير': 'صاحب العمل', 'وزارة':'وزارة العمل', 'راتب':'أجر', 'إختبار':'تجربة', 'المرأة':'النساء', 'إجازته':'إجازة', 'الأجانب':'الغير سعوديين', 'الاطفال':'الاحداث'}
#normalize arabic sentences to prevent harakat, make all the alefat and haa' marbuta in one form
def normalizeArabic(sentence):
    noise = re.compile(""" ّ    | # Tashdid
                             َ    | # Fatha
                             ً    | # Tanwin Fath
                             ُ    | # Damma
                             ٌ    | # Tanwin Damm
                             ِ    | # Kasra
                             ٍ    | # Tanwin Kasr
                             ْ    | # Sukun
                             ـ     # Tatwil/Kashida
                         """, re.VERBOSE)
    sentence = re.sub(noise, '', sentence)
    sentence = re.sub("[إأٱآا]", "ا", sentence)
    sentence = re.sub("ة", "ه", sentence)
    return sentence
#clean up user's input
def clean_up_sentence(sentence):
    normalizeArabic(sentence)
    #using replacment dictionary to replace a popular words that clients may use
    for old,new in replacments.items():
        sentence=sentence.replace(old, new)
    sentence=sentence.replace('؟', ' ')
    #tokenize the pattern
    tokens = word_tokenize(sentence)
    #remove punctuation from each word
    remove_pun = str.maketrans('', '', string.punctuation)
    words = [w.translate(remove_pun) for w in tokens]
    #remove non-alphabetic characters
    alphabetic_words = [word for word in words if word.isalpha()]
    #remove arabic stop stop
    arabic_stop_word = stopwords.words('arabic')
    stop_words = set(arabic_stop_word)
    alphabetic_words = [word for word in alphabetic_words if not word in stop_words]
    #stem each word
    stemer = ISRIStemmer()
    stemmed_words = [stemer.stem(word) for word in alphabetic_words]
    stemmed_words = list(dict.fromkeys(stemmed_words))
    return stemmed_words
#matching between client's query and cleaned_keywords_Dic dictionary
#matching between client's query and keywords_patterns_dic dictionary
def matching(sentence):
    #clean up client's input
    client_query = clean_up_sentence(sentence)
    matching_counter_dic={}
    #matching client's query with cleaned_keywords_Dic dictionary
    for client_word in client_query:
        #matching each client's word with keywords
        for keywords,cleand_key_list in cleaned_keywords_Dic.items():
            #matching client's word with each cleaned key
            for key in cleand_key_list:
                #if there is a match then increase value of matching_counter_dic key by 1
                if client_word == key:
                    matching_counter_dic[keywords] = matching_counter_dic.get(keywords, 0) + 1
                else:
                    matching_counter_dic[keywords] = matching_counter_dic.get(keywords, 0)

        #matching client's query with patterns and count each keyword how much appear in client's query
        for key,pattern_list in keywords_patterns_dic.items():
            for pattern in pattern_list:
                if client_word == pattern:
                    matching_counter_dic[key] = matching_counter_dic.get(key, 0) + 1
                else:
                    matching_counter_dic[key] = matching_counter_dic.get(key, 0)
    return matching_counter_dic
#to generate the keyword who has the highest counter number
def match_filtering(sentence):
    #dictionary for keywords and its number of repetition
    matching_result = matching(sentence)
    #best match will used to hold the highest counter value and it's initialize to 0
    best_matching=int()
    #list that contain keywords which have the highest counter
    key_matched=[]
    #search for best matching keywords
    for key,counter in matching_result.items():
        if counter >= best_matching:
            best_matching = counter
    #put the best matched keyword in key_matched list
    for key,counter in matching_result.items():
        if counter == best_matching:
            key_matched.append(key)
    #check if client's query didn't match any thing in our dataset or match greater than 3 keywords then need specific input to get more appropriate keyword
    if((len(key_matched) == 0) or (len(key_matched) > 3 )):
        key_matched=[]
        key_matched.append('Questions')
    return key_matched
def make_response_dic(sentence):
    #get the best matching keywords
    match_filter = match_filtering(sentence)
    response_files=[]
    response_Dic ={}
    #change directory to responses folder
    os.chdir(responsesFolderPath)
    #put response .csv files name for the best matching keywords in response_files list
    for key in match_filter:
        response_files.append(key+".csv")
    #open each file in 'utf-8-sig' format
    for file in response_files:
        with open(file, encoding='utf-8-sig',errors='replace') as csv_file:
            # read all responses for the best matching keywords to get responses list
            responses = csv.reader(csv_file)
            if file == 'Questions.csv':
                #read each lines separately
                lines = open(file, encoding='utf-8-sig',errors='replace').read().splitlines()
                #choose random line for response
                row = random.choice(lines)
                response_Dic[row]=0
            else:
                #separate each response in seperate row from responses list
                for response in responses:
                    #save response as a key in response_Dic dictionary and assign its value to 0
                    for row in response:
                        response_Dic[row]=0
    return response_Dic
def response(sentence):
    #for greeting query
    greet= normalizeArabic(sentence)
    #replying by appropriate greet
    for key,val in greeting_dic.items():
        if(greet==key):
            return val

    #clean up client's query
    client_query=clean_up_sentence(sentence)
    #get all responses of the best matching keywords
    responses=make_response_dic(sentence)

    for response,counter in responses.items():
        #clean up the responses
        cleaned_response=clean_up_sentence(response)
        #matching each word in client's input with cleaned response and count each respons how much appear its words in client's input
        for client_word in client_query:
            for cleand_word in cleaned_response:
                if client_word == cleand_word:
                    responses[response] = responses.get(response, 0) + 1
                else:
                    responses[response] = responses.get(response, 0)
    best_matching=int()
    responses_matched=[]
    #find the best matching response
    for response,counter in responses.items():
        if counter >= best_matching:
            best_matching = counter
    for response,counter in responses.items():
        if counter == best_matching:
            responses_matched.append(response)
    return responses_matched[0]



app = Flask(__name__)


@app.route('/')
def index():
    return render_template('indexme.html')

@app.route('/background_process')
def background_process():
    lang = request.args.get('user_input')
    lang = str(lang)
    result = response(lang)
    result = str(result)
    # dict[lang] = result
    return jsonify(user_input=lang, response=result)

if __name__=='__main__':
    app.run(debug=True,port=5000)
