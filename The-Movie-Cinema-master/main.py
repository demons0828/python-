import numpy as np
import pandas as pd
from flask import Flask, render_template, request
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import json
import bs4 as bs
import urllib.request
import pickle
import requests
from datetime import date, datetime
import uuid


# 从磁盘加载nlp模型和tfidf向量器
filename = 'nlp_model.pkl'
clf = pickle.load(open(filename, 'rb'))
vectorizer = pickle.load(open('tranform.pkl','rb'))

#调用azure翻译API
def translate_text(text):
    subscription_key = '549a7d82141140f0963802f7859694d2'
    endpoint = 'https://api.cognitive.microsofttranslator.com'
    path = '/translate'
    params = {
        'api-version': '3.0',
        'from': 'en',
        'to': ['zh-Hans']
    }
    constructed_url = endpoint + path
    headers = {
        'Ocp-Apim-Subscription-Key': subscription_key,
        'Ocp-Apim-Subscription-Region': 'eastasia',
        'Content-type': 'application/json',
        'X-ClientTraceId': str(uuid.uuid4())
    }
    body = [{
        'text': text
    }]
    request = requests.post(constructed_url, headers=headers, json=body, params=params)
    response = request.json()
    return response[0]['translations'][0]['text']

    
# 将字符串列表转换为列表 (例如，将"["abc","def"]" 转换为 ["abc","def"])
def convert_to_list(my_list):
    my_list = my_list.split('","')
    my_list[0] = my_list[0].replace('["','')
    my_list[-1] = my_list[-1].replace('"]','')
    return my_list

# 将数字列表转换为列表 (例如，将"[1,2,3]" 转换为 [1,2,3])
def convert_to_list_num(my_list):
    my_list = my_list.split(',')
    my_list[0] = my_list[0].replace("[","")
    my_list[-1] = my_list[-1].replace("]","")
    return my_list

def get_suggestions():
    data = pd.read_csv('main_data.csv')
    return list(data['movie_title'].str.capitalize())

app = Flask(__name__)

@app.route("/")
@app.route("/home")
def home():
    suggestions = get_suggestions()
    return render_template('home.html',suggestions=suggestions)

@app.route("/populate-matches",methods=["POST"])
def populate_matches():
    # getting data from AJAX request
    res = json.loads(request.get_data("data"));
    movies_list = res['movies_list'];

    movie_cards = {"https://image.tmdb.org/t/p/original"+movies_list[i]['poster_path'] if movies_list[i]['poster_path'] else "/static/movie_placeholder.jpeg": [movies_list[i]['title'],movies_list[i]['original_title'],movies_list[i]['vote_average'],datetime.strptime(movies_list[i]['release_date'], '%Y-%m-%d').year if movies_list[i]['release_date'] else "N/A", movies_list[i]['id']] for i in range(len(movies_list))}

    return render_template('recommend.html',movie_cards=movie_cards);



@app.route("/recommend",methods=["POST"])
def recommend():
    # getting data from AJAX request
    title = request.form['title']
    cast_ids = request.form['cast_ids']
    cast_names = request.form['cast_names']
    cast_chars = request.form['cast_chars']
    cast_bdays = request.form['cast_bdays']
    cast_bios = request.form['cast_bios']
    cast_places = request.form['cast_places']
    cast_profiles = request.form['cast_profiles']
    imdb_id = request.form['imdb_id']
    poster = request.form['poster']
    genres = request.form['genres']
    overview = request.form['overview']
    vote_average = request.form['rating']
    vote_count = request.form['vote_count']
    rel_date = request.form['rel_date']
    release_date = request.form['release_date']
    runtime = request.form['runtime']
    status = request.form['status']
    rec_movies = request.form['rec_movies']
    rec_posters = request.form['rec_posters']
    rec_movies_org = request.form['rec_movies_org']
    rec_year = request.form['rec_year']
    rec_vote = request.form['rec_vote']
    rec_ids = request.form['rec_ids']

    # get movie suggestions for auto complete
    suggestions = get_suggestions()

    # call the convert_to_list function for every string that needs to be converted to list
    rec_movies_org = convert_to_list(rec_movies_org)
    rec_movies = convert_to_list(rec_movies)
    rec_posters = convert_to_list(rec_posters)
    cast_names = convert_to_list(cast_names)
    cast_chars = convert_to_list(cast_chars)
    cast_profiles = convert_to_list(cast_profiles)
    cast_bdays = convert_to_list(cast_bdays)
    cast_bios = convert_to_list(cast_bios)
    cast_places = convert_to_list(cast_places)
    
    # convert string to list (eg. "[1,2,3]" to [1,2,3])
    cast_ids = convert_to_list_num(cast_ids)
    rec_vote = convert_to_list_num(rec_vote)
    rec_year = convert_to_list_num(rec_year)
    rec_ids = convert_to_list_num(rec_ids)
    
    # rendering the string to python string
    for i in range(len(cast_bios)):
        cast_bios[i] = cast_bios[i].replace(r'\n', '\n').replace(r'\"','\"')

    for i in range(len(cast_chars)):
        cast_chars[i] = cast_chars[i].replace(r'\n', '\n').replace(r'\"','\"') 
    
    # 将多个列表组合为一个字典，这个字典可以传递给html文件，这样可以轻松处理信息，并且信息的顺序将得到保留
    movie_cards = {rec_posters[i]: [rec_movies[i],rec_movies_org[i],rec_vote[i],rec_year[i],rec_ids[i]] for i in range(len(rec_posters))}

    casts = {cast_names[i]:[cast_ids[i], cast_chars[i], cast_profiles[i]] for i in range(len(cast_profiles))}

    cast_details = {cast_names[i]:[cast_ids[i], cast_profiles[i], cast_bdays[i], cast_places[i], cast_bios[i]] for i in range(len(cast_places))}

    if(imdb_id != ""):
        # 从IMDB网站进行网络爬取以获取用户评论
        sauce = urllib.request.urlopen('https://www.imdb.com/title/{}/reviews?ref_=tt_ov_rt'.format(imdb_id)).read()
        soup = bs.BeautifulSoup(sauce,'lxml')
        soup_result = soup.find_all("div",{"class":"text show-more__control"})

        reviews_list = [] # 评论列表
        reviews_status = [] # 评论状态列表（好或坏）
        for reviews in soup_result:
            if reviews.string:
                reviews_list.append(reviews.string)
                # 将评论传递给我们的模型
                # 将评论转换为numpy数组
                movie_review_list = np.array([reviews.string])
                # 使用向量化器将评论转换为向量
                movie_vector = vectorizer.transform(movie_review_list)
                # 使用分类器预测评论的情感
                pred = clf.predict(movie_vector)
                # 根据预测结果，将评论的情感状态添加到列表中
                reviews_status.append('Positive' if pred else 'Negative')

        # 获取当前日期
        movie_rel_date = ""
        curr_date = ""
        if(rel_date):
            today = str(date.today())
            curr_date = datetime.strptime(today,'%Y-%m-%d')
            movie_rel_date = datetime.strptime(rel_date, '%Y-%m-%d')

        # 将评论和评论状态组合成一个字典
        movie_reviews = {reviews_list[i]: reviews_status[i] for i in range(len(reviews_list))}
        # 调用翻译函数翻译字典
        movie_reviews = {translate_text(key): value for key, value in movie_reviews.items()}
             
        # passing all the data to the html file
        return render_template('recommend.html',title=title,poster=poster,overview=overview,vote_average=vote_average,
            vote_count=vote_count,release_date=release_date,movie_rel_date=movie_rel_date,curr_date=curr_date,runtime=runtime,status=status,genres=genres,movie_cards=movie_cards,reviews=movie_reviews,casts=casts,cast_details=cast_details)

    else:
        return render_template('recommend.html',title=title,poster=poster,overview=overview,vote_average=vote_average,
            vote_count=vote_count,release_date=release_date,movie_rel_date="",curr_date="",runtime=runtime,status=status,genres=genres,movie_cards=movie_cards,reviews="",casts=casts,cast_details=cast_details)


if __name__ == '__main__':
    app.run(debug=True)