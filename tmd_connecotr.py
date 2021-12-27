import requests

from e_mail import send_email

API_LINK = 'https://api.themoviedb.org/3'
API_KEY = 'af9723a178712cff3229d2d2535483aa'

#  account wymaga api_key i session_id, do utworzenia sessji potrzeba request_token i na jego podstawie dostajemy session_id
API_URLS = {
    'account_detail': API_LINK + '/account',
    'request_token': API_LINK + '/authentication/token/new',
    'login': API_LINK + '/authentication/token/validate_with_login',
    'new_session': API_LINK + '/authentication/session/new',
    'delete_session': API_LINK + '/authentication/session',
    'get_user_lists': API_LINK + '/account/{}/lists',
    'list_detail': API_LINK + '/list/{}',
    'search_movie': API_LINK + '/search/movie',
    'add_movie': API_LINK + '/list/{}/add_item',
    'remove_movie': API_LINK + '/list/{}/remove_item',
    'create_list': API_LINK + '/list',
    'watch_provider': API_LINK + '/movie/{}/watch/providers'
}


class TMDConnector:

    def __init__(self):
        self.session_id: str = ''
        self.request_token: str = ''
        self.username: str = ''
        self.account_id: int
        #  obiekt tmd przechowuje id listy która była wybrana, jezeli chcemy dodac film do listy to stad wezmiemy list_id
        self.actual_list_id: str = ''
        self.language: str = 'PL'
        self.no_provider_list_id: str = ''
        self.no_providers_list_name: str = 'no_provider'
        #  selected region, default = PL
        self.selected_region: str = 'PL'
        self.providers_ids = []

    def login_to_api(self, login, password):
        #  opakowujemy metody w jedna ktora je wykonyje, dla czytelnosci, wykonuja sie tutaj wszystkie metody niezbedne
        #  do dzialania z api
        self.get_request_token()
        if self.api_auth_user(login, password):
            self.get_session_id()
            self.get_account_details()
            return True
        else:
            return False

    def get_request_token(self):
        """
        request token is required to get session_id
        """
        try:
            response = requests.get(API_URLS['request_token'], params={'api_key': API_KEY})
            self.request_token = response.json()['request_token']
        except Exception as e:
            print(e)

    def api_auth_user(self, login, password) -> bool:
        """
        login user to api
        get request_token from api
        """
        body = {
            "username": login,
            "password": password,
            "request_token": self.request_token
        }
        try:
            response = requests.post(API_URLS['login'], params={'api_key': API_KEY}, data=body)
            self.request_token = ''
            self.request_token = response.json()['request_token']
            if self.request_token != '':
                return True
        except Exception as e:
            print(e)
            return False

    def get_account_details(self):
        """
        get account info from api, required for few requests(account_id)
        """
        #  trzeba zapytac api o account_id, ogolnie droga logowania jest dluga i skomplikowana(duzo requestow)
        #  ale takie api, tego sie nie obejdzie
        try:
            response = requests.get(API_URLS['account_detail'], params={
                'api_key': API_KEY,
                'session_id': self.session_id
            })
            response = response.json()
            self.account_id = response['id']
            self.username = response['username']
        except Exception as e:
            print(e)

    def get_session_id(self):
        """get session if from api"""
        #  session_id jest wymagane aby tworzyc listy oraz dodawac do nich filmy
        body = {
            "request_token": self.request_token
        }
        try:
            response = requests.post(API_URLS['new_session'], params={'api_key': API_KEY}, data=body)
            self.session_id = response.json()['session_id']
        except Exception as e:
            print(e)

    def delete_session(self) -> bool:
        """delete current session"""
        #  usuwamy sessje aby wylogowac sie z api
        body = {
            "session_id": self.session_id
        }
        try:
            response = requests.post(API_URLS['delete_session'], params={'api_key': API_KEY}, data=body)
            #  jezeli zakonczylo sie sukcesem, api zwraca zmienna success jako true to delete_session zwraca true
            if response.json()['success']:
                return True
            return False
        except Exception as e:
            print(e)

    def get_user_lists(self) -> list:
        """
        get all user list
        """
        #  pobieramy wszystkie listy filmow stworzone przez uzytkowika
        try:
            response = requests.get(API_URLS['get_user_lists'].format(self.account_id), params={
                'api_key': API_KEY,
                'session_id': self.session_id
            })
            return response.json()['results']
        except Exception as e:
            print(e)

    def create_list(self, name, description, language):
        """create list"""
        body = {
            'name': name,
            'description': description,
            'language': language
        }
        try:
            response = requests.post(API_URLS['create_list'], params={
                                    'api_key': API_KEY,
                                    'session_id': self.session_id},
                                     data=body)
            return response.json()
        except Exception as e:
            print(e)

    def get_list_detail(self, list_id):
        """get list with movies from api"""
        try:
            response = requests.get(API_URLS['list_detail'].format(list_id), params={
                'api_key': API_KEY,
                'language': self.language
            })
            self.actual_list_id = response.json()['id']
            return response.json()['items']
        except Exception as e:
            print(e)

    def add_movie_to_list(self, movie_id):
        """add movie to list"""
        body = {
            'media_id': int(movie_id)
        }
        try:
            #  sprawdzamy czy film jest dostepny u providera, jezeli tak to dodajemy do listy, jezeli nie to
            #  dodajemy do listy no_provider
            if self.watch_provider(int(movie_id)):
                response = requests.post(API_URLS['add_movie'].format(self.actual_list_id),
                                         params={'api_key': API_KEY, 'session_id': self.session_id},
                                         data=body)
                print(response.json())
            else:
                response = requests.post(API_URLS['add_movie'].format(self.no_provider_list_id),
                                         params={'api_key': API_KEY, 'session_id': self.session_id},
                                         data=body)
                print(response)
        except Exception as e:
            print(e)

    def remove_movie_from_list(self, movie_id):
        body = {
            'media_id': movie_id
        }
        try:
            response = requests.post(API_URLS['remove_movie'].format(self.actual_list_id), params={
                                    'api_key': API_KEY, 'session_id': self.session_id},
                                     data=body)
            print(response.json()['status_message'])
        except Exception as e:
            print(e)

    def search_movie(self, language, query):
        """search movie by phrase"""
        try:
            response = requests.get(API_URLS['search_movie'], params={
                'api_key': API_KEY,
                'language': language,
                'query': query
            })
            return response.json()['results']
        except Exception as e:
            print(e)

    def delete_list(self, list_id):
        """delete list"""
        try:
            response = requests.delete(API_URLS['list_detail'].format(list_id), params={
                'api_key': API_KEY,
                'session_id': self.session_id
            })
            if response.json()['status_code'] == 200:
                print('list has been deleted')
            else:
                print(response.json()['status_message'])
        except Exception as e:
            print(e)

    def watch_provider(self, movie_id) -> bool:
        """
        method check if movie is available in current cuntry
        return: true if movie is available in provider
                false if movie has no provider
        """
        try:
            response = requests.get(API_URLS['watch_provider'].format(movie_id), params={'api_key': API_KEY})
            #  jezeli odpowiedz z api jest pusta to znaczy ze film nie jest dostepny przez providera w danym regionie
            response = response.json()
            print(response['results'])
            if self.selected_region in response['results']:
                return True
            return False
        except Exception as e:
            print(e)

    def get_no_provider_list_id(self):
        """get list_id with no provider movie"""
        try:
            lists = self.get_user_lists()
            #  sprawdzamy czy istnieje lista ktora przychowuje filmy bez providera
            #  jezeli nie to tworzymy taka i nadajemy nazwe "no_provider"
            #  potem bedziemy skanowac filmy z tej listy
            no_provider_list = [i for i in lists if i['name'] == self.no_providers_list_name]

            if not no_provider_list:
                li = self.create_list(name=self.no_providers_list_name, language=self.language,
                                      description="movies with no provider")
                self.no_provider_list_id = li.json()['list_id']
            else:
                self.no_provider_list_id = no_provider_list[0]['id']
        except Exception as e:
            print(e)

    def set_selected_region(self, region):
        """set provider region"""
        self.selected_region = region

    def send_email(self, provider, title):
        send_email(provider, title)

    def check_available_provider_for_movie(self):
        """chek if movie from no_provider list has been add to any provider in region
            if yes, we send email
        """
        try:
            self.get_no_provider_list_id()
            user_list = self.get_list_detail(self.no_provider_list_id)
            for movie in user_list:
                response = requests.get(API_URLS['watch_provider'].format(movie['id']), params={'api_key': API_KEY})
                response = response.json()
                if self.selected_region in response['results']:
                    provider = response['results']
                    self.send_email(provider, movie['title'])
        except Exception as e:
            print(e)

    #  ponizej metody wymagane dla login_managera
    def is_active(self):
        return True

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

    def is_admin(self):
        return False

    def get_id(self):
        return self.session_id
