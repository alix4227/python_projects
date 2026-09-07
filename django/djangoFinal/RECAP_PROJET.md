# Récap du projet "Final Django" (AJAX + Websockets)

Ce document explique, étape par étape, comment le projet a été construit, en se basant
sur le code réellement présent dans le dépôt. Il ne modifie aucun fichier du projet,
c'est un simple mémo de relecture.

## 0. Mise en place de l'environnement

- `my_script.sh` : crée un virtualenv (`django_venv`), installe les dépendances depuis
  `requirement.txt` (Django, psycopg2-binary, daphne, channels), puis active le venv.
- `psql_script.sh` : lance un conteneur Docker Postgres (`postgres:17-alpine`), crée
  l'utilisateur `djangouser` et la base `formationdjango`, exposée sur le port `5433`.
- `d09/settings.py` pointe `DATABASES` vers cette base Postgres (`ENGINE:
  django.db.backends.postgresql`, `HOST: localhost`, `PORT: 5433`).

## 1. Création du projet et de l'application `account` (Exercice 00)

Conformément au sujet : `django-admin startproject d09`, puis `startapp account`.

### Réglages globaux (`d09/settings.py`)
- `account` et `chat` sont ajoutées à `INSTALLED_APPS`, avec `daphne` en tête de liste
  (nécessaire pour que `daphne` prenne le relais du serveur de dev ASGI).
- `ASGI_APPLICATION = "d09.asgi.application"` est défini pour permettre les Websockets
  (obligatoire pour l'exercice 01, géré ici dès la mise en place car les deux apps sont
  développées dans la foulée).
- `CHANNEL_LAYERS` : la config **actuelle** utilise `channels.layers.InMemoryChannelLayer`.
  Un `git diff` sur ce fichier montre que la version **committée** utilisait plutôt
  `channels_redis.core.RedisChannelLayer` (avec Redis sur `127.0.0.1:6379`) — ce
  changement vers l'InMemoryChannelLayer est présent dans l'arbre de travail mais pas
  encore commité. Redis n'est pas listé dans `requirement.txt`, ce qui suggère que le
  Redis n'était pas dispo/nécessaire lors du dernier test et a été remplacé pour tester
  en local.

### Routing HTTP (`d09/urls.py`)
```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include("account.urls")),
    path('chat/', include("chat.urls")),
]
```
- L'admin par défaut est conservée (obligatoire selon les règles de la journée).
- Les urls de `account` sont montées à la racine, celles de `chat` sous `/chat/`.

### Formulaire de connexion (`account/forms.py`)
- `CustomAuthenticationForm` hérite de `AuthenticationForm` (le "cadeau" du sujet) et ne
  fait que surcharger le rendu des champs `username`/`password` avec des classes
  Bootstrap (`form-control form-control-sm`) et des placeholders.

### Vues (`account/views.py`)
- `Register` (CreateView + `UserCreationForm`) : permet de créer un compte ; redirige
  vers `account` (page de login) après inscription. `dispatch()` renvoie un `Http404` si
  l'utilisateur est déjà connecté.
- `Login` (FormView + `CustomAuthenticationForm`) :
  - `post()` distingue deux cas selon le `Content-Type` de la requête :
    - Si c'est du JSON (`application/json`) → c'est l'appel AJAX du formulaire de login.
      Le body est parsé (`json.loads`), on récupère `payload.username`/`payload.password`,
      on appelle `authenticate()`, puis `login()` si l'utilisateur est valide. La réponse
      est un `JsonResponse` (`{'status': 'User logged!', 'username': ...}` ou 401 si échec).
    - Sinon → comportement standard de Django (`form_valid` classique), utilisé pour le
      chargement initial de la page (rendu du formulaire côté serveur).
  - Ce découpage permet de respecter la contrainte "communication uniquement via AJAX en
    POST" pour la partie interactive, tout en gardant un formulaire Django classique pour
    le rendu HTML initial et la validation des erreurs.
- `Logout` (View) :
  - `get()` : déconnexion classique avec redirection (utilisée si on va sur `/logout/`
    directement).
  - `post()` : déconnexion via AJAX, renvoie un `JsonResponse` sans recharger la page.

### Template (`account/templates/account/base.html`)
C'est le cœur de l'exercice 00. Il sert de layout pour toute l'app `account` **et**
contient directement la logique AJAX de login/logout dans sa barre de navigation :

- Si `user.is_authenticated` est faux → affiche le formulaire `#form-login` (les deux
  champs du `CustomAuthenticationForm` + un bouton "Login").
- Sinon → affiche "Logged as {{ user }}" + un formulaire `#form-logout` avec un bouton
  "Logout".
- Un bloc `<script>` en bas de page :
  - `getCookie('csrftoken')` : petite fonction utilitaire pour lire le cookie CSRF de
    Django (nécessaire car le call AJAX POST doit envoyer le header `X-CSRFToken`
    manuellement, vu qu'on n'utilise pas `{% csrf_token %}` dans un `<form>` classique
    soumis par le navigateur).
  - `$(document).on('submit', '#form-login', ...)` : intercepte la soumission du
    formulaire de login (`e.preventDefault()`), construit un objet JSON `{username,
    password}`, l'envoie en `POST` (`contentType: application/json`) vers l'url `account`
    avec le header CSRF. En cas de succès, remplace le `<ul>` contenant le formulaire par
    le bloc "Logged as ..." + bouton logout, **sans recharger la page**.
  - `$(document).on('submit', '#form-logout', ...)` : même principe pour la
    déconnexion : POST vers `logout`, puis remplacement du bloc HTML par le formulaire de
    login, toujours sans rechargement de page.
- Comme le rendu HTML initial (`Login.form_valid`/`GET`) dépend de
  `user.is_authenticated`, un rafraîchissement manuel de la page retrouve bien le bon état
  (connecté ou pas) — ce qui correspond à l'exigence du sujet.
- Bootstrap est utilisé pour le style (autorisé par le sujet), jQuery pour l'AJAX (seule
  librairie JS autorisée).

### `account/templates/account/register.html`
Formulaire d'inscription simple (`UserCreationForm` affiché champ par champ, avec
affichage des erreurs), soumis en POST classique (pas d'AJAX exigé pour l'inscription,
seul le login/logout doit l'être selon le sujet).

## 2. Application `chat` — chatrooms de base (Exercice 01)

### Modèle (`chat/models.py`)
- `Chatroom` : `name` (le nom affiché/utilisé dans l'URL) + `members`
  (`ManyToManyField` vers `User`, `related_name='chatrooms'`) qui sert à savoir qui est
  actuellement connecté à la room (utilisé par l'exercice 03).
- `Message` : `chatroom` (FK), `content`, `user` (FK), `created` (horodatage auto). Sert
  à la fois à l'historique (exercice 02) et à l'affichage temps réel.
- Migration unique `chat/migrations/0001_initial.py` créant ces deux tables
  (`db_table = "Chatroom"` / `"Message"`).

### Vues (`chat/views.py`)
- `index` : liste toutes les `Chatroom` existantes et les passe au template (les "trois
  liens" du sujet correspondent aux chatrooms créées en base, un lien par room).
- `room(request, room_name)` : si l'utilisateur est connecté, affiche `chat/room.html`
  avec `room_name` en contexte ; sinon redirige vers la page de login (`account`) — c'est
  ce qui rend le chat inaccessible aux utilisateurs non connectés.
- `CreateChatroom` (CreateView) : formulaire minimal (juste le champ `name`) pour créer
  une chatroom depuis `chat/chatroom_creation.html` — un outil pratique pour peupler la
  base de données avec les "trois chatrooms" demandées par le sujet, sans passer par
  l'admin.
- `CreateMessage` : vue POST "classique" (non-Websocket) qui crée un `Message` et
  redirige vers la room ; semble être une première version/alternative avant le passage
  tout-Websocket exigé par le sujet (le flux réellement utilisé dans `room.html` passe
  par les Websockets, pas par cette vue).

### Routing Websocket
- `chat/routing.py` : `re_path(r'^ws/chat/(?P<room_name>[^/]+)/$',
  consumers.ChatConsumer.as_asgi())`.
- `d09/asgi.py` : `ProtocolTypeRouter` avec :
  - `"http"` → l'application Django classique.
  - `"websocket"` → `AllowedHostsOriginValidator(AuthMiddlewareStack(URLRouter(...)))`,
    ce qui permet au consumer d'accéder à `self.scope["user"]` (utilisateur Django
    authentifié via la session, grâce à `AuthMiddlewareStack`).

### `ChatConsumer` (`chat/consumers.py`)
- `connect()` :
  1. Récupère `room_name` depuis l'URL, puis normalise ce nom en un identifiant de
     groupe valide (`re.sub(r'[^a-zA-Z0-9\-_\.]', '_', room_name)`) — les noms de groupe
     Channels ont des contraintes de caractères, d'où cette normalisation.
  2. Rejoint le groupe Channels (`group_add`) et accepte la connexion.
  3. Ajoute l'utilisateur courant à `chatroom.members` (`save_connected_members`) →
     alimente la liste des connectés (exercice 03).
  4. Récupère l'historique des messages et la liste des membres connectés, envoie ces
     infos **uniquement au client qui vient de se connecter** (`self.send(...)`, pas de
     `group_send`).
  5. Diffuse à **tout le groupe** (y compris soi-même, via `group_send`) le message
     `"<user> has joined the chat"`.
- `disconnect()` : retire l'utilisateur de `chatroom.members`, puis diffuse `"<user> has
  left the chat"` à tout le groupe avant de quitter le groupe Channels.
- `receive()` : reçoit `{"message": ...}` du client, sauvegarde le message en base
  (`save_message`), puis le diffuse à tout le groupe sous forme `"<user>: <message>"`.
- `chat_message()` (handler du `type: "chat.message"`) : renvoie au client connecté un
  JSON `{"message": ..., "messages": [...], "members_connected": [...]}` — c'est le
  point d'entrée unique qui alimente le JS côté navigateur.

### Template `chat/room.html`
- Layout façon "app de chat" (cartes Bootstrap : liste des membres à gauche, messages à
  droite), défini avec du CSS custom dans `chat/base.html`.
- `{{ room_name|json_script:"room-name" }}` : technique Django pour passer une valeur
  Python au JS de façon sûre (échappée), lue ensuite via
  `JSON.parse(document.getElementById('room-name').textContent)`.
- Ouverture de la WebSocket : `ws://` ou `wss://` (selon le protocole de la page) vers
  `/ws/chat/<roomName>/`.
- `chatSocket.onmessage` :
  - Si `data.message` est présent → ajoute une bulle de message (`appendMessage`).
  - Si `data.messages` est présent (envoyé seulement à la connexion) → vide puis
    reconstruit tout le conteneur de messages avec l'historique (exercice 02).
  - Si `data.members_connected` est présent → reconstruit la liste des membres connectés
    (exercice 03).
- Envoi de message : `Enter` dans le `<textarea>` (sans `Shift`) ou clic sur le bouton
  d'envoi déclenchent `sendMessage()`, qui envoie `{"message": ...}` sur la socket si
  elle est ouverte, puis vide le champ.
- Seul jQuery/JS natif est utilisé, pas d'AJAX HTTP pour le chat — conforme au sujet.

## 3. Historique des messages (Exercice 02)

Implémenté directement dans `ChatConsumer.connect()` :
```python
messages = await self.get_messages()          # tous les messages, triés par date
messages = [...][-3:]                          # les 3 derniers seulement
```
Ces 3 derniers messages sont envoyés uniquement au client qui vient de se connecter
(pas de `group_send`), et affichés du plus ancien au plus récent car `get_messages` trie
par `created` croissant puis on ne garde que les 3 derniers de cette liste triée.

## 4. Liste des utilisateurs connectés (Exercice 03)

- Le champ `Chatroom.members` (ManyToMany) sert de "liste des connectés" : ajouté à la
  connexion (`save_connected_members`), retiré à la déconnexion
  (`remove_connected_members`).
- Cette liste est renvoyée à chaque connexion/déconnexion via `members_connected` dans
  le payload JSON, et le JS de `room.html` la réaffiche dans le `<ul id="members-list">`,
  visuellement séparé (`.contacts_card`) du conteneur des messages (`#messages_input`) —
  conforme à l'exigence "conteneur distinct".
- Les messages `"<user> has joined/left the chat"` sont envoyés à tout le groupe via
  `chat_message`, donc affichés dans le flux de messages normal, à la suite des autres.

## 5. Défilement (Exercice 04)

Le CSS de `chat/base.html` définit `.msg_card_body { overflow-y: auto; }` et `.card {
height: 500px; }`, ce qui donne un conteneur de messages à hauteur fixe avec scroll.
**Point d'attention** : le code actuel de `room.html` ne semble pas forcer explicitement
le scroll vers le bas à chaque nouveau message (pas de `scrollTop =
scrollHeight` visible dans le script) — si ce comportement fonctionne quand même à l'usage,
il vaut la peine de vérifier ce point en le retestant, sinon c'est probablement la partie
qui reste à finaliser/vérifier pour l'exercice 04.

## Résumé du flux global

1. `account/urls.py` + `account/views.py` + `account/templates/account/base.html` =
   Exercice 00 (login/logout AJAX).
2. `chat/models.py`, `chat/consumers.py`, `chat/routing.py`, `d09/asgi.py`,
   `chat/templates/chat/room.html` = Exercice 01 (chat Websocket de base).
3. `ChatConsumer.connect()` (les 3 derniers messages) = Exercice 02.
4. `Chatroom.members` + `members_connected` dans le consumer et le template = Exercice 03.
5. CSS `.msg_card_body`/`.card` dans `chat/base.html` = Exercice 04 (à confirmer pour
   l'auto-scroll).

## Fichiers annexes

- `requirement.txt` : dépendances (`pip freeze`), conforme à la règle spécifique du
  sujet.
- `account/fixtures/test_users.json` : quatre utilisateurs de test (`alice`, `bob`,
  `carla`, `Alix`) pour peupler rapidement la base pendant les tests manuels.
- `my_script.sh` / `psql_script.sh` : scripts d'installation de l'environnement
  (venv + Postgres via Docker), pas des livrables du sujet mais des aides personnelles.
