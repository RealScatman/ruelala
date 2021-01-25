# eCommerce/Braintree source Render/ eGrocer
ecommerce source render using django and bootstrap and jquery/js
Has updated BrainTree Payments integration
also has stripe api payment integration
Has Delivery Module that can impot zipcodes and display delivery zip codes on google map
Has checkout process for curbside pickup timeslot and vehicle slot logic - all within app - no phone calls needed.
Simplistic filtering with django filters and DRF
custom analytics to track user browsing history and save to db
sales/order tracking/dashboard using chart.js

Developed on a Mac
Create a clone and check this ish out!

### Requirements
- Django 2.1.5
- Python 3.8 (and up)

### Recommended Start:
#(using django built in sqlite3 database configuration, and creating a superuser)

```
$ cd path/to/your/dev/folder
$ mkdir ruelala
$ cd ruelala
$ virtualenv -p python3 .
$ source bin/activate
$ mkdir src
$ cd src
$ git clone https://github.com/RealScatman/ruelala.git .
$ git remote remove origin
$ rm -rf .git
(ruelala) $ pip install -r requirements.txt
...
Create a local settings file (copy the base file)
...
(ruelala) $ python manage.py makemigrations
(ruelala) $ python manage.py migrate
(ruelala) $ python manage.py createsuperuser
(ruelala) $ python manage.py runserver

```


### Heroku Go Live (setup)
```
(ruelala) $ heroku login
(ruelala) $ heroku create project-name
(ruelala) $ heroku addons:create heroku-postgresql:hobby-dev
(ruelala) $ heroku config:set DISABLE_COLLECTSTATIC=1
(ruelala) $ git push heroku master
(ruelala) $ heroku run python manage.py createsuperuser
(ruelala) $ heroku config
```