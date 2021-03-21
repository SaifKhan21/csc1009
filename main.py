import PySimpleGUI as sg
import tweepy
import requests
import nltk
import matplotlib
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.probability import FreqDist
import string
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from bs4 import BeautifulSoup
import requests
import datetime


def draw_figure(canvas, figure): #To plot the Bar Graph
    ''' Plots the graph onto the canvas of the layout
        ...
    Args:
        canvas : window[KEY].TKCANVAS
            Points to which canvas is the graph to be plotted on
        figure : variable
            The graph that you want to plot onto the canvas
    '''
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg

def delete_fig_photo(fig_photo): #To erase all Bar Graph initialised
    ''' Erases the graphs from the canvas of the layout to allow new graphs to be plot
        ...
        Args:
            fig_photo : variable
                The variable which contains the plotted graph
    '''
    fig_photo.get_tk_widget().forget()
    plt.close('all')

#Main Code'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

access_token = '69234906-YzksEPRONOs0DAvbUlKpG6eyge5WavTNjBJUaT4nY' #Access and consumer token for Tweepy access
access_token_secret = 'je3cum6bPnxDHdYecYaRitx2JIBNutwO1NPL6yw3VE8lI'
consumer_key = 'pvJol71VQghupjm4WPZjunDnD'
consumer_secret = 'biQwOhz8uPcsZ3hj3cCDrhKAcn7pnYSwAHmcqlRjKXux0OFzXY'

#Layout of the GUI
''' Defines what is to be displayed on the window of the GUI'''
layout1 = [[sg.DropDown(["M1", "Singtel", "Starhub","MyRepublic","WhizComms","ViewQwest"],enable_events=True, default_value="M1", key="-drop-")],
           [sg.Canvas(key='-CANVAS-'), sg.Column([[sg.Text("Pricelist",font=["ariel",20])],[sg.Multiline(size=(45, 27),key ='-ML1-')]])],
           [sg.Column([[sg.Text("Average Rating: ",font=["ariel",20]), sg.Text("0.00", key="-OUT-",font=["ariel",20])],
                       [sg.Text("Most Recent Reviews",font=["ariel",20])],[sg.Multiline(size=(90, 27),key ='-ML2-')]]),
            sg.Column([[sg.Text("Outage Information",font=["ariel",20])],[sg.Multiline(size=(45, 27),key ='-ML3-')]])]
           ]
#Pop out Window definition
''' Defines the size of the window of the GUI, its title and the layout it uses'''
window = sg.Window('ISP Review Scraper', layout1, size=(1000, 1000), finalize=True)

class Review:  #Review class for rating and the review comment
    """
    Used to hold both the rating and review text of a single ISP review

    '''

    Attributes
    ----------
    rating : int
        The rating the review gave to the ISP out of 5
    comment : str
        The review text itself
    """
    def __init__(self, rating, comment):
        """
        Parameters
        ----------
        rating : int
            The rating the review gave to the ISP out of 5
        comment : str
            The review text itself
        """
        self.rating = rating
        self.comment = comment

class Plan: #Plan class for Price list information
    """
    Used to hold the details of a single plan the ISP offers

    '''

    Attributes
    ----------
    plan : str
        The name of the plan
    length : str
        The length of the plan, how long the plan lasts for
    price : str
        The price of the plan
    """
    def __init__(self, plan, length, price):
        """
        Parameters
        ----------
        plan : str
            The name of the plan
        length : str
            The length of the plan, how long the plan lasts for
        price : str
            The price of the plan
        """
        self.plan = plan
        self.length = length
        self.price = price

class ISP: #Main class for the other class to inherit from
    """
    A parent class that the ISP brand classes will inherit all its variables and methods from

    '''

    Attributes
    ----------
    phrase : str
        Phrase used to extract the tweets concerning this ISP
    productNo : int
        Product number of the ISP on Seedly, to extract data from the Seedly website
    url_price : str
        URL of the plans the ISP offers on Seedly
    reviews : Review[]
        Array of Review objects to store the reviews the ISP has gotten
    sums : int
        Total sum of ratings, used to calculate average rating later on
    avg : int
        Average rating of ISP
    stop_words : set
        Set of commonly used English words to filter out from the review text
    exclude : str[]
        Manually made array of words to filter out from the review text
    filteredgood : str[]
        Array of positive words that passed through the word filters
    filteredbad : str[]
        Array of negative words that passed through the word filters
    plans : Plan[]
        Array of Plan objects to store the different plans the ISP offers and their details
    downtimeArr : str[]
        Array of dates that the ISP has gone down on
    totalDown : int
        Total number of times the ISP has gone down
    badwords : str[]
        Array of negative attributes that describe the ISP
    goodwords : str[]
        Array of positive attributes that describe the ISP

    Methods
    ------
    getReviewAndRating()
        Method to obtain the Ratings and Review Texts, and analysation for reviews
    getDowntime()
        Method to obtain the outages frequency and its date from tweets on twitter
    getPricing()
        Method to obtain the price lists of the different ISPs from seedly.sg
    """
    def __init__(self, phrase, productNo, url_price):
        """
        Parameters
        ----------
        phrase : str
            Phrase used to extract the tweets concerning this ISP
        productNo : int
            Product number of the ISP on Seedly, to extract data from the Seedly website
        url_price : str
            URL of the plans the ISP offers on Seedly
        """
        self.phrase = phrase
        self.productNo = productNo
        self.url_price = url_price
        self.reviews = []
        self.sums = 0
        self.avg = 0
        self.stop_words = set(stopwords.words("english"))
        self.exclude = ["mobile", "good", "best", "great", "bad", "worst", "new", "much", "please", "last", "sure", "possible", "similar", "previous", "sure", "starhub", "self-unsubscribed"
                        ,"quite", "need", "u", "myrepublic", "able", "right", "due", "old", "current", "assist", "sign"
                        ,"fine", "email", "next", "many"]
        self.filteredgood = []
        self.filteredbad = []
        self.plans = []
        self.downtimeArr = []
        self.totalDown = 0
        self.badwords =[]
        self.goodwords = []

    def getReviewAndRating(self): #Method to obtain the Rating and Review Text, it also does filtering of the review text
        '''
            Method to obtain the Ratings and Review Texts, and analysation for reviews

            Return:
                Plot out the average rating text on the program
                Plot out the most used words on the bar chart
                Plot out the 5 most recent reviews and its ratings

        '''
        for numbers in range(1, 100): #Looping from page 1 to 100 to obtain the rating and review text from the restful api link
            url_review = f"https://api.seedly.sg/api/v4/product/items/{self.productNo}/reviews?page={numbers}&sort%5Bby%5D=updated_at&sort%5Bdir%5D=desc&include_latest_comment=true&per=5"
            raw = requests.get(url_review).json() #putting it in a json structure
            if len(raw["data"]) == 0:
                break
            for review in raw["data"]: #Reading the json data and obtaining the rating and review text from it
                rating = review["rating"]
                comment = review["reviewText"]
                self.reviews.append(Review(rating, comment))
        for review in self.reviews:
            if review.rating >= 4: #filtering the good review ( 4 & 5 rating) and accumulating the words used
                word = word_tokenize(review.comment)
                for j in word:
                    if j not in self.stop_words and j not in string.punctuation and j not in self.exclude:
                        self.filteredgood.append(j)
            elif review.rating <= 2: #filtering the bad review ( 4 & 5 rating) and accumulating the words used
                word = word_tokenize(review.comment)
                for j in word:
                    if j not in self.stop_words and j not in string.punctuation and j not in self.exclude:
                        self.filteredbad.append(j)
        self.goodwords = [f for f in nltk.pos_tag(self.filteredgood) if f[1] == "JJ"]
        self.badwords = [f for f in nltk.pos_tag(self.filteredbad) if f[1] == "JJ"]
        self.goodwords = [row[0] for row in self.goodwords]
        self.badwords = [row[0] for row in self.badwords]
        for review in self.reviews: #Calculating the average rating
            self.sums += review.rating
        self.avg = round(self.sums / len(self.reviews), 2)
        window['-OUT-'].update(self.avg)
        freqgood = FreqDist(self.goodwords)
        freqbad = FreqDist(self.badwords)
        freqgood = freqgood.most_common(5)
        freqbad = freqbad.most_common(5)
        plt.bar([r[0] for r in freqgood], [r[1] for r in freqgood]) #Allocating the values from the filtered good reviews to a bar graph
        plt.bar([r[0] for r in freqbad], [r[1] for r in freqbad]) #Allocating the values from the filtered bad reviews to a bar graph
        plt.xticks(fontsize=6)
        plt.ylabel('Number of times mentioned')
        plt.title('Most Said Words')
        for i in range(5): #printing 5 of the recent reviews of the ISP into the GUI textbox
            window['-ML2-'].print("--------", end='')
            window['-ML2-'].print(i + 1, end='')
            window['-ML2-'].print("--------", end='')
            window['-ML2-'].print("Rating: ", end='')
            window['-ML2-'].print(self.reviews[i].rating, end='')
            window['-ML2-'].print("\n", end='')
            window['-ML2-'].print(self.reviews[i].comment, end='')
            window['-ML2-'].print("\n\n\n\n", end='')


    def getDowntime(self): #Obtaining the downtime frequency and date from a user in twitter
        '''
            Method to obtain the outages frequency and its date from tweets on twitter

            Return:
                Plot out the total number of outages occurs in a year in the multiline textbox
                Plot out the dates in the multiline textbox
        '''
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret) #Authenticating the user to use tweepy
        auth.set_access_token(access_token, access_token_secret)

        api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True) # rate limiting what we are search to allow us to search legally

        tweets = tweepy.Cursor(api.search_full_archive, environment_name='tester', query=self.phrase, #searching from 01/01/2020 00:00:00 am on the ISPs
                               fromDate="202001010000").items(100)

        for tweet in tweets:
            currentDate = datetime.datetime.strptime(str(tweet.created_at), "%Y-%m-%d %H:%M:%S")
            newDate = currentDate.strftime("%d/%m/%Y")
            self.downtimeArr.append(newDate)
            self.totalDown += 1

        window['-ML3-'].print("Total down time for ", end='')
        window['-ML3-'].print(self.phrase.removeprefix('from:downdetectorSG '), end='')
        window['-ML3-'].print(" since 01/01/2020: ", end='')
        window['-ML3-'].print(self.totalDown, end='')
        window['-ML3-'].print("\n", end='')
        window['-ML3-'].print("Dates of down time: ", end='')
        window['-ML3-'].print("\n", end='')
        for i in range(0, self.totalDown):
            window['-ML3-'].print(self.downtimeArr[i], end='')
            window['-ML3-'].print("\n", end='')

    def getPricing(self): #Obtaining the price lists of the different ISPs from seedly.sg
        '''
        Method to obtain the price lists of the different ISPs from seedly.sg

        Returns:
            Plot out the Pricing plans in the multiline textbox
        '''
        isp_html = requests.get(self.url_price).text
        soup = BeautifulSoup(isp_html, 'lxml')
        review = soup.find_all('tr')[1:] #finding all table tag
        for i in review:
            plan = i.find('div').get_text() #finding the first div in tr
            length = i.find('div').find_next("div").get_text() #finding the second div in tr
            price = i.find('div').find_next("div").find_next("div").get_text() #finding the third div in tr
            self.plans.append(Plan(plan, length, price))
        for plan in self.plans: #printing out the plan name, plan length and plan price if they are available to the output
            window['-ML1-'].print(plan.plan,end='')
            window['-ML1-'].print("\n",end='')
            window['-ML1-'].print(plan.length,end='')
            window['-ML1-'].print("\n",end='')
            window['-ML1-'].print(plan.price,end='')
            window['-ML1-'].print("\n\n",end='')

class M1(ISP):
    """
    Class for the M1 ISP, inheriting the attributes and methods from the ISP class

    '''

    Attributes
    ----------
    phrase : str
        Phrase used to extract the tweets concerning this ISP
    productNo : int
        Product number of the ISP on Seedly, to extract data from the Seedly website
    url_price : str
        URL of the plans the ISP offers on Seedly
    reviews : Review[]
        Array of Review objects to store the reviews the ISP has gotten
    sums : int
        Total sum of ratings, used to calculate average rating later on
    avg : int
        Average rating of ISP
    stop_words : set
        Set of commonly used English words to filter out from the review text
    exclude : str[]
        Manually made array of words to filter out from the review text
    filteredgood : str[]
        Array of positive words that passed through the word filters
    filteredbad : str[]
        Array of negative words that passed through the word filters
    plans : Plan[]
        Array of Plan objects to store the different plans the ISP offers and their details
    downtimeArr : str[]
        Array of dates that the ISP has gone down on
    totalDown : int
        Total number of times the ISP has gone down
    badwords : str[]
        Array of negative attributes that describe the ISP
    goodwords : str[]
        Array of positive attributes that describe the ISP

    Methods
    ------
    getReviewAndRating()
        Method to obtain the Ratings and Review Texts, and analysation for reviews
    getDowntime()
        Method to obtain the outages frequency and its date from tweets on twitter
    getPricing()
        Method to obtain the price lists of the different ISPs from seedly.sg
    """
    def __init__(self):
        phrase = "from:downdetectorSG " + self.__class__.__name__
        productNo = 197
        url_price = "https://seedly.sg/reviews/broadband/m1-broadband"
        ''' Call the initialization function of the parent ISP class '''
        super().__init__(phrase, productNo, url_price)

class Singtel(ISP):
    """
    Class for the Singtel ISP, inheriting the attributes and methods from the ISP class

    '''

    Attributes
    ----------
    phrase : str
        Phrase used to extract the tweets concerning this ISP
    productNo : int
        Product number of the ISP on Seedly, to extract data from the Seedly website
    url_price : str
        URL of the plans the ISP offers on Seedly
    reviews : Review[]
        Array of Review objects to store the reviews the ISP has gotten
    sums : int
        Total sum of ratings, used to calculate average rating later on
    avg : int
        Average rating of ISP
    stop_words : set
        Set of commonly used English words to filter out from the review text
    exclude : str[]
        Manually made array of words to filter out from the review text
    filteredgood : str[]
        Array of positive words that passed through the word filters
    filteredbad : str[]
        Array of negative words that passed through the word filters
    plans : Plan[]
        Array of Plan objects to store the different plans the ISP offers and their details
    downtimeArr : str[]
        Array of dates that the ISP has gone down on
    totalDown : int
        Total number of times the ISP has gone down
    badwords : str[]
        Array of negative attributes that describe the ISP
    goodwords : str[]
        Array of positive attributes that describe the ISP

    Methods
    ------
    getReviewAndRating()
        Method to obtain the Ratings and Review Texts, and analysation for reviews
    getDowntime()
        Method to obtain the outages frequency and its date from tweets on twitter
    getPricing()
        Method to obtain the price lists of the different ISPs from seedly.sg
    """
    def __init__(self):
        phrase = "from:downdetectorSG " + self.__class__.__name__
        productNo = 196
        url_price = "https://seedly.sg/reviews/broadband/singtel-broadband"
        ''' Call the initialization function of the parent ISP class '''
        super().__init__(phrase, productNo, url_price)

    def getPricing(self): #Method overriding for Singtel due to its different table
        '''
        Method to obtain the price lists of the different ISPs from seedly.sg

        Returns:
            Plot out the Pricing plans in the multiline textbox
        '''
        isp_html = requests.get(self.url_price).text
        soup = BeautifulSoup(isp_html, 'lxml')
        review = soup.find_all('tr')[1:]
        print(len(review))
        for i in review:
            plan = i.find('div').get_text()
            length = ""
            price = i.find('div').find_next("div").get_text()
            self.plans.append(Plan(plan, length, price))

        for plan in self.plans:
            window['-ML1-'].print(plan.plan, end='')
            window['-ML1-'].print("\n", end='')
            window['-ML1-'].print(plan.price, end='')
            window['-ML1-'].print("\n\n", end='')


class Starhub(ISP):
    """
    Class for the Starhub ISP, inheriting the attributes and methods from the ISP class

    '''

    Attributes
    ----------
    phrase : str
        Phrase used to extract the tweets concerning this ISP
    productNo : int
        Product number of the ISP on Seedly, to extract data from the Seedly website
    url_price : str
        URL of the plans the ISP offers on Seedly
    reviews : Review[]
        Array of Review objects to store the reviews the ISP has gotten
    sums : int
        Total sum of ratings, used to calculate average rating later on
    avg : int
        Average rating of ISP
    stop_words : set
        Set of commonly used English words to filter out from the review text
    exclude : str[]
        Manually made array of words to filter out from the review text
    filteredgood : str[]
        Array of positive words that passed through the word filters
    filteredbad : str[]
        Array of negative words that passed through the word filters
    plans : Plan[]
        Array of Plan objects to store the different plans the ISP offers and their details
    downtimeArr : str[]
        Array of dates that the ISP has gone down on
    totalDown : int
        Total number of times the ISP has gone down
    badwords : str[]
        Array of negative attributes that describe the ISP
    goodwords : str[]
        Array of positive attributes that describe the ISP

    Methods
    ------
    getReviewAndRating()
        Method to obtain the Ratings and Review Texts, and analysation for reviews
    getDowntime()
        Method to obtain the outages frequency and its date from tweets on twitter
    getPricing()
        Method to obtain the price lists of the different ISPs from seedly.sg
    """
    def __init__(self):
        phrase = "from:downdetectorSG " + self.__class__.__name__
        productNo = 198
        url_price = "https://seedly.sg/reviews/broadband/starhub-broadband"
        ''' Call the initialization function of the parent ISP class '''
        super().__init__(phrase, productNo, url_price)

class Myrepub(ISP):
    """
    Class for the Myrepub ISP, inheriting the attributes and methods from the ISP class

    '''

    Attributes
    ----------
    phrase : str
        Phrase used to extract the tweets concerning this ISP
    productNo : int
        Product number of the ISP on Seedly, to extract data from the Seedly website
    url_price : str
        URL of the plans the ISP offers on Seedly
    reviews : Review[]
        Array of Review objects to store the reviews the ISP has gotten
    sums : int
        Total sum of ratings, used to calculate average rating later on
    avg : int
        Average rating of ISP
    stop_words : set
        Set of commonly used English words to filter out from the review text
    exclude : str[]
        Manually made array of words to filter out from the review text
    filteredgood : str[]
        Array of positive words that passed through the word filters
    filteredbad : str[]
        Array of negative words that passed through the word filters
    plans : Plan[]
        Array of Plan objects to store the different plans the ISP offers and their details
    downtimeArr : str[]
        Array of dates that the ISP has gone down on
    totalDown : int
        Total number of times the ISP has gone down
    badwords : str[]
        Array of negative attributes that describe the ISP
    goodwords : str[]
        Array of positive attributes that describe the ISP

    Methods
    ------
    getReviewAndRating()
        Method to obtain the Ratings and Review Texts, and analysation for reviews
    getDowntime()
        Method to obtain the outages frequency and its date from tweets on twitter
    getPricing()
        Method to obtain the price lists of the different ISPs from seedly.sg
    """
    def __init__(self):
        phrase = "from:downdetectorSG My Republic"
        productNo = 201
        url_price = "https://seedly.sg/reviews/broadband/myrepublic-broadband"
        ''' Call the initialization function of the parent ISP class '''
        super().__init__(phrase, productNo, url_price)

class Whiz(ISP):
    """
    Class for the Whiz ISP, inheriting the attributes and methods from the ISP class

    '''

    Attributes
    ----------
    phrase : str
        Phrase used to extract the tweets concerning this ISP
    productNo : int
        Product number of the ISP on Seedly, to extract data from the Seedly website
    url_price : str
        URL of the plans the ISP offers on Seedly
    reviews : Review[]
        Array of Review objects to store the reviews the ISP has gotten
    sums : int
        Total sum of ratings, used to calculate average rating later on
    avg : int
        Average rating of ISP
    stop_words : set
        Set of commonly used English words to filter out from the review text
    exclude : str[]
        Manually made array of words to filter out from the review text
    filteredgood : str[]
        Array of positive words that passed through the word filters
    filteredbad : str[]
        Array of negative words that passed through the word filters
    plans : Plan[]
        Array of Plan objects to store the different plans the ISP offers and their details
    downtimeArr : str[]
        Array of dates that the ISP has gone down on
    totalDown : int
        Total number of times the ISP has gone down
    badwords : str[]
        Array of negative attributes that describe the ISP
    goodwords : str[]
        Array of positive attributes that describe the ISP

    Methods
    ------
    getReviewAndRating()
        Method to obtain the Ratings and Review Texts, and analysation for reviews
    getDowntime()
        Method to obtain the outages frequency and its date from tweets on twitter
    getPricing()
        Method to obtain the outages frequency and its date from tweets on twitter
        Unfortunately for Whiz, none of its outtage data is available on twitter so the program relays this information to the user
    """
    def __init__(self):
        phrase = ""
        productNo = 200
        url_price = "https://seedly.sg/reviews/broadband/whizcomms-broadband"
        ''' Call the initialization function of the parent ISP class '''
        super().__init__(phrase, productNo, url_price)

    def getPricing(self): #Method overriding for Whizz due to its different table
        '''
        Method to obtain the price lists of the different ISPs from seedly.sg

        Returns:
            Plot out the Pricing plans in the multiline textbox
        '''
        isp_html = requests.get(self.url_price).text
        soup = BeautifulSoup(isp_html, 'lxml')
        review = soup.find_all('tr')[1:]
        print(len(review))
        for i in review:
            plan = i.find('div').get_text()
            length = i.find('div').find_next("div").get_text()
            price = i.find('div').find_next("div").find_next("div").find_next("div").get_text()
            self.plans.append(Plan(plan, length, price))
        for plan in self.plans:
            window['-ML1-'].print(plan.plan, end='')
            window['-ML1-'].print("\n", end='')
            window['-ML1-'].print(plan.length, end='')
            window['-ML1-'].print("\n", end='')
            window['-ML1-'].print(plan.price, end='')
            window['-ML1-'].print("\n\n", end='')

    def getDowntime(self):
        '''
        Method to obtain the outages frequency and its date from tweets on twitter
        Unfortunately for Whiz, none of its outtage data is available on twitter so the program relays this information to the user

        Returns:
            Prints out "no data available" on the GUI to notify the user
        '''
        window['-ML3-'].print("No data available",  end='')

class Viewqwest(ISP):
    """
    Class for the Viewqwest ISP, inheriting the attributes and methods from the ISP class

    '''

    Attributes
    ----------
    phrase : str
        Phrase used to extract the tweets concerning this ISP
    productNo : int
        Product number of the ISP on Seedly, to extract data from the Seedly website
    url_price : str
        URL of the plans the ISP offers on Seedly
    reviews : Review[]
        Array of Review objects to store the reviews the ISP has gotten
    sums : int
        Total sum of ratings, used to calculate average rating later on
    avg : int
        Average rating of ISP
    stop_words : set
        Set of commonly used English words to filter out from the review text
    exclude : str[]
        Manually made array of words to filter out from the review text
    filteredgood : str[]
        Array of positive words that passed through the word filters
    filteredbad : str[]
        Array of negative words that passed through the word filters
    plans : Plan[]
        Array of Plan objects to store the different plans the ISP offers and their details
    downtimeArr : str[]
        Array of dates that the ISP has gone down on
    totalDown : int
        Total number of times the ISP has gone down
    badwords : str[]
        Array of negative attributes that describe the ISP
    goodwords : str[]
        Array of positive attributes that describe the ISP

    Methods
    ------
    getReviewAndRating()
        Method to obtain the Ratings and Review Texts, and analysation for reviews
    getDowntime()
        Method to obtain the outages frequency and its date from tweets on twitter
    getPricing()
        Method to obtain the price lists of the different ISPs from seedly.sg
    """
    def __init__(self):
        phrase = "from:downdetectorSG " + self.__class__.__name__
        productNo = 199
        url_price = "https://seedly.sg/reviews/broadband/viewqwest-broadband"
        ''' Call the initialization function of the parent ISP class '''
        super().__init__(phrase, productNo, url_price)


#GUI code'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
def main():
    ''' Checks for the values of the DropDownList and excute the different classes methods accordingly.
        '''
    fig_photo = None
    if fig_photo is not None: #Checking if a graph has been plotted yet to erase them if they are initialised
        delete_fig_photo(fig_photo)
    fig = plt.gcf() #ploting of the bar graph
    fig.set_dpi(100) #setting the size of the bar graph
    m1 = M1() #calling of class M1 and its methods
    m1.getReviewAndRating()
    m1.getPricing()
    m1.getDowntime()
    fig_photo = draw_figure(window['-CANVAS-'].TKCanvas, fig) #initialisation of the graph onto the layout
    while True:
        ''' Refreshes the window before reading the values generated by the events happening in the GUI.
                '''
        window.Refresh() #refreshes any new updates to the layout
        event, values = window.Read() #reads the layout for any events happening and obtaining its value
        ''' Checks if the window of the GUI has been closed to end the program(process)
                '''
        if event in (sg.WIN_CLOSED, None): #If the window is closed, it will break and end the process
            break
        else:
            print(values["-drop-"])
            ''' Checks the values of the DropDownList and execute the different methods accordingly
                            '''
            if values["-drop-"] == "M1": #Checking of the droplist's selected value
                window["-ML1-"].update("") #Clearing the Output textbox before printing onto them
                window["-ML2-"].update("")
                window["-ML3-"].update("")
                if fig_photo is not None: #Checking if a graph has been plotted yet to erase them if they are initialised
                    delete_fig_photo(fig_photo)
                fig = plt.gcf()
                fig.set_dpi(100)
                m1 = M1()
                m1.getReviewAndRating()
                m1.getPricing()
                m1.getDowntime()
                fig_photo = draw_figure(window['-CANVAS-'].TKCanvas, fig)
            elif values["-drop-"] == "Singtel": #Checking of the droplist's selected value
                window["-ML1-"].update("") #Clearing the Output textbox before printing onto them
                window["-ML2-"].update("")
                window["-ML3-"].update("")
                if fig_photo is not None: #Checking if a graph has been plotted yet to erase them if they are initialised
                    delete_fig_photo(fig_photo)
                fig = plt.gcf()
                fig.set_dpi(100)
                sing = Singtel()
                sing.getReviewAndRating()
                sing.getPricing()
                sing.getDowntime()
                fig_photo = draw_figure(window['-CANVAS-'].TKCanvas, fig)
            elif values["-drop-"] == "Starhub": #Checking of the droplist's selected value
                window["-ML1-"].update("") #Clearing the Output textbox before printing onto them
                window["-ML2-"].update("")
                window["-ML3-"].update("")
                if fig_photo is not None: #Checking if a graph has been plotted yet to erase them if they are initialised
                    delete_fig_photo(fig_photo)
                fig = plt.gcf()
                fig.set_dpi(100)
                star = Starhub()
                star.getReviewAndRating()
                star.getPricing()
                star.getDowntime()
                fig_photo = draw_figure(window['-CANVAS-'].TKCanvas, fig)
            elif values["-drop-"] == "MyRepublic": #Checking of the droplist's selected value
                window["-ML1-"].update("") #Clearing the Output textbox before printing onto them
                window["-ML2-"].update("")
                window["-ML3-"].update("")
                if fig_photo is not None: #Checking if a graph has been plotted yet to erase them if they are initialised
                    delete_fig_photo(fig_photo)
                fig = plt.gcf()
                fig.set_dpi(100)
                myre = Myrepub()
                myre.getReviewAndRating()
                myre.getPricing()
                myre.getDowntime()
                fig_photo = draw_figure(window['-CANVAS-'].TKCanvas, fig)
            elif values["-drop-"] == "WhizComms": #Checking of the droplist's selected value
                window["-ML1-"].update("") #Clearing the Output textbox before printing onto them
                window["-ML2-"].update("")
                window["-ML3-"].update("")
                if fig_photo is not None: #Checking if a graph has been plotted yet to erase them if they are initialised
                    delete_fig_photo(fig_photo)
                fig = plt.gcf()
                fig.set_dpi(100)
                whizz = Whiz()
                whizz.getReviewAndRating()
                whizz.getPricing()
                whizz.getDowntime()
                fig_photo = draw_figure(window['-CANVAS-'].TKCanvas, fig)
            elif values["-drop-"] == "ViewQwest": #Checking of the droplist's selected value
                window["-ML1-"].update("") #Clearing the Output textbox before printing onto them
                window["-ML2-"].update("")
                window["-ML3-"].update("")
                if fig_photo is not None: #Checking if a graph has been plotted yet to erase them if they are initialised
                    delete_fig_photo(fig_photo)
                fig = plt.gcf()
                fig.set_dpi(100)
                view = Viewqwest()
                view.getReviewAndRating()
                view.getPricing()
                view.getDowntime()
                fig_photo = draw_figure(window['-CANVAS-'].TKCanvas, fig)

    window.Close()

if __name__ == "__main__":
    main()