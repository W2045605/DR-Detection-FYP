Setup:
first download the trained model from the one drive link here or in my word document:https://universityofwestminster-my.sharepoint.com/:f:/g/personal/w2045605_westminster_ac_uk/IgAA6e_Nw5alT66tt86Dcsb1AewOwVnxLe1JT4aHVCtsvmg?e=p6yt3h
in the terminal paste this:git clone https://github.com/W2045605/DR-Detection-FYP.git
cd DR-Detection-FYP
python -m venv venv
venv\Scripts\activate   # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
then create an .env. file in the project root with the key:
SECRET_KEY=any-random-string-for-local-testing-only
DEBUG=True
once of all that is done run this to create a superuser to access the django admin section:python manage.py createsuperuser
then run python manage.py migrate
then python manage.py runserver to start the server 
the server will then be at http://127.0.0.1:8000/auth/login/
