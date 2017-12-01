import re
import os
import sys
import telebot
import time
from telebot import types
import configparser
import urllib.request, json
from bs4 import BeautifulSoup
import requests

from chatterbot import ChatBot



# Connectando ao API  Telegram

curPath = os.path.dirname(os.path.realpath(sys.argv[0]));
config = configparser.ConfigParser()

#arquivo .ini com o seguinte formato:
#[DEFAULT]
#token=<token>
#support_chat_id=<bot id> 

config.read_file(open(curPath+'\config_hal.ini'))
bot = telebot.TeleBot(token=config['DEFAULT']['token'])



    

#uriEncoder
def uriEncode(t):
    from urllib.parse import quote
    return quote(t)

#getJSON
def getJSON(req):
    with urllib.request.urlopen(req) as url:
        return json.loads(url.read().decode())

def castHeaderCorrection(s):
    s = re.sub(r'[\ \n]{2,}', '',s).replace('\n','')
    return s.replace("Director:","<b>Director: </b>").replace("Stars:","\n\n<b>Stars: </b>").replace("|","").replace(",",", ").replace("Directors:","<b>Directors: </b>")
    
#youtubeLinkFormatter
def youtubeLink(l):
    return l.split('?')[0].replace('embed/','watch?v=').replace('//www.','')

#Global Vars
sResultsList = []
randomMoviesRatingScores = [9.5,9,8.5,8,7.5,7,6.5,6]
randomMoviesGenresList = {'action','adventure','animation','biography','comedy','comedy','documentary','drama','family','fantasy','film_noir','history','horror','music','musical','mystery','romance','sci_fi','short', 'sport','thriller','war','western'}
commonPhrases = {'noMovieFound':'No movies found, please try again!',
                 'mayYoulike':'Maybe you\'ll like this one',
                 'formatError':'Please use the following format:',
                 'search_result_desc':'Here\'s what you looking for:'}
botStartText = """
Welcome to the Movies Search Bot!

Here you can with just a few commands search for specific movies,
or get an suggestion to your movie night!
"""
commandsList = """
You can control me by sending these commands:

<b>Suggestions:</b>
/suggestMe - Returns a suggestion based on director, cast, rating, genre or any movie without filters. (Choice by buttons)

<b>Suggestions sub-commands:</b>
/suggestByGenre - Returns a suggestion based on genre (comedy, animation, drama, etc.)
/suggestByRating - Returns a suggestion based on IMDB Score
/suggestByDirector - Returns a suggestion based on a director
/suggestByCast - Returns a suggestion based on a cast member
/suggestAnything - Returns a suggestion without specific filters

<b>Suggestions | Specific commands:</b>

<b>Suggestions by Genre:</b>
/sbg <b>genre</b> - Returns a suggestion based on genre\n(Ex: /sbg animation)

<b>Suggestions by Cast Member:</b>
/sbc <b>cast member name</b> - Returns a suggestion based on a cast member\n(Ex: /sbc Marlon Brando)

<b>Suggestions by Director:</b>
/sbd <b>director\'s name</b> - Returns a suggestion based on a director\n(Ex: /sbd: Stanley Kubrick)

<b>Suggestions by IMDB Score:</b>
/sbr <b>IDMB Score (0-10)</b> - Returns a suggestion based on the score\n(Ex: /sbr 6 - will return a movie rated in 6 or above)

You can also search for specific movies:

<b>Search:</b>
To do so just type <b>@MoviesSearch_bot</b> <i>your movie name</i> and a list with 10 results will appear
"""

#getRandomMovieBy
#GENERO/(DIRETOR/ATOR)/NUMERO DE USUARIOS QUE AVALIARAM NO IMDB/PONTUACAO NO IMDB/(PERIODO DE LANCAMENTO)/PESQUISA FILTRADA OU NÃO
def getRandomMovieBy(genre='',person='',imdbusers=0,imdbrating=0,yearStart=0,yearEnd=0,filtered=0):
    url = 'http://www.suggestmemovie.com'
    if(filtered == 1):
        #retorna filme aleatorio baseado em filtros (SUGERIR BASEADO EM FILTROS ESPECIFICOS)
        values = {'mood_change' : 1,
            'mood_category' : genre,
            'mood_imdb_users' : imdbusers,
            'mood_year1': yearStart,
            'mood_year2': yearEnd,        
            'mood_imdb_rating' : imdbrating,
            'mood_extra1':person}
        r = requests.post(url, data=values)
        sopa =  BeautifulSoup(r.text,"html.parser")
    else:
        #retorna filme aleatorio sem filtro (SUGERIR QUALQUER FILME)
        page = urllib.request.urlopen(url).read().decode('iso8859')
        sopa = BeautifulSoup(page,"html.parser")
    #PESQUISA RETORNOU RESULTADO
    if(sopa.findAll('h1')):
        
        try:
            title = sopa.findAll('h1')[0].get_text()
            year = re.findall('\s\([^\d]*(\d+)[^\d]*\)', title)[0]
            title = re.sub('\s\([^\d]*(\d+)[^\d]*\)','', title)
        except:
            year = 'N/A'
            title = 'N/A'
        try:
            poster = url+sopa.find('div',{'class':'movie-tell'}).find('img')['src']
        except:
            poster = "https://s-media-cache-ak0.pinimg.com/236x/f3/5a/d9/f35ad9427be01af5955e6a6ce803f5dc--artist-list-top-artists.jpg"
        try:
            rating = sopa.find('div',{'class':'meter-text-movie'}).findAll('span')[0].get_text()
        except:
            rating = "N/A"
        try:
            imdbUrl = sopa.find('div',{'class':'movie-tell'}).findAll('div')[6].find('a')['href']
        except:
            imdbUrl = "http://www.imdb.com"
        try:
            genre = sopa.find('div',{'class':'movie-tell'}).findAll('div')[3].get_text().replace(' ,',', ').split()[1:]
            genre = ' '.join(genre)[:-1]
        except:
            genre = "N/A"
        try:   
            director = sopa.find('div',{'class':'movie-tell'}).findAll('div')[4].find('a').get_text()
        except:
            director = "N/A"
        try:    
            synopsis = sopa.find('div',{'class':'movie-tell'}).find('div',{'class':'content'}).get_text().split()
            synopsis = ' '.join(synopsis)
        except:
            synopsis = "N/A"
        try:    
            cast = sopa.find('div',{'class':'movie-tell'}).findAll('div')[5].get_text().replace(' ,',', ').split()[1:]
            cast = ' '.join(cast)[:-1]
        except:
            cast = "N/A"
        try:
            trailer = sopa.find('div',{'class':'video'}).find('iframe')['src']
        except:
            trailer = ""
        return {'title': title, 'poster': poster, 'director': director, 'synopsis': synopsis,'cast':cast,'trailer':trailer,'year':year,'genre':genre,'rating':rating,'imdbLink':imdbUrl,'result':True}
    else:
        #PESQUISA NÃO RETORNOU RESULTADO
        return {'result': False}

#print(getRandomMovieBy('','',0,0,'','',1))


#Interação inicial
@bot.message_handler(commands=['start'])
def start_cmd(message):
    username = str(message.from_user.first_name)
    bot.reply_to(message, text="Hello "+username+"!"+botStartText+commandsList,parse_mode='HTML')


#AJUDA (CARECE FINALIZAÇÃO)
@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.reply_to(message, "You can control me by sending these commands:\n\n")
    with urllib.request.urlopen(suggestionUrl) as url:
        data = json.loads(url.read().decode())


#MOSTRA O FILME ALEATORIO PARA USUARIO
def randomMovie(bot,message,movie,text):
    markup = types.ReplyKeyboardRemove(selective=False)
    msgBody = text+"\n\n<b>"+movie['title']+" ("+movie['year']+")</b>\n\U00002B50 <b>"+movie['rating']+"</b>/10 on <a style=\"display:none\" href=\""+movie['imdbLink']+"\">IMDB</a>\n\n<b>Genre: </b>"+movie['genre']+"\n\n<b>Director:</b> "+movie['director']+"\n<b>Cast:</b> "+movie['cast']+"\n\n<b>Synopsis:</b> "+movie['synopsis']
    bot.send_message(chat_id=message.chat.id,parse_mode='HTML',text=msgBody,disable_web_page_preview=True,reply_markup=markup)
    bot.send_photo(chat_id=message.chat.id, caption="\""+movie['title']+"\" poster", photo=movie['poster'])
    bot.send_message(chat_id=message.chat.id,parse_mode='HTML',text="<b>Trailer:</b>\n@vid "+youtubeLink(movie['trailer']))


#RECOMENDAÇÕES - MAIN
@bot.message_handler(commands=['suggestMe'])
def suggestMain_cmd(message):
    reply_markup = types.InlineKeyboardMarkup(row_width=2) 
    i1 = types.InlineKeyboardButton(text='Suggestion by Genre',callback_data='sbg')
    i2 = types.InlineKeyboardButton(text='Suggestion by Rating',callback_data='sbr')
    i3 = types.InlineKeyboardButton(text='Suggestion by Director',callback_data='sbd')
    i4 = types.InlineKeyboardButton(text='Suggestion by Cast',callback_data='sbc')
    i5 = types.InlineKeyboardButton(text='Suggest Anything',callback_data='san')
    reply_markup.add(i1, i2, i3, i4, i5)
    bot.send_message(message.chat.id,text='Tell me what kind of suggestions you want:', reply_markup=reply_markup)


#RECOMENDAÇÕES - GENRE
@bot.message_handler(commands=['suggestByGenre'])
def suggestGenre_cmd(message):
    markup = types.ReplyKeyboardRemove(selective=False)
    markup = types.ReplyKeyboardMarkup(row_width=4)
    for x in randomMoviesGenresList:
        markup.add(types.KeyboardButton('/sbg '+x.replace('_','-')))    
    bot.send_message(message.chat.id, "Type the command /sbc followed by the genre based suggestions do you want:", reply_markup=markup)

@bot.message_handler(commands=['sbg'])
def suggestGenre_select(message):
    try:
        genre = re.split("/sbg ", message.text)[1]
        for x in [' ','-']:
            genre = genre.replace(x,"_")
        if genre in randomMoviesGenresList:
            movie = getRandomMovieBy(genre,'',0,0,'','',1)
            if(movie['result'] == True):
                randomMovie(bot,message,movie,commonPhrases['mayYoulike']+' from <b>'+genre.replace('_','-')+'</b> movies:')
            else:
                bot.send_message(message.chat.id, commonPhrases['noMovieFound'])
        else:
            bot.send_message(chat_id=message.chat.id, parse_mode='HTML', text="<b>"+genre+"</b> is not a valid genre!")
    except IndexError:
            bot.send_message(message.chat.id, commonPhrases['formatError']+"\n/sbg genre")
		
   
#RECOMENDAÇÕES - DIRECTOR
@bot.message_handler(commands=['suggestByDirector'])
def suggestDirector_cmd(message):
    markup = types.ForceReply(selective=False)
    bot.send_message(chat_id=message.chat.id, parse_mode='HTML',text="Type the command /sbd followed by the director that you've in mind:\nEx: <b>/sbd Stanley Kubrick</b>", reply_markup=markup)

@bot.message_handler(commands=['sbd'])
def suggestDirector_select(message):
    markup = types.ReplyKeyboardRemove(selective=False)
    try:
        director = re.split("/sbd ", message.text)[1]
        movie = getRandomMovieBy('',director,0,0,'','',1)
        if(movie['result'] == True):
            randomMovie(bot,message,movie,commonPhrases['mayYoulike']+', directed by <b>'+director.title()+'</b>:')
        else:
            bot.send_message(message.chat.id, commonPhrases['noMovieFound'])
    except IndexError:
        bot.send_message(message.chat.id, commonPhrases['formatError']+"\n/sbd director name")

#RECOMENDAÇÕES - CAST
@bot.message_handler(commands=['suggestByCast'])
def suggestCast_cmd(message):
    print(message)
    markup = types.ForceReply(selective=False)
    bot.send_message(chat_id=message.chat.id, parse_mode='HTML', text="Type the command /sbc followed by the actor/actress you've in mind:\nEx: <b>/sbc Marlon Brando</b>", reply_markup=markup)

@bot.message_handler(commands=['sbc'])
def suggestCast_select(message):
    markup = types.ReplyKeyboardRemove(selective=False)
    try:
        cast = re.split("/sbc ", message.text)[1]
        movie = getRandomMovieBy('',cast,0,0,'','',1)
        if(movie['result'] == True):
            randomMovie(bot,message,movie, commonPhrases['mayYoulike']+', with <b>'+cast.title()+'</b> on the cast:')
        else:
            bot.send_message(message.chat.id, commonPhrases['noMovieFound'])
    except IndexError:
        bot.send_message(message.chat.id, commonPhrases['formatError']+"\n/sbc cast member name")

#RECOMENDAÇÕES - RATING   
@bot.message_handler(commands=['suggestByRating'])
def suggestRating_cmd(message):
    markup = types.ForceReply(selective=False)
    markup = types.InlineKeyboardMarkup(row_width=4)
    btns = []
    for x in randomMoviesRatingScores:
        btns.append(types.InlineKeyboardButton(text=str(x),callback_data="/sbr "+str(x)))  
    markup.add(btns[0],btns[1],btns[2],btns[3],btns[4],btns[5],btns[6],btns[7])
    bot.send_message(chat_id=message.chat.id,parse_mode='HTML', text="Tell me what rating note based suggestions do you want:\nYou can use one of these buttons or type: /sbr (score number)\nEx: <b>/sbr 6</b>\n\nObs: The result will be any movie with score above the given number", reply_markup=markup)

@bot.message_handler(commands=['sbr'])
def suggestRating_select(message,rating=''):
    markup = types.ReplyKeyboardRemove(selective=False)
    try:
        if(rating == ''):
            rating = re.split("/sbr ", message.text)[1]
        movie = getRandomMovieBy('','',0,(float(rating)*10),'','',1)
        if(movie['result'] == True):
            randomMovie(bot,message,movie,commonPhrases['mayYoulike']+', rated over <b>'+rating+'</b> on IMDB:')
        else:
            bot.send_message(message.chat.id, commonPhrases['noMovieFound'])
    except IndexError:
        bot.send_message(message.chat.id, commonPhrases['formatError']+"\n/sbr (0-10)")

#RECOMENDAÇÕES - ANYTHING
@bot.message_handler(commands=['suggestAnything'])
def suggestAnything_cmd(message):
    markup = types.ReplyKeyboardRemove(selective=False)
    movie = getRandomMovieBy('','',0,0,'','',0)
    if(movie['result'] == True):
        randomMovie(bot,message,movie, commonPhrases['mayYoulike'])
    else:
        bot.send_message(message.chat.id, commonPhrases['noMovieFound'])

#BUTTONS HANDLER (GERENCIA CHAMADAS DE BOTOES INLINE)
@bot.callback_query_handler(func=lambda call: True)
def inlineCallbackHandler(call):
    markup = types.ReplyKeyboardRemove(selective=False)
    if(call.data == 'sbg'):
        suggestGenre_cmd(call.message)
    elif(call.data == 'sbr'):
        suggestRating_cmd(call.message)        
    elif(call.data == 'sbd'):
        suggestDirector_cmd(call.message)
    elif(call.data == 'sbc'):
        suggestCast_cmd(call.message)
    elif(call.data == 'san'):
        suggestAnything_cmd(call.message)
    elif(re.match("/sbr", call.data)):
        suggestRating_select(call.message,re.split("/sbr ", call.data)[1])


#PARTE II - BUSCA DE FILMES

#BUSCA TRAILERS NO YOUTUBE ATRAVES DO NOME DO FILME
def getYoutubeTrailer(movie):
    query = urllib.request.quote(movie + " movie trailer")
    url = "https://www.youtube.com/results?search_query=" + query
    response = urllib.request.urlopen(url)
    html = response.read()
    soup = BeautifulSoup(html,'html.parser')
    return 'https://www.youtube.com' + soup.find(attrs={'class':'yt-uix-tile-link'})['href']

#FAZ BUSCA NO IMDB POR FILMES (EXIBE ATÉ 10 RESULTADOS)
def movieSearch(search=''):
    global sResultsList
    del sResultsList
    sResultsList = [] #GLOBAL RESULTS LIST
    results_list = [] #LOCAL RESULTS LIST
    i = 0
    url = "http://www.imdb.com/search/title?adult=include&title_type=feature,tv_movie,documentary,short&title="+search
    sopa = BeautifulSoup(urllib.request.urlopen(url).read().decode('utf-8'),"lxml").find('div',{'class':'lister-list'})

    try:
        html = sopa.findAll('div',{'class':'lister-item'})    
        for x in html:
            try:
                title = x.find('h3',{'class':'lister-item-header'}).find('a').get_text()
            except:
                title = ""
            try:
                url = "http://imdb.com"+x.find('h3',{'class':'lister-item-header'}).find('a')['href']
            except:
                url = "http://imdb.com"
            try:
                year = x.find('h3',{'class':'lister-item-header'}).find('span',{'class':'lister-item-year'}).get_text()
            except:
                year = ""    
            try:
                rating = x.find('div',{'class':'ratings-bar'}).find('div',{'class':'ratings-imdb-rating'}).find('strong').get_text()
            except:
                rating = "?"
            try:
                genre = x.find('p',{'class':'text-muted'}).find('span',{'class':'genre'}).get_text()
            except:
                genre = ""
            try:
                runtime = x.find('p',{'class':'text-muted'}).find('span',{'class':'runtime'}).get_text()
            except:
                runtime = ""
            try:
                summary = x.findAll('p',{'class':'text-muted'})[1].get_text()
            except:
                summary = ""    
            try:
                castAndDirectors = x.findAll('p')[2].get_text()
            except:
                castAndDirectors = ""
            try:
                poster = x.find('div',{'class':'lister-item-image'}).find('a').find('img')['loadlate']
            except:
                poster = ""
            sResultsList.append({'title': title, 'runtime' : runtime,'poster': poster, 'castAndDirectors': castAndDirectors, 'summary': summary,'year':year,'genre':genre,'rating':rating, 'imdbUrl':url}) 
            results_list.append(types.InlineQueryResultArticle(str(i), title, types.InputTextMessageContent(search), None, url, True,  summary, poster,40, 60))
            if i == 9:
                break;
            i= i+1
    except:
        results_list.append(types.InlineQueryResultArticle("666", "Could not find results", types.InputTextMessageContent('Check if the title you searched is correct!'), None, url, True,  "", "http://ia.media-imdb.com/images/G/01/imdb/images/nopicture/large/film-184890147._CB522736516_.png",40, 40))
    i = 0    
    return results_list

#INICIA BUSCA SEMPRE QUE O USUARIO CHAMAR O BOT "@MoviesSearch_bot godfather"
@bot.inline_handler(lambda query: query.query)
def search_cmd(message):
    print(message)
    resultsList = movieSearch(message.query)
    while resultsList == None:
        time.sleep(20)
    bot.answer_inline_query(message.id, results=resultsList, cache_time=1)
    
@bot.chosen_inline_handler(func=lambda chosen_inline_result: True)
def inline_chosen(res):
    global sResultsList
    id = int(res.result_id)
    print(sResultsList[int(res.result_id)])
    markup = types.ReplyKeyboardRemove(selective=False)
    msgBody = commonPhrases['search_result_desc']+"\n\n<b>"+sResultsList[id]['title']+" "+sResultsList[id]['year']+"</b> | "+sResultsList[id]['runtime']+"\n\U00002B50 <b>"+sResultsList[id]['rating']+"</b>/10 on <a style=\"display:none\" href=\""+sResultsList[id]['imdbUrl']+"\">IMDB</a>\n\n<b>Genre: </b>"+sResultsList[id]['genre']+"\n\n"+castHeaderCorrection(sResultsList[id]['castAndDirectors'])+"\n\n<b>Summary:</b> "+sResultsList[id]['summary']
    bot.send_message(chat_id=res.from_user.id,parse_mode='HTML',text=msgBody,disable_web_page_preview=True,reply_markup=markup)
    bot.send_photo(chat_id=res.from_user.id, caption="\""+sResultsList[id]['title']+"\" poster", photo=sResultsList[id]['poster'])
    bot.send_message(chat_id=res.from_user.id,parse_mode='HTML',text="<b>Trailer:</b>\n@vid "+getYoutubeTrailer(sResultsList[id]['title']))


#CHATTER
chatbot = ChatBot(
    'Hal 9000',
    trainer='chatterbot.trainers.ChatterBotCorpusTrainer'
)

#chatbot.storage.drop()

chatbot.train("chatterbot.corpus.english.conversations")
chatbot.train("chatterbot.corpus.english.humor")
chatbot.train("chatterbot.corpus.english.movies")
chatbot.train("chatterbot.corpus.english.movies_suggestions")

@bot.message_handler(func=lambda m: True)
def get_conversation(msg):
    res = chatbot.get_response(msg.text)
    bot.send_message(chat_id=msg.chat.id,parse_mode='HTML',text=res)

   
#Roda Bot
bot.polling()
