from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
import re
import random

#Nossos imports instalados
#    --> NOVAS VERS�ES TEM QUE COMENTAR A LINHA DE STREAMING NO ARQUIVO __init__.py DO TWEEPY PQ ENTRA EM CONFLITO <--
import tweepy#pip install tweepy
'''from googletrans import Translator'''#pip install googletrans
from yandex_translate import YandexTranslate#pip install yandex.translate
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer#pip install vaderSentiment
from mapbox import Geocoder#pip install mapbox

#OUTRAS OPCOES PARA TRADUZIR
#pip install gp-python-client	>> gp-python-client 1.0.0
#pip install mstranslate			>> Python-Microsoft-Translate-API


#A classe que recebe o texto do tweet, como tambem o valor de sua polarizacao.
#Usada no momento na pagina de polarizacao
#Vale notar que ela nao funcionara com o retorno da API no mesmo template. Ou use a API em si, ou mande o retorno dela pra essa classe
class Tweet():
	seq = 0
	objects = []

	def __init__(self):
		self.id = None
		self.texto = None
		self.textotrad = None
		self.textotradbr = None
		self.pol = None
		self.profile_image_url = None
		self.name = None
		self.url = None
		self.screen_name = None
		self.iso_language_code = None
		self.followers_count = None
		self.friends_count = None
		self.favourites_count = None
		self.verified = None
		self.extras = None
		self.links = None

	def setAll(self, texto, textotrad, textotradbr, pol, profile_image_url, name, url, screen_name,
	iso_language_code, followers_count, friends_count, favourites_count, verified, extras, links):
		self.id = None
		self.texto = texto
		self.textotrad = textotrad
		self.textotradbr = textotradbr
		self.pol = pol
		self.profile_image_url = profile_image_url
		self.name = name
		self.url = url
		self.screen_name = screen_name
		self.iso_language_code = iso_language_code
		self.followers_count = followers_count
		self.friends_count = friends_count
		self.favourites_count = favourites_count
		self.verified = verified
		self.extras = extras
		self.links = links

	def save(self):
		self.__class__.seq+=1
		self.id = self.__class__.seq
		self.__class__.objects.append(self)

	def __str__(self):
		return self.texto

	@classmethod
	def remover(cls):
		cls.objects.clear()

	@classmethod
	def all(cls):
		return cls.objects

#Setup da API com as chaves e secrets
def setup():
	CONSUMER_KEY = 'WL7P4M3mVgzeCofWLUqAiUvoG'
	CONSUMER_SECRET = 'oZIqGzXbo7Oi3H2e1fJz47xRFQ6jEH6f2SZfhgvqwOejZoumWg'

	ACCESS_TOKEN = '431994221-PYlnHDXb08zHZemgGSA79L9Tz2VPCoxmaDUAmXBh'
	ACCESS_SECRET = 'h7cz3tmcw0FBuVhamWxm4gp8RP2cSAeRuuYtSv9SwaN5h'

	auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
	auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)

	api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

	if (not api):
		print ("ERRO! API nao autenticada")
		sys.exit(-1)
	else:
		return api

#A pesquisa mais basica, separada caso o user escolha pesquisa livre ou direcionada por usuario
def collect(request):
	try:
		#Busca das informacoes de search.html
		op = request.POST.get('op')			#Opcao do usuario
		search = request.POST.get('search')	#Texto do usuario
		#translator = Translator()	USAR COM GOOGLETRANS

		#Setup do collect
		Tweet.remover()				#Limpar a classe Tweet
		api = setup()				#Deixar a API pronta

		if(op == "1"):	#Opcao de analise bruta

			#Setar as variaveis
			count = 40 	#Quantos tweets vai pegar
			past = 0	#Quantos tweets nao foram polarizados
			posTot = 0	#Total positivo
			neuTot = 0	#Total negativo
			negTot = 0	#Total neutro
			comTot = 0	#Total geral

			#Filtro e busca
			filter = " -filter:retweets"		#Nao podemos aceitar retweets pois eles sujam os dados com repeticao de um mesmo tweet
			newsearch = "".join((search,filter))#Junta a pesquisa do usuario com o filtro
			tweets = tweepy.Cursor(api.search, q=newsearch, count=count, tweet_mode="extended").items(count)#Faz a coleta do tweepy

			count = 0	#Zerar para caso tenha menos de 20 tweets

			#Iterar pelos tweets
			for tweet in tweets:
				count += 1	#Cada tweet adiciona um

				#Setando a classe
				analysis = Tweet()

				#Retirar os emojis do texto
				texto = tira_emoji(tweet.full_text)

				#Esse aqui eh o yandex, funciona mas fico duvidoso por precisar dar str() --> USAR DE BACKUP
				translate = YandexTranslate('trnsl.1.1.20180809T195441Z.ee8cb1461b193a37.718666e4f14fa0a45cf6e490af90863be18ab677')

				lang = translate.detect(texto)
				textoen = translate.translate(texto, 'en')
				textobr = translate.translate(texto, 'pt')

				textotraden = str(textoen.get('text'))
				textotradbr = str(textobr.get('text'))
				extras = str(textoen.get('code'))

				'''
				#Para a traducao EN
				translationsen = translator.translate(['Erro na traducao EN', texto], dest='en')
				for translationen in translationsen:
					textotraden = translationen.text
					lang = translationen.src
				#Para a traducao BR
				translationsbr = translator.translate(['Error at translating BR', texto], dest='pt')
				for translationbr in translationsbr:
					textotradbr = translationbr.text
					extras = translationbr.extra_data
				'''

				#Polarizacao
				pol = unique_sentiment_score(textotraden)

				#Dar o setALL na classe Tweet
				analysis.setAll( texto, textotraden, textotradbr, pol, tweet.user.profile_image_url_https, tweet.user.name,
				tweet.user.url, tweet.user.screen_name, lang, tweet.user.followers_count, tweet.user.friends_count, tweet.user.favourites_count,
				tweet.user.verified, extras, links="")

				#Salvar os dados do setAll para ler no HTML
				analysis.save()

				#Caso a polarizacao falhe e neutralidade de 1
				if pol['neu'] == 1:
					pol['neu'] = 0	#Impede que a neutralidade suje os dados
					count -=1		#Retira do total de tweets
					past +=1		#Adiciona nos tweets sem polaridade

				#Adicionando os valores para os graficos
				posTot += pol['pos']
				negTot += pol['neg']
				neuTot += pol['neu']
				comTot += pol['compound']

			#Media dos valores totais para os graficos
			posTot = float(posTot/count)
			negTot = float(negTot/count)
			neuTot = float(neuTot/count)
			comTot = float(comTot/count)

			#Contexto de retorno para o HTML
			context = {
				'posTot' : posTot,
				'negTot' : negTot,
				'neuTot' : neuTot,
				'comTot' : comTot,
				'count' : count,
				'past' : past,
				'analysis': analysis.all(),
				'query': search,}
		elif(op == "2"):	#Se voce escolheu pesquisa livre

			#Filtro e busca
			filter = " -filter:retweets"		#Nao podemos aceitar retweets pois eles sujam os dados com repeticao de um mesmo tweet
			newsearch = "".join((search,filter))#Junta a pesquisa do usuario com o filtro
			tweets = tweepy.Cursor(api.search, q=newsearch, count=40, tweet_mode="extended").items(40)#Faz a coleta do tweepy


			#se não houve resultado, manda para nothing.html AMANDA PAROU AQUI AAAAAAAA
			#if not tweets:
				#return render(request, 'tcc/nothing.html')

			#Contexto de retorno para o HTML
			context = {
				'tweets': tweets,
				'query': search,}

		else:	#Se voce escolheu pesquisa direcionada por usuario

			users = api.search_users(q=search, count=100)#Faz a coleta do tweepy

			#se não houve resultado, manda para nothing.html
			if not users:
				return render(request, 'tcc/nothing.html')

			#Contexto de retorno para o HTML
			context = {
				'users': users,
				'query': search,}

	except ZeroDivisionError:
		return render(request, 'tcc/nothing.html')
	except tweepy.TweepError:
		return render(request, 'tcc/error.html')
	except KeyError:
		return render(request, 'tcc/error.html')
	else:
		return render(request, 'tcc/result_list.html', context)

#Funcao que analiza o texto de um unico tweet
def analyze_tweet(request):
	try:
		#Instanciando o tradutor e a classe
		Tweet.remover()
		#translator = Translator()	USAR COM GOOGLETRANS
		results = Tweet()
		results.remover() #Limpando novamente caso haja sujeira

		#Coleta das informacoes fornecidas pelo HTML
		texto = tira_emoji(request.POST.get('tweet_text'))
		lang = request.POST.get('iso_language_code')

		#Pega os links no texto, caso houver
		links = get_links(texto)

		#Remove os links no texto, caso houver
		texto = del_links(texto)

		#Esse aqui eh o yandex, funciona mas fico duvidoso por precisar dar str() --> USAR DE BACKUP
		translate = YandexTranslate('trnsl.1.1.20180809T195441Z.ee8cb1461b193a37.718666e4f14fa0a45cf6e490af90863be18ab677')

		lang = translate.detect(texto)
		textoen = translate.translate(texto, 'en')
		textobr = translate.translate(texto, 'pt')

		textotraden = str(textoen.get('text'))
		textotradbr = str(textobr.get('text'))
		extras = str(textoen.get('code'))
		'''
		#Para a traducao EN
		translationsen = translator.translate(['Erro na traducao EN', texto], dest='en')
		for translationen in translationsen:
			textotraden = translationen.text
			lang = translationen.src
		#Para a traducao BR
		translationsbr = translator.translate(['Error at translating BR', texto], dest='pt')
		for translationbr in translationsbr:
			textotradbr = translationbr.text
			extras = translationbr.extra_data
		'''

		#Polarizacao do texto traduzido
		pol = unique_sentiment_score(textotraden)

		#Da o setAll na classe usando a informacao do HTML
		results.setAll( texto, textotraden, textotradbr, pol, request.POST.get('profile_img_url'), request.POST.get('name'),
		request.POST.get('url'), request.POST.get('screen_name'), lang,
		request.POST.get('followers_count'), request.POST.get('friends_count'), request.POST.get('favourites_count'),
		request.POST.get('verified'), extras, links)

		#Contexto de retorno para o HTML
		context = {
			'results': results,
			'text':request.POST.get('tweet_text')}

	except KeyError:
		return render(request, 'tcc/error.html')
	else:
		return render(request, 'tcc/tweet_analysis.html', context)

#Funcao que analiza todos os tweets de um usuario
def analyze_user(request):
	try:
		#Setar as variaveis que serap usadas e o count de qntos tweets vai pegar
		count = 40
		past = 0
		posTot = 0
		neuTot = 0
		negTot = 0
		comTot = 0

		#Limpar a classe e instanciar as apis
		Tweet.remover()
		api = setup()
		#translator = Translator()	USAR COM GOOGLETRANS

		#Busca de tweets e instanciamento das ferramentas
		tweets = api.user_timeline(screen_name=request.POST.get('name'), count=count, tweet_mode="extended")

		count = 0	#Zerar para caso tenha menos de 20 tweets

		for tweet in tweets:
			count += 1 #Cada tweet adiciona um

			#Setando a classe para um tweet
			analysis = Tweet()

			#Retirar os emojis do texto pois eles dao crash no app
			full_text_emojiless = tira_emoji(tweet.full_text)

			#Esse aqui eh o yandex, funciona mas fico duvidoso por precisar dar str() --> USAR DE BACKUP
			translate = YandexTranslate('trnsl.1.1.20180809T195441Z.ee8cb1461b193a37.718666e4f14fa0a45cf6e490af90863be18ab677')

			lang = translate.detect(full_text_emojiless)
			textoen = translate.translate(full_text_emojiless, 'en')
			textobr = translate.translate(full_text_emojiless, 'pt')

			textotraden = str(textoen.get('text'))
			textotradbr = str(textobr.get('text'))
			extras = str(textoen.get('code'))

			'''
			#Para a traducao EN
			translationsen = translator.translate(['Erro na traducao EN', full_text_emojiless], dest='en')
			for translationen in translationsen:
				textotraden = translationen.text
				lang = translationen.src
			#Para a traducao BR
			translationsbr = translator.translate(['Error at translating BR', full_text_emojiless], dest='pt')
			for translationbr in translationsbr:
				textotradbr = translationbr.text
				extras = translationbr.extra_data
			'''

			#Para a polarizacao
			pol = unique_sentiment_score(textotraden)

			#Dar o setAll nas informacoes criadas nessa funcao
			analysis.setAll( full_text_emojiless, textotraden, textotradbr, pol, tweet.user.profile_image_url_https, tweet.user.name,
			tweet.user.url, tweet.user.screen_name, lang, tweet.user.followers_count, tweet.user.friends_count, tweet.user.favourites_count,
			tweet.user.verified, extras, links="")

			#Salvar os dados na classe
			analysis.save()

			#Caso a polarizacao falhe e neutralidade de 1
			if pol['neu'] == 1:
				pol['neu'] = 0#Impede que a neutralidade suje os dados
				count -= 1#Retira do total de tweets
				past += 1#Adiciona nos tweets sem polaridade

			#Adicionando os valores para os graficos
			posTot += pol['pos']
			negTot += pol['neg']
			neuTot += pol['neu']
			comTot += pol['compound']

		#Fazer as medias de cada valor geral para os graficos
		posTot = float(posTot/count)
		negTot = float(negTot/count)
		neuTot = float(neuTot/count)
		comTot = float(comTot/count)

		#Contexto de retorno para o HTML
		context = {
			'posTot' : posTot,
			'negTot' : negTot,
			'neuTot' : neuTot,
			'comTot' : comTot,
			'count' : count,
			'past' : past,
			'analysis': analysis.all(),
			'query':request.POST.get('name'),}

	except tweepy.TweepError:
		return render(request, 'tcc/user_protected.html')
	except KeyError:
		return render(request, 'tcc/error.html')
	else:
		return render(request, 'tcc/user_analysis.html', context)

#Informacoes mais profundas sobre um certo usuario, eh preciso do id ou nome desse usuario para essas informacoes
def collect_user(request):
	try:
		api = setup()
		geocoder = Geocoder(access_token="pk.eyJ1IjoibGFtb3R0YSIsImEiOiJjam1hdnJlaTIwcnh1M3Bqb2JzZjc5cnhvIn0.w986x6WriEojUaBUGQtMig")

		user_data = api.get_user(request.POST.get('user_name'))
		user_favourites = api.favorites(id=request.POST.get('user_name'))
		tweets = api.user_timeline(screen_name=request.POST.get('user_name'), count=20, tweet_mode="extended")

		location = user_data.location

		lat = -22.3154
		long = -49.0615

		response = geocoder.forward(location)
		if response:
			features = response.geojson()['features'][0]
			long = features['geometry'].get('coordinates')[0]
			lat = features['geometry'].get('coordinates')[1]

		context = {
			'lat' : lat,
			'long' : long,
			'user_data': user_data,
			'user_favourites': user_favourites,
			'tweets': tweets,
			'query':request.POST.get('user_name'),}

	except tweepy.TweepError:
		return render(request, 'tcc/user_protected.html')
	#except KeyError:
	#	return render(request, 'tcc/error.html')
	else:
		return render(request, 'tcc/user_detail.html', context)

#Coleta os possiveis retweets de um tweet, eh preciso que tenhamos o id do tweet para buscar seus retweets
def collect_retweets(request):
	try:
		api = setup()

		retweets = api.retweets(id=request.POST.get('tweet'), count=99)

		context = {
			'retweets': retweets,
			'query': request.POST.get('tweet'),}

	except KeyError:
		return render(request, 'tcc/error.html')
	else:
		return render(request, 'tcc/retweet_list.html', context)

#Coleta as mais notaveis trends do mundo e atribui-as a seus devidos locais para demonstracao
def collect_multiple_trends(request):
	try:
		api = setup()

		trends = api.trends_available()

		context = {'trends': trends,}

	except KeyError:
		return render(request, 'tcc/error.html')
	else:
		return render(request, 'tcc/trend_list.html', context)

#Coleta informacoes mais especificas sobre uma certa trend, precisa da woeid dessa trend
def collect_trend(request):
	#try:
		api = setup()
		geocoder = Geocoder(access_token="pk.eyJ1IjoibGFtb3R0YSIsImEiOiJjam1hdnJlaTIwcnh1M3Bqb2JzZjc5cnhvIn0.w986x6WriEojUaBUGQtMig")

		trends = api.trends_place(id=request.POST.get('woeid'))

		lat = -22.3154
		long = -49.0615

		#trends[0] eh dicionario, ja que trends[] nao tem um indice [1], o [0] eh o unico que existe
		trendDict = trends[0]
		for key, value in trendDict.items():
			if key == 'locations':
				location = value[0].get('name')
				response = geocoder.forward(location)
				if response:
					features = response.geojson()['features'][0]
					long = features['geometry'].get('coordinates')[0]
					lat = features['geometry'].get('coordinates')[1]
			if key == 'trends':
				trendLista = value

				#Tomar cuidado ao mexer com as variaveis de trend, o retorno da API eh assim...
				#trends =
				#[{												--> Esse eh o {trendDict}
				#	key: 'value'								--> Exemplo do que key e value sao
				#	as_of: 'aaa',
				#	created_at: 'bbb',
				#	locations: [{ name: 'teste', woeid: 1 }],
				#	trends:										--> Esse eh o [trendLista]
				#	[
				#		{name: 'aaa', tweet_volume: 'bbb'},
				#		{name: 'aaa', tweet_volume: 'bbb'},
				#		{name: 'aaa', tweet_volume: 'bbb'}
				#	]
				#}]

		context = {
			'long' : long,
			'lat' : lat,
			'location' : location,
			'dict' : trendDict,
			'trends' : trendLista,
			'query' : request.POST.get('place_name')}

	#except KeyError:
	#	return render(request, 'tcc/error.html')
	#else:
		return render(request, 'tcc/trend_detail.html', context)

#Funcao para analizar uma unica sentenca com VADER
def unique_sentiment_score(sentence):
	analyzer = SentimentIntensityAnalyzer()
	pol = analyzer.polarity_scores(sentence)
	return pol

#Retira os emojis UNICODE do texto dado
def tira_emoji(text):
	emojies = re.compile('[\U00010000-\U0010ffff]', flags=re.UNICODE)
	return emojies.sub(r'', text)

#Retira os links do texto original
def del_links(txt):
	p = re.compile(r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+")
	return p.sub(r'', txt)

#Anota todos os links de um certo texto em -> links
def get_links(txt):
	links = [None]
	p = re.compile(r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+")
	if (p.findall(txt)):
		links = p.findall(txt)
	else:
		links[0] = ""
	return links[0]

#Randomiza uma curiosidade sobre IA
def curiosidade():
	x = random.randint(0,19)
	texts = [
	"Hoje em dia, muitos estabelecimentos dependem de suas resenhas em plataformas da internet, como o Google Maps, o TripAdvisor ou o Facebook, para que sua reputação traga mais clientes. Pois agora existe uma inteligência artificial capaz de escrever avaliações em restaurantes, lanchonetes e outros locais.",
	"A literatura é uma das mais belas artes que o ser humano produz e que atinge muitas pessoas e encanta a maioria delas. Mas e se os robôs começassem a escrever livros por aí? Cansado de esperar pela continuação da série de livros As Crônicas de Gelo e Fogo, de onde saiu a série Game of Thrones, o engenheiro de software Zack Thoutt resolveu desenvolver uma IA para escrever o sexto livro. O resultado é surpreendente!",
	"Edições em vídeo de partidas esportivas são bastante chatas de se fazer e não necessariamente é uma atividade que carregue uma personalidade própria, sendo mais um trabalho mecânico mesmo. Por isso, nada melhor do que colocar um computador com inteligência artificial para realizar a ingrata tarefa, mais especificamente o sistema Watson, da IBM, que tem treinado com partidas de tênis do US Open.",
	"A artista Taryn Southern resolver criar um álbum inteiro usando softwares de inteligência artificial para compor suas músicas após ter brincado de fazer canções dessa maneira e ter gostado do resultado. Chamado I AM AI, seu álbum vai ser o primeiro a ser produzido completamente por IA. Provavelmente, o pioneiro de muitos.",
	"Não é uma tarefa simples reconhecer estilos de desenho, pintura, escolas artísticas e outras características em obras de arte. Porém, um software de inteligência artificial consegue reconhecer – com uma precisão impressionante – estilos de tatuagem, analisando apenas uma imagem da obra. Ele vai dizer com porcentagens de certeza se a tattoo é do tipo aquarela, blackwork, oldschool entre outras.",
	"A Amazon pode, em algum tempo, tomar o lugar das grandes marcas de moda com sua tecnologia de inteligência artificial chamada Generative Adversarial Network (Rede Adversária Generativa em português), que é capaz de desenhar objetos fashion apenas observando amostras de um estilo específico, buscando as próximas tendências da moda.",
	"O reconhecimento de voz já é uma tecnologia bastante antiga, o que não significa que ela ainda não precisasse melhorar bastante para funcionar com maior precisão. Aparentemente, chegamos enfim a um ponto onde esse recurso consegue ser igual ou melhor do que a identificação que nós, seres humanos, fazemos de palavras faladas – pelo menos de maneira literal",
	"Ok, essa é um pouco assustadora, mas o recurso está sendo desenvolvido pela Silver Logic Labs e consegue desvendar se alguém está ou não mentindo apenas olhando para a imagem de seu rosto e analisando características que indicam o estado emocional da pessoa. Se você pensou em algo parecido com o filme Minority Report ou similar, você não está tão errado assim.",
	"Uma equipe da Microsoft Research tem trabalhado no desenvolvimento de um sistema de inteligência artificial que é capaz de manter planadores o máximo de tempo possível no ar, analisando as correntes de ar para que a aeronave sempre tenha aquele ventinho providencial para fazê-lo voar sem gastar combustível desnecessariamente. Aliando isso à produção de energia solar ou eólica, esses aviões poderiam ficar planando no ar quase que para sempre.",
	"Pesquisadores de duas universidades chinesas e duas norte-americanas criaram um sistema que usa inteligência artificial para gerar desenhos no melhor estilo mangá sem nenhuma ajuda humana. Usando uma interface simples que permite a definição de certos traços básicos, a plataforma cria personagens únicos de desenho japonês com um alto nível de perfeição.",
	"O sistema de monitoramento de sono criado pelo Instituto de Tecnologia de Massachusetts (MIT) identifica as ondas de rádio que uma pessoa emite durante o sono e é capaz de saber se ela está sonhando ou não de acordo com as atividades cerebrais. A ideia é tratar de diversas doenças do sono que podem acometer o ser humano, mas não deixa de ser um pouco assustador saber que tem uma IA praticamente lendo a sua mente enquanto você dorme.",
	"Com o curioso nome de DeepLoco, o programa de computador criado nos Estados Unidos por uma equipe da Universidade da Colúmbia Britânica é capaz de desenvolver habilidades por conta própria e, se mostrando um grande fã do esporte bretão, ele aprendeu sozinho a jogar futebol (na verdade, conduzir uma bola, o que já é melhor do que muitos jogadores por aí) e correr.",
	"A inteligência artificial do Facebook deixou seus desenvolvedores um pouco preocupados após ter criado uma linguagem própria para se comunicar de uma maneira que considerou mais prática do que conforme foi programada. Driblando alguns obstáculos do idioma que deveria usar, o sistema acabou sendo desativado pela empresa.",
	"Um acontecimento que já ficou bem conhecido na internet foi o fato da inteligência artificial da Google ter começado a sonhar e, mais interessante ainda, foram as imagens bizarras geradas nesses sonhos digitais. A plataforma pegava conceitos prontos fornecidos a ela e geravam essas imagens a partir dessas informações, criando cenários dignos de artistas abstratos ou de pesadelos assustadores.",
	"Criado pelo programador Joshua Browder, o bot DoNotPay usa inteligência artificial para servir como advogado para as pessoas. Na verdade, o chatbot tira dúvidas sobre direito e processos e consegue ajudar seus usuários a compreender melhor o funcionamento das leis. Especializado em legislação de trânsito, o DoNotPay já venceu mais 160 mil contestações de multas por estacionamento proibido.",
	"Uma inteligência artificial no comando de aviões de combate não apenas foi capaz de manejar as aeronaves com maestria como também conseguiu superar todos os pilotos humanos em voos de teste. O sistema de IA, chamado ALPHA, comandou caças virtuais em simuladores de última geração, os mesmos usados no treinamento de pilotos da aeronáutica norte-americana, e venceu a disputa contra oficiais experientes mesmo com desvantagens colocadas pelos programadores. ",
	"O melhor centro para análise social do Twitter ! (Shhh! Não conte que somos um dos únicos)",
	"Tem alguma ideia que possa nos ajudar? Alguma dúvida que podemos sanar? Envie uma mensagem/pergunta pela nossa página de FAQ no site da empresa que prometemos que será levada em consideração o mais rápido possível.",
	"A Shift foi criada em homenagem ao seu teclado.",
	"Temos uma surpresa na URL 200.145.153.163/shift/jooj"]
	return texts[x]

#A pagina de erro caso precise mostrar manualmente
def error(request):
	return render(request, 'tcc/error.html')

#O 'index' do projeto, renderiza a pagina search para o usuario pesquisar a vontade
def search(request):
	return render(request, 'tcc/search.html')

#Erro ao tentar acessar user_detail de conta privada
def user_protected(request):
	return render(request, 'tcc/user_protected.html')

#Página "Sem resultados"
def nothing(request):
	return render(request, 'tcc/nothing.html')

#Carregar a pagina USUARIO, mostra a barra e redireciona
def loading_user(request):
	try:
		texto = curiosidade()
		name = request.POST.get('name')
		context = {
			'name': name,
			'curiosidade': texto,}

	except tweepy.TweepError:
		return render(request, 'tcc/error.html')
	except KeyError:
		return render(request, 'tcc/error.html')
	else:
		return render(request, 'tcc/loading_user.html', context)

#Carregar a pagina RESULTADO, mostra a barra e redireciona
def loading_results(request):
	try:
		texto = curiosidade()
		search = request.POST.get('search')
		op = request.POST.get('op')
		context = {
			'search': search,
			'op': op,
			'curiosidade': texto,}

	except tweepy.TweepError:
		return render(request, 'tcc/error.html')
	except KeyError:
		return render(request, 'tcc/error.html')
	else:
		return render(request, 'tcc/loading_results.html', context)