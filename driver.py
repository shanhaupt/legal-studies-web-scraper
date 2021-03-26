import requests
from bs4 import BeautifulSoup
import re
import json

class Page():

    def __init__(self, pageURL):
        self.pageURL = pageURL
        self.l_pageSubURLS = []

    def findPageSubURLS(self):
        reqs = requests.get(self.pageURL)
        soup = BeautifulSoup(reqs.text, 'html.parser')

        for link in soup.find_all('a'):
            tempSubURL = link.get('href')
            if tempSubURL is not None:
                if ( (("/press-release/" in tempSubURL) or ("/news/" in tempSubURL)) and (tempSubURL[0] == '/')):
                    actualSubURL = "https://drugpolicy.org" + tempSubURL
                    self.l_pageSubURLS.append(actualSubURL)


class URLFinder():

    def __init__(self, WebsiteToParseForURLS, numPagesToProcess):
        
        self.website = WebsiteToParseForURLS
        self.numPagesToProcess = numPagesToProcess

        # List of Page objects
        self.l_PageObjects = []

        self.init_PageObjects()

    
    def init_PageObjects(self):
        for i in range(self.numPagesToProcess):
            pageURL = self.website + str(i)
            self.l_PageObjects.append(Page(pageURL))
        

class Article:
    def __init__(self, url, content_ExcludeList):
        self.url = url
       
        self.articleRequest = requests.get(self.url)
        self.articleContent = self.articleRequest.content
        self.articleSoup = BeautifulSoup(self.articleContent, 'html.parser')

        self.content_ExcludeList = content_ExcludeList

        self.dateWritten = None
        self.headline = None
        self.l_content = []
        self.l_terms = []

        # We will be writing classifications to these later...
        self.classifications = {}
        self.classifications["headline_drugs"] = None
        self.classifications["terms_drugs"] = None
        self.classifications["content_drugs"] = None

        self.classifications["headline_states"] = None
        self.classifications["terms_states"] = None
        self.classifications["content_states"] = None

        # Variable to store final JSON in 
        self.articleJSON = None




    def parseArticleDate(self):
        l_dates = self.articleSoup.find_all('time')
        if len(l_dates) == 1:
            dateString = l_dates[0].get_text()
            self.dateWritten = Article.cleanString(dateString)
        else:
            print("WARNING: This article contains more than one <time> element...")

    def parseArticleHeadline(self):
        l_Headlines = self.articleSoup.find_all('h1', class_='node--type-news__title')
        if len(l_Headlines) == 1:
            headlineSpan = l_Headlines[0].find('span')
            self.headline = Article.cleanString(headlineSpan.get_text())
        else:
            print("WARNING: This article contains more than one <h1> element of class {node--type-news__title}...")

    def parseArticleContent(self):
        l_tempContent = None
        l_content = self.articleSoup.find_all('div', class_='field field--body field--name-body field--type-text-with-summary field--label-hidden')

        for content in l_content:
            s_content = Article.cleanString(content.get_text())

            b_validString = True
            for s_reserved in self.content_ExcludeList:
                if s_reserved in s_content:
                    b_validString = False
            
            if ( b_validString and (s_content != " ") and (s_content != "") ):
                self.l_content.append(s_content)

    def parseArticleTerms(self):
        l_terms = self.articleSoup.find_all('div', class_='terms')
        for term in l_terms:
            s_Term = Article.cleanString(term.get_text())
            self.l_terms.append(s_Term)

    def printArticleAttr(self, numTabs):
        
        tabString = ""
        for tab in range(numTabs):
            tabString += "\t" 
        
        tabString_Extra = tabString = "\t"


        print(tabString + "Article URL: " + self.url)

        # Print the article date
        if self.dateWritten is not None:
            print (tabString_Extra + "Date Written: " + self.dateWritten)
        else:
            print (tabString_Extra + "Date Written: None Set") 

        # Print the article headline 
        if self.headline is not None:
            print (tabString_Extra + "Article Headline: " + self.headline)
        else:
            print (tabString_Extra + "Article Headline: None Set")
        
        # Print the article Terms
        if len(self.l_terms) != 0:
            s_terms = tabString_Extra + "Article Terms: |"
            for term in self.l_terms:
                s_terms += term + "|"
            print(s_terms)
        else:
            print(tabString_Extra + "Article Terms: None Set")

        # Print the article content
        if len(self.l_content) != 0:
            s_content = tabString_Extra + "Article Content: "
            for content in self.l_content:
                s_content += content
            print(s_content)
        else:
            print(tabString_Extra + "Article Content: None Set ")

        # Print the Classifiers
        print(self.classifications["headline_drugs"])
        print(self.classifications["terms_drugs"])
        print(self.classifications["content_drugs"])

        print(self.classifications["headline_states"])
        print(self.classifications["terms_states"])
        print(self.classifications["content_states"])

    def makeJSON(self):
        # init the final JSON data object
        jsonData = {}

        # Make arrays to group hits by classification category 
        l_StateHitsAggregate_temp = self.classifications["headline_states"] + self.classifications["terms_states"] + self.classifications["content_states"]
        # Make Array of All Drug Hits
        l_DrugHitsAggregate_temp = self.classifications["headline_drugs"] + self.classifications["terms_drugs"] + self.classifications["content_drugs"]

        # Remove Dupes while keeping initial ordering
        l_StateHitsAggregate = [i for n, i in enumerate(l_StateHitsAggregate_temp) if i not in l_StateHitsAggregate_temp[:n]]
        l_DrugHitsAggregate = [i for n, i in enumerate(l_DrugHitsAggregate_temp) if i not in l_DrugHitsAggregate_temp[:n]]
        
        # Create The Dict To be turned into JSON later
        hits_byClassificationCategory = {}
        hits_byClassificationCategory["state"] = l_StateHitsAggregate
        hits_byClassificationCategory["drug"] = l_DrugHitsAggregate



        # Make arrays to group hits by article section
        l_HeadlineHitsAggregate_temp = self.classifications["headline_drugs"] + self.classifications["headline_states"]
        l_TermHitsAggregate_temp = self.classifications["terms_drugs"] + self.classifications["terms_states"]
        l_ContentHitsAggregate_temp = self.classifications["content_drugs"] + self.classifications["content_states"]

        # Remove Dupes while keeping initial ordering
        l_HeadlineHitsAggregate = [i for n, i in enumerate(l_HeadlineHitsAggregate_temp) if i not in l_HeadlineHitsAggregate_temp[:n]]
        l_TermHitsAggregate = [i for n, i in enumerate(l_TermHitsAggregate_temp) if i not in l_TermHitsAggregate_temp[:n]]
        l_ContentHitsAggregate = [i for n, i in enumerate(l_ContentHitsAggregate_temp) if i not in l_ContentHitsAggregate_temp[:n]]

        # Create the dict to be turned into JSON later
        hits_byArticleSection = {}
        hits_byArticleSection["headline"] = l_HeadlineHitsAggregate
        hits_byArticleSection["terms"] = l_TermHitsAggregate
        hits_byArticleSection["content"] = l_ContentHitsAggregate

        classifications = {}
        classifications["agregate"] = hits_byClassificationCategory
        classifications["article-section"] = hits_byArticleSection

        # Make the terms JSON
        terms = {}
        for i, term in enumerate(self.l_terms):
            key = "term-"+str(i)
            terms[key] = term

        # Make the content JSON
        s_content = ""
        for content in self.l_content:
            if content is not None:
                s_content += content + " "



        # Make the final JSON data object
        jsonData["article-url"] = self.url
        jsonData["article-headline"] = self.headline
        jsonData["article-date-published"] = self.dateWritten
        jsonData["article-terms"] = terms
        jsonData["article-classifications"] = classifications
        jsonData["article-content"] = s_content

        self.articleJSON = jsonData

    @classmethod
    def cleanString(cls, string):
        l_string = string.split()
        returnString = ' '.join(l_string)
        returnString = returnString.lower()
        returnString = returnString.strip()
        return returnString

class Classifier():
    def __init__(self, statesFilePath, drugsFilePath):
        self.pathToStatesFile = statesFilePath
        self.pathToDrugsFile = drugsFilePath

        self.l_states = []
        self.l_drugs = []

        self.fileReader(self.pathToStatesFile, True)
        self.fileReader(self.pathToDrugsFile, False)

       

    # Note: This function has really bad performance - see below comments for detials

    # If isStatesList is ture, we are reading a file that contains states, one per line
    # If isStatesList is False, we are reading a file that contains drugs, one per line
    def fileReader(self, fileToRead, isStatesList):
        with open(fileToRead) as f:
            l_lines = f.readlines()
            for line in l_lines:
                # Reusing the string cleaner function from the article class
                # Note: If we ever seperate the classes into discrete files, we will need to import the Article package or create a new cleanString funtion
                cleanLine = Article.cleanString(line)

                if isStatesList:
                    self.l_states.append(cleanLine)
                else:
                    self.l_drugs.append(cleanLine)

    def classifyArticle(self, article):
        headline_stateHits = []
        content_stateHits = []
        terms_stateHits = []

        headline_drugHits = []
        content_drugHits = []
        terms_drugHits = []

        if ((self.l_states is None) or (self.l_drugs is None)):
            print("The states or drugs list in Classifier.classifyArticle() is Empty...  Quitting")
            exit()
        else:
            # Bad Perf Here - Fix Later 
            for state in self.l_states:
                
                # Check the headline for the classifier
                if article.headline is None:
                    print("The article's headline string is empty... Quitting")
                    exit()
                else:
                    if state in article.headline:
                        headline_stateHits.append(state)

                # Check the terms for the classifier
                for term in article.l_terms:
                    if state in term:
                        terms_stateHits.append(state)

                # Check the content for the classifier
                for content in article.l_content:
                    if state in content:
                        content_stateHits.append(state)

            for drug in self.l_drugs:
                
                # Check the headline for the classifier
                if article.headline is None:
                    print("The article's headline string is empty... Quitting")
                    exit()
                else:
                    if drug in article.headline:
                        headline_drugHits.append(drug)

                # Check the terms for the classifier
                for term in article.l_terms:
                    if drug in term:
                        terms_drugHits.append(drug)

                # Check the content for the classifier
                for content in article.l_content:
                    if drug in content:
                        content_drugHits.append(drug)

        article.classifications["headline_drugs"] = headline_drugHits
        article.classifications["terms_drugs"] = terms_drugHits
        article.classifications["content_drugs"] = content_drugHits

        article.classifications["headline_states"] = headline_stateHits
        article.classifications["terms_states"] = terms_stateHits
        article.classifications["content_states"] = content_stateHits
        

    # Utility functions to print the states and drugs list
    def printStates(self):
        for state in self.l_states:
            print(state)

    def printDrugs(self):
        for drug in self.l_drugs:
            print(drug)





if __name__ == "__main__":

    ################
    #### CONFIG ####
    ################

    # Define a list of strings that should not be included in article parsing
    article_contentExcludeList = [
            "donate",
            "drug policy alliance is a 501(c)(3) nonprofit registered in the us under ein: 52-1516692",
            "sign up to receive action alerts and news about drug policy reform",
            "for the first time ever, we’re finally seeing real momentum to decriminalize drugs at both the state and federal level. join the fight to end the criminalization of people who use drugs"
        ]

    # Base website page URL to parse for Sub URLS
    WebsiteToParseForURLS = "https://drugpolicy.org/press-release?page="

    # Total Number of pages to parse
    numPagesToParse = 2

    # Define The path to the states file
    statesFilePath = "./src/states.txt"
    # Define the path to the drugs file
    drugsFilePath = "./src/drugs.txt"

    # Final JSON File Output
    finalJSONFilePath = "./src/out.json"
    ################
    ## END CONFIG ##
    ################


    # Keep a list of article objects
    l_articleObjects = []
    i_articleCounter = 0
    # Final JSON Object
    jsonData_out = {}
    articles_out = {}

    # Create the URL finder class
    urlFinder = URLFinder(WebsiteToParseForURLS, numPagesToParse)

    # Create the Classifier Class
    classifier = Classifier(statesFilePath, drugsFilePath)

    # Loop through each page object in the URL finder class
    # Note: This outer loop is not necessary, but for perforamnce it will be better to process one page at, where each page has X articles (i.e. sub URLs)
    for page in urlFinder.l_PageObjects:
        # Find the sub URLS that are present on each page
        page.findPageSubURLS()
        page.findPageSubURLS()
        print("Parsing Page URL: "  + page.pageURL + " - Found " + str(len(page.l_pageSubURLS)) + " article url's on the page.")

        # For each SUB URL, create an article object as each SUB URL actually corresponds to a discrete article on the base website
        for subURL in page.l_pageSubURLS:
            articleObject = Article(subURL, article_contentExcludeList)
            i_articleCounter += 1
            l_articleObjects.append(articleObject)

            # Process the article immediately after we create the object to avoid overhead
            articleObject.parseArticleDate()
            articleObject.parseArticleHeadline()
            articleObject.parseArticleTerms()
            articleObject.parseArticleContent()

            
            classifier.classifyArticle(articleObject)
            
            articleObject.makeJSON()
            s_jsonKey = "article-" + str(i_articleCounter)
            articles_out[s_jsonKey] = articleObject.articleJSON

    jsonData_out["articles"] = articles_out

    with open(finalJSONFilePath, 'w', encoding='utf-8') as f:
        json.dump(jsonData_out, f, ensure_ascii=False, indent=4)




    

        


       